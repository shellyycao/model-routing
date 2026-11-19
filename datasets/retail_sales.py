"""Project `retail_sales`: synthetic retail order lines, 2023-2024.

Three trusted, deterministic parts (no LLM involvement):
  generate_raw()       seeded synthetic raw CSV with documented imperfections
  reference_clean()    pure-Python implementation of CLEANING_REQUIREMENTS, rule by rule
  reference_analysis() pure-Python implementation of the analysis questions
"""

from __future__ import annotations

import calendar
import math
import random
import statistics
from datetime import date
from pathlib import Path

from src.contracts import AnalysisQuestion, ColumnSpec, ProjectSpec, ReportingRequirement

from .common import (
    DATE_FORMATS,
    fmt_num,
    is_missing,
    parse_date,
    parse_number,
    r6,
    read_csv_text,
    render_date,
    write_csv,
)

PROJECT_ID = "retail_sales"
SEED = 20261117
N_ORDERS = 600
N_DUPLICATES = 36
KEY_COLUMN = "order_id"

RAW_COLUMNS = ["order_id", "order_date", "customer_id", "region", "product_category",
               "quantity", "unit_price", "discount_pct"]
CLEAN_COLUMNS = ["order_id", "order_date", "customer_id", "region", "product_category",
                 "quantity", "unit_price", "discount_pct", "revenue"]

REGIONS = ("North", "South", "East", "West")
REGION_MAP = {r.lower(): r for r in REGIONS} | {r[0].lower(): r for r in REGIONS}

CATEGORY_PRICES = {  # canonical name -> (min, max) unit price
    "Electronics": (40.0, 1500.0),
    "Clothing": (8.0, 150.0),
    "Home & Garden": (10.0, 400.0),
    "Sports": (12.0, 600.0),
    "Books": (5.0, 60.0),
}
CATEGORIES = tuple(CATEGORY_PRICES)
CATEGORY_SYNONYMS = {
    "electronic": "Electronics",
    "home and garden": "Home & Garden",
    "home&garden": "Home & Garden",
    "sport": "Sports",
    "apparel": "Clothing",
    "book": "Books",
}
CATEGORY_MAP = {c.lower(): c for c in CATEGORIES} | CATEGORY_SYNONYMS

PRICE_MIN_EXCLUSIVE, PRICE_MAX = 0.0, 5000.0
QTY_MIN, QTY_MAX = 1, 50
DISCOUNT_MIN, DISCOUNT_MAX = 0.0, 100.0
HIGH_DISCOUNT = 20.0

# Tolerance used when comparing a cleaned file to the canonical one (numeric cells).
CLEAN_VALUE_ABS_TOL = 0.011
CLEAN_VALUE_REL_TOL = 1e-6

CLEANING_REQUIREMENTS = [
    "R1. Read every column of the raw CSV as text. Strip leading and trailing whitespace from every value. "
    "Treat the following values as missing (compare case-insensitively, after stripping): empty string, "
    "'NA', 'N/A', 'null', 'None', '-'.",
    "R2. Remove duplicate records BEFORE applying any other row filter: rows that share the same order_id "
    "are duplicates; keep only the first occurrence in raw-file order and discard the later ones.",
    "R3. order_date: parse each value using exactly one of these formats: YYYY-MM-DD; MM/DD/YYYY (month first); "
    "DD-Mon-YYYY with an English 3-letter month abbreviation (e.g. 05-Mar-2024); YYYY/MM/DD; "
    "'Month D, YYYY' with the full English month name (e.g. March 5, 2024). Drop rows whose order_date is "
    "missing or cannot be parsed. Write order_date as YYYY-MM-DD.",
    "R4. region: map case-insensitively to one of North, South, East, West; the single-letter abbreviations "
    "N, S, E, W map to North, South, East, West. Drop rows whose region is missing or not one of these.",
    "R5. product_category: map case-insensitively to one of Electronics, Clothing, Home & Garden, Sports, Books. "
    "Also map these variants (case-insensitive): 'Electronic' -> Electronics; 'Home and Garden' and "
    "'Home&Garden' -> Home & Garden; 'Sport' -> Sports; 'Apparel' -> Clothing; 'Book' -> Books. "
    "Drop rows whose product_category is missing or maps to none of the five categories.",
    "R6. unit_price: remove the substrings '$', 'USD' and ',' and surrounding spaces, then parse as a number. "
    "Drop rows whose unit_price is missing, not a number, <= 0, or > 5000. Keep the value as given "
    "(raw prices have at most 2 decimals).",
    "R7. quantity: parse as a number (values such as '3.0' are allowed). Drop rows whose quantity is missing, "
    "not a number, not a whole number, < 1, or > 50. Store quantity as an integer.",
    "R8. discount_pct: remove a trailing '%' and parse as a number (it is a percentage, e.g. 15 means 15%). "
    "A missing discount_pct means no discount: set it to 0. Drop rows whose discount_pct is not a number, "
    "< 0, or > 100.",
    "R9. customer_id: convert to upper case. A missing customer_id is set to the string 'UNKNOWN' "
    "(the row is kept).",
    "R10. Add column revenue = quantity * unit_price * (1 - discount_pct / 100), rounded to 2 decimals.",
    "R11. Output exactly these columns in this order: order_id, order_date, customer_id, region, "
    "product_category, quantity, unit_price, discount_pct, revenue. Sort rows by order_id ascending. "
    "Write a CSV with a header row and no index column; numbers are written without currency symbols, "
    "percent signs or thousands separators.",
]

QUESTIONS = [
    AnalysisQuestion(
        question_id="q1",
        question="Overall performance (aggregation): total revenue (sum of revenue) -> total_revenue; "
                 "number of orders (rows in the cleaned data) -> order_count; average order value = "
                 "total_revenue / order_count -> average_order_value.",
        metric_keys=["total_revenue", "order_count", "average_order_value"],
        abs_tolerance=0.011, rel_tolerance=1e-4),
    AnalysisQuestion(
        question_id="q2",
        question="Regional comparison (group comparison): total revenue per region -> revenue_north, "
                 "revenue_south, revenue_east, revenue_west.",
        metric_keys=["revenue_north", "revenue_south", "revenue_east", "revenue_west"],
        abs_tolerance=0.011, rel_tolerance=1e-4,
        ranking_labels={"revenue_north": "North", "revenue_south": "South",
                        "revenue_east": "East", "revenue_west": "West"}),
    AnalysisQuestion(
        question_id="q3",
        question="Quarterly trend in 2024 (trend): total revenue of orders dated in each calendar quarter of "
                 "2024 (Q1 = Jan-Mar, Q2 = Apr-Jun, Q3 = Jul-Sep, Q4 = Oct-Dec) -> revenue_2024_q1, "
                 "revenue_2024_q2, revenue_2024_q3, revenue_2024_q4.",
        metric_keys=["revenue_2024_q1", "revenue_2024_q2", "revenue_2024_q3", "revenue_2024_q4"],
        abs_tolerance=0.011, rel_tolerance=1e-4,
        ranking_labels={f"revenue_2024_q{i}": f"Q{i}" for i in range(1, 5)}),
    AnalysisQuestion(
        question_id="q4",
        question="Year-over-year change (percentage change): total revenue of orders dated in 2023 -> "
                 "revenue_2023; in 2024 -> revenue_2024; percentage change = (revenue_2024 - revenue_2023) "
                 "/ revenue_2023 * 100 -> revenue_yoy_change_pct, expressed as a percentage.",
        metric_keys=["revenue_2023", "revenue_2024", "revenue_yoy_change_pct"],
        abs_tolerance=0.011, rel_tolerance=1e-4,
        direction_key="revenue_yoy_change_pct"),
    AnalysisQuestion(
        question_id="q5",
        question="High-discount electronics (conditional filtering): among orders with product_category "
                 "'Electronics' and discount_pct >= 20: number of orders -> electronics_high_discount_orders; "
                 "their total revenue -> electronics_high_discount_revenue.",
        metric_keys=["electronics_high_discount_orders", "electronics_high_discount_revenue"],
        abs_tolerance=0.011, rel_tolerance=1e-4),
    AnalysisQuestion(
        question_id="q6",
        question="Order revenue distribution (statistical summary) over all orders: mean -> "
                 "order_revenue_mean; median -> order_revenue_median; sample standard deviation "
                 "(denominator n - 1) -> order_revenue_std; minimum -> order_revenue_min; maximum -> "
                 "order_revenue_max.",
        metric_keys=["order_revenue_mean", "order_revenue_median", "order_revenue_std",
                     "order_revenue_min", "order_revenue_max"],
        abs_tolerance=0.011, rel_tolerance=1e-4),
    AnalysisQuestion(
        question_id="q7",
        question="Customer concentration (derived step): number of distinct customer_id values -> "
                 "unique_customer_count; revenue of the highest-revenue customer -> top_customer_revenue; "
                 "top_customer_revenue / total revenue * 100 -> top_customer_revenue_share_pct.",
        metric_keys=["unique_customer_count", "top_customer_revenue", "top_customer_revenue_share_pct"],
        abs_tolerance=0.011, rel_tolerance=1e-4),
]

CLEANED_SCHEMA = [
    ColumnSpec(name="order_id", dtype="str"),
    ColumnSpec(name="order_date", dtype="date"),
    ColumnSpec(name="customer_id", dtype="str"),
    ColumnSpec(name="region", dtype="category", allowed_values=list(REGIONS)),
    ColumnSpec(name="product_category", dtype="category", allowed_values=list(CATEGORIES)),
    ColumnSpec(name="quantity", dtype="int", min_value=QTY_MIN, max_value=QTY_MAX),
    ColumnSpec(name="unit_price", dtype="float", min_value=0.01, max_value=PRICE_MAX),
    ColumnSpec(name="discount_pct", dtype="float", min_value=DISCOUNT_MIN, max_value=DISCOUNT_MAX),
    ColumnSpec(name="revenue", dtype="float", min_value=0.0),
]


def project_spec() -> ProjectSpec:
    return ProjectSpec(
        project_id=PROJECT_ID,
        domain="retail",
        seed=SEED,
        objective=("Clean the raw retail order export and analyse 2023-2024 sales performance: overall "
                   "revenue, regional differences, the 2024 quarterly trend, year-over-year growth, "
                   "high-discount electronics orders, customer concentration and the distribution of order revenue, then report "
                   "the verified findings to business stakeholders."),
        raw_data_file="raw.csv",
        cleaning_requirements=CLEANING_REQUIREMENTS,
        cleaned_schema=CLEANED_SCHEMA,
        analysis_questions=QUESTIONS,
        reporting=ReportingRequirement(required_finding_ids=[q.question_id for q in QUESTIONS],
                                       max_words=600, audience="business stakeholders"),
        canonical_cleaned_file="canonical/cleaned.csv",
        canonical_findings_file="canonical/findings.json",
        ground_truth_file="ground_truth.json",
        notes=("SYNTHETIC data. Known raw imperfections: duplicate order_id rows (exact copies and "
               "re-formatted copies); five date formats; missing values written as '', NA, N/A, null, "
               "None or '-'; prices as strings with '$', 'USD', thousands separators and padding; "
               "quantities as '3.0' or padded; discounts with '%'; region/category case, padding, "
               "abbreviations and spelling variants; an unknown category ('Toys'); unparseable prices "
               "('TBD'); invalid values (quantity <= 0 or > 50, negative prices, discounts < 0 or > 100); "
               "lower-case customer ids. findings.json is a flat JSON object mapping each metric_key to a "
               "number."),
    )


# --------------------------------------------------------------------------- generation

def _base_records(rng: random.Random) -> list[dict]:
    month_w = [6, 5, 6, 7, 7, 7, 8, 8, 8, 9, 11, 14]
    dates = []
    for _ in range(N_ORDERS):
        year = 2023 if rng.random() < 0.45 else 2024
        month = rng.choices(range(1, 13), weights=month_w)[0]
        day = rng.randint(1, calendar.monthrange(year, month)[1])
        dates.append(date(year, month, day))
    dates.sort()
    recs = []
    for i, d in enumerate(dates):
        cat = rng.choices(CATEGORIES, weights=[22, 30, 18, 15, 15])[0]
        lo, hi = CATEGORY_PRICES[cat]
        recs.append({
            "order_id": f"R{100001 + i}",
            "order_date": d,
            "customer_id": f"C{rng.randint(1, 250):04d}",
            "region": rng.choices(REGIONS, weights=[30, 25, 25, 20])[0],
            "category": cat,
            "quantity": rng.choices(range(1, 11), weights=[30, 20, 14, 10, 8, 6, 4, 3, 3, 2])[0],
            "unit_price": round(rng.uniform(lo, hi), 2),
            "discount_pct": float(rng.choice([0, 0, 0, 0, 5, 10, 10, 15, 20, 25, 30])),
        })
    return recs


def _inject_defects(rng: random.Random, recs: list[dict]) -> dict[str, int]:
    """Mutate semantic values in place; returns counts of injected defects."""
    log = {k: 0 for k in ("missing_date", "missing_region", "missing_price", "missing_customer",
                          "missing_discount", "unknown_category", "unparseable_price",
                          "nonpositive_or_too_large_quantity", "fractional_quantity",
                          "negative_price", "discount_out_of_range")}
    for r in recs:
        u = rng.random()
        if u < 0.015:
            r["order_date"], k = None, "missing_date"
        elif u < 0.035:
            r["region"], k = None, "missing_region"
        elif u < 0.050:
            r["unit_price"], k = None, "missing_price"
        elif u < 0.058:
            r["category"], k = "Toys", "unknown_category"
        elif u < 0.066:
            r["unit_price"], k = "TBD", "unparseable_price"
        elif u < 0.084:
            r["quantity"], k = rng.choice([0, -1, -2, 60, 500]), "nonpositive_or_too_large_quantity"
        elif u < 0.090:
            r["quantity"], k = rng.choice([1.5, 2.5]), "fractional_quantity"
        elif u < 0.100:
            r["unit_price"], k = -abs(r["unit_price"]), "negative_price"
        elif u < 0.110:
            r["discount_pct"], k = rng.choice([-5.0, 120.0, 150.0]), "discount_out_of_range"
        else:
            k = None
        if k:
            log[k] += 1
        # Non-dropping defects are independent of the above.
        if rng.random() < 0.03:
            r["customer_id"] = None
            log["missing_customer"] += 1
        if rng.random() < 0.05:
            r["discount_pct"] = None
            log["missing_discount"] += 1
    return log


def _render(rng: random.Random, r: dict) -> list[str]:
    def missing() -> str:
        return rng.choice(["", "NA", "N/A", "null", "None", "-"])

    d = r["order_date"]
    if d is None:
        date_s = missing()
    else:
        fmt = rng.choices(list(DATE_FORMATS), weights=[50, 20, 15, 10, 5])[0]
        date_s = render_date(d, fmt)

    cust = r["customer_id"]
    if cust is None:
        cust_s = missing()
    else:
        cust_s = cust.lower() if rng.random() < 0.10 else cust

    reg = r["region"]
    if reg is None:
        reg_s = missing()
    else:
        reg_s = rng.choices([reg, reg.lower(), reg.upper(), f"  {reg} ", reg[0]],
                            weights=[60, 10, 10, 10, 10])[0]

    cat = r["category"]
    variants = [cat, cat.lower(), cat.upper()] + [k.title() for k, v in CATEGORY_SYNONYMS.items() if v == cat]
    weights = [70, 10, 10] + [10] * (len(variants) - 3)
    cat_s = rng.choices(variants, weights=weights)[0]

    q = r["quantity"]
    if isinstance(q, float):
        qty_s = str(q)
    else:
        qty_s = rng.choices([str(q), f"{q}.0", f" {q} "], weights=[85, 10, 5])[0]

    p = r["unit_price"]
    if p is None:
        price_s = missing()
    elif isinstance(p, str):
        price_s = p
    else:
        style = rng.choices(["plain", "dollar", "pad", "usd"], weights=[50, 25, 15, 10])[0]
        neg = "-" if p < 0 else ""
        a = abs(p)
        if style == "plain":
            price_s = f"{neg}{a:.2f}"
        elif style == "dollar":
            price_s = f"{neg}${a:,.2f}"
        elif style == "pad":
            price_s = f" {neg}{a:.2f} "
        else:
            price_s = f"USD {neg}{a:.2f}"

    disc = r["discount_pct"]
    if disc is None:
        disc_s = missing()
    else:
        txt = f"{disc:g}"
        disc_s = txt + "%" if rng.random() < 0.20 else txt

    return [r["order_id"], date_s, cust_s, reg_s, cat_s, qty_s, price_s, disc_s]


def generate_raw(path: Path) -> dict:
    rng = random.Random(SEED)
    recs = _base_records(rng)
    injected = _inject_defects(rng, recs)
    keyed: list[tuple[float, list[str]]] = [(float(i), _render(rng, r)) for i, r in enumerate(recs)]
    dup_idx = sorted(rng.sample(range(len(recs)), N_DUPLICATES))
    n_exact = 0
    for i in dup_idx:
        if rng.random() < 0.5:
            row = list(keyed[i][1])
            n_exact += 1
        else:
            row = _render(rng, recs[i])
            row[6] = "999.99"  # later duplicate deliberately disagrees; keep-first order is observable
        keyed.append((i + rng.uniform(1.0, 50.0), row))
    keyed.sort(key=lambda t: t[0])
    write_csv(path, RAW_COLUMNS, [row for _, row in keyed])
    injected["duplicate_rows_exact"] = n_exact
    injected["duplicate_rows_changed_value"] = N_DUPLICATES - n_exact
    return {"raw_row_count": len(keyed), "base_record_count": len(recs), "injected": injected}


# --------------------------------------------------------------------------- reference cleaning

def reference_clean(raw_path: Path, out_path: Path) -> dict:
    """Apply CLEANING_REQUIREMENTS R1-R11 literally. Returns a log of what each rule did."""
    header, rows = read_csv_text(raw_path)
    assert header == RAW_COLUMNS, header
    log = {"raw_rows": len(rows)}

    # R1
    def val(row: dict, col: str) -> str | None:
        v = (row[col] or "").strip()
        return None if is_missing(v) else v

    # R2
    seen, deduped = set(), []
    for row in rows:
        oid = row["order_id"].strip()
        if oid in seen:
            continue
        seen.add(oid)
        deduped.append(row)
    log["R2_duplicates_removed"] = len(rows) - len(deduped)

    drops = {k: 0 for k in ("R3_date", "R4_region", "R5_category", "R6_unit_price",
                            "R7_quantity", "R8_discount")}
    out = []
    for row in deduped:
        d = parse_date(val(row, "order_date") or "")
        if d is None:
            drops["R3_date"] += 1
            continue
        reg = val(row, "region")
        reg = REGION_MAP.get(reg.lower()) if reg else None
        if reg is None:
            drops["R4_region"] += 1
            continue
        cat = val(row, "product_category")
        cat = CATEGORY_MAP.get(cat.lower()) if cat else None
        if cat is None:
            drops["R5_category"] += 1
            continue
        price = parse_number(val(row, "unit_price"), strip=("$", "USD", ","))
        if price is None or not (PRICE_MIN_EXCLUSIVE < price <= PRICE_MAX):
            drops["R6_unit_price"] += 1
            continue
        qty = parse_number(val(row, "quantity"))
        if qty is None or qty != math.floor(qty) or not (QTY_MIN <= qty <= QTY_MAX):
            drops["R7_quantity"] += 1
            continue
        disc_raw = val(row, "discount_pct")
        if disc_raw is None:
            disc = 0.0
        else:
            disc = parse_number(disc_raw[:-1] if disc_raw.endswith("%") else disc_raw)
            if disc is None or not (DISCOUNT_MIN <= disc <= DISCOUNT_MAX):
                drops["R8_discount"] += 1
                continue
        cust = val(row, "customer_id")
        cust = cust.upper() if cust else "UNKNOWN"
        qty_i = int(qty)
        revenue = round(qty_i * price * (1 - disc / 100), 2)
        out.append([row["order_id"].strip(), d.isoformat(), cust, reg, cat, str(qty_i),
                    fmt_num(price), fmt_num(disc), fmt_num(revenue)])
    out.sort(key=lambda r: r[0])
    write_csv(out_path, CLEAN_COLUMNS, out)
    log.update({f"dropped_{k}": v for k, v in drops.items()})
    log["cleaned_rows"] = len(out)
    return log


# --------------------------------------------------------------------------- reference analysis

def reference_analysis(cleaned_path: Path) -> dict[str, float]:
    header, rows = read_csv_text(cleaned_path)
    if missing := [c for c in CLEAN_COLUMNS if c not in header]:
        raise ValueError(f"cleaned file lacks columns {missing}")
    recs = [{
        "date": date.fromisoformat(r["order_date"]),
        "region": r["region"],
        "category": r["product_category"],
        "discount": float(r["discount_pct"]),
        "customer": r["customer_id"],
        "revenue": float(r["revenue"]),
    } for r in rows]
    rev = [r["revenue"] for r in recs]

    def total(pred) -> float:
        return math.fsum(r["revenue"] for r in recs if pred(r))

    m: dict[str, float] = {}
    m["total_revenue"] = math.fsum(rev)
    m["order_count"] = float(len(recs))
    m["average_order_value"] = m["total_revenue"] / len(recs)
    for reg in REGIONS:
        m[f"revenue_{reg.lower()}"] = total(lambda r, reg=reg: r["region"] == reg)
    for q in range(1, 5):
        m[f"revenue_2024_q{q}"] = total(
            lambda r, q=q: r["date"].year == 2024 and (r["date"].month - 1) // 3 + 1 == q)
    m["revenue_2023"] = total(lambda r: r["date"].year == 2023)
    m["revenue_2024"] = total(lambda r: r["date"].year == 2024)
    m["revenue_yoy_change_pct"] = (m["revenue_2024"] - m["revenue_2023"]) / m["revenue_2023"] * 100
    sel = [r for r in recs if r["category"] == "Electronics" and r["discount"] >= HIGH_DISCOUNT]
    m["electronics_high_discount_orders"] = float(len(sel))
    m["electronics_high_discount_revenue"] = math.fsum(r["revenue"] for r in sel)
    m["order_revenue_mean"] = statistics.fmean(rev)
    m["order_revenue_median"] = statistics.median(rev)
    m["order_revenue_std"] = statistics.stdev(rev)
    m["order_revenue_min"] = min(rev)
    m["order_revenue_max"] = max(rev)
    by_customer: dict[str, float] = {}
    for r in recs:
        by_customer[r["customer"]] = by_customer.get(r["customer"], 0.0) + r["revenue"]
    m["unique_customer_count"] = float(len(by_customer))
    m["top_customer_revenue"] = max(by_customer.values())
    m["top_customer_revenue_share_pct"] = m["top_customer_revenue"] / m["total_revenue"] * 100
    return {k: r6(v) for k, v in m.items()}
