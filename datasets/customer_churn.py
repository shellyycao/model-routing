"""Project `customer_churn`: synthetic subscription-customer snapshot (as of 2024-12-31).

Trusted, deterministic parts (no LLM): generate_raw(), reference_clean(), reference_analysis().
"""

from __future__ import annotations

import math
import random
import statistics
from datetime import date, timedelta
from pathlib import Path

from src.contracts import AnalysisQuestion, ColumnSpec, ProjectSpec, ReportingRequirement

from .common import (
    DATE_FORMATS,
    fmt_num,
    is_missing,
    missing_token,
    parse_date,
    parse_number,
    r6,
    read_csv_text,
    render_date,
    whole_number,
    write_csv,
)

PROJECT_ID = "customer_churn"
SEED = 20261118
N_CUSTOMERS = 800
N_DUPLICATES = 40
KEY_COLUMN = "customer_id"
SNAPSHOT = date(2024, 12, 31)

RAW_COLUMNS = ["customer_id", "signup_date", "plan", "contract_type", "monthly_fee", "tenure_months",
               "support_tickets", "satisfaction_score", "churned"]
CLEAN_COLUMNS = ["customer_id", "signup_date", "plan", "contract_type", "monthly_fee", "tenure_months",
                 "support_tickets", "satisfaction_score", "churned", "lifetime_value"]

PLANS = ("Basic", "Standard", "Premium")
PLAN_FEES = {"Basic": (19.99, 24.99), "Standard": (39.99, 44.99), "Premium": (79.99, 89.99)}
PLAN_SYNONYMS = {"basic plan": "Basic", "std": "Standard", "standard plan": "Standard",
                 "prem": "Premium", "premium plan": "Premium"}
PLAN_MAP = {p.lower(): p for p in PLANS} | PLAN_SYNONYMS
CONTRACTS = ("Monthly", "Annual")
CONTRACT_MAP = {"monthly": "Monthly", "month-to-month": "Monthly", "m2m": "Monthly",
                "annual": "Annual", "yearly": "Annual", "1 year": "Annual"}
CHURN_TRUE = {"yes", "y", "true", "1", "churned"}
CHURN_FALSE = {"no", "n", "false", "0", "active"}

FEE_MAX = 500.0
TENURE_MAX = 120
TICKETS_MAX = 100

CLEAN_VALUE_ABS_TOL = 0.011
CLEAN_VALUE_REL_TOL = 1e-6

CLEANING_REQUIREMENTS = [
    "R1. Read every column of the raw CSV as text. Strip leading and trailing whitespace from every value. "
    "Treat the following values as missing (compare case-insensitively, after stripping): empty string, "
    "'NA', 'N/A', 'null', 'None', '-'.",
    "R2. Remove duplicate records BEFORE applying any other row filter: rows that share the same customer_id "
    "are duplicates; keep only the first occurrence in raw-file order and discard the later ones.",
    "R3. signup_date: parse each value using exactly one of these formats: YYYY-MM-DD; MM/DD/YYYY (month first); "
    "DD-Mon-YYYY with an English 3-letter month abbreviation (e.g. 05-Mar-2024); YYYY/MM/DD; "
    "'Month D, YYYY' with the full English month name (e.g. March 5, 2024). Drop rows whose signup_date is "
    "missing or cannot be parsed. Write signup_date as YYYY-MM-DD.",
    "R4. plan: map case-insensitively to one of Basic, Standard, Premium. Also map these variants "
    "(case-insensitive): 'Basic Plan' -> Basic; 'Std' and 'Standard Plan' -> Standard; 'Prem' and "
    "'Premium Plan' -> Premium. Drop rows whose plan is missing or maps to none of the three plans.",
    "R5. contract_type: map case-insensitively: 'Monthly', 'Month-to-month', 'M2M' -> Monthly; 'Annual', "
    "'Yearly', '1 Year' -> Annual. Drop rows whose contract_type is missing or not one of these.",
    "R6. monthly_fee: remove the substrings '$', 'USD' and ',' and surrounding spaces, then parse as a number. "
    "Drop rows whose monthly_fee is missing, not a number, <= 0, or > 500.",
    "R7. tenure_months: remove a trailing word 'months' or 'month' (case-insensitive) and spaces, then parse "
    "as a number. Drop rows whose tenure_months is missing, not a number, not a whole number, < 0, or > 120. "
    "Store as an integer.",
    "R8. support_tickets: a missing value means 0. Otherwise parse as a number; drop rows whose value is not "
    "a number, not a whole number, < 0, or > 100. Store as an integer.",
    "R9. satisfaction_score: parse as a number; if it is missing, not a number, not a whole number, < 1 or > 5, "
    "set it to missing (write an empty cell) and KEEP the row. Otherwise store as an integer 1-5.",
    "R10. churned: map case-insensitively 'Yes', 'Y', 'True', '1', 'Churned' -> 1 and 'No', 'N', 'False', "
    "'0', 'Active' -> 0. Drop rows whose churned value is missing or not one of these. Store as integer 0/1.",
    "R11. Add column lifetime_value = monthly_fee * tenure_months, rounded to 2 decimals.",
    "R12. Output exactly these columns in this order: customer_id, signup_date, plan, contract_type, "
    "monthly_fee, tenure_months, support_tickets, satisfaction_score, churned, lifetime_value. Sort rows by "
    "customer_id ascending. Write a CSV with a header row and no index column; numbers are written without "
    "currency symbols or thousands separators; a missing satisfaction_score is an empty cell.",
]

_T = dict(abs_tolerance=0.011, rel_tolerance=1e-4)
QUESTIONS = [
    AnalysisQuestion(question_id="q1", metric_keys=["customer_count", "churn_rate_pct", "avg_monthly_fee"], **_T,
                     question="Overall (aggregation): number of customers (rows) -> customer_count; percentage of "
                              "customers with churned = 1 -> churn_rate_pct, expressed as a percentage; "
                              "mean monthly_fee -> avg_monthly_fee."),
    AnalysisQuestion(question_id="q2", metric_keys=["churn_rate_basic_pct", "churn_rate_standard_pct",
                                                    "churn_rate_premium_pct"], **_T,
                     question="Churn by plan (group comparison): churn rate in percent among customers of each plan "
                              "-> churn_rate_basic_pct, churn_rate_standard_pct, churn_rate_premium_pct.",
                     ranking_labels={"churn_rate_basic_pct": "Basic", "churn_rate_standard_pct": "Standard",
                                     "churn_rate_premium_pct": "Premium"}),
    AnalysisQuestion(question_id="q3", metric_keys=["churn_rate_cohort_2021_pct", "churn_rate_cohort_2022_pct",
                                                    "churn_rate_cohort_2023_pct", "churn_rate_cohort_2024_pct"], **_T,
                     question="Churn by signup cohort (trend): churn rate in percent among customers whose "
                              "signup_date falls in each calendar year -> churn_rate_cohort_2021_pct, "
                              "churn_rate_cohort_2022_pct, churn_rate_cohort_2023_pct, churn_rate_cohort_2024_pct.",
                     ranking_labels={f"churn_rate_cohort_{y}_pct": str(y) for y in range(2021, 2025)}),
    AnalysisQuestion(question_id="q4", metric_keys=["churn_rate_monthly_pct", "churn_rate_annual_pct",
                                                    "churn_monthly_vs_annual_change_pct"], **_T,
                     question="Contract effect (percentage change): churn rate in percent for Monthly contracts -> "
                              "churn_rate_monthly_pct; for Annual contracts -> churn_rate_annual_pct; relative "
                              "difference = (churn_rate_monthly_pct - churn_rate_annual_pct) / churn_rate_annual_pct "
                              "* 100 -> churn_monthly_vs_annual_change_pct.",
                     direction_key="churn_monthly_vs_annual_change_pct"),
    AnalysisQuestion(question_id="q5", metric_keys=["at_risk_customer_count", "at_risk_churn_rate_pct"], **_T,
                     question="At-risk segment (conditional filtering): customers with support_tickets >= 5 AND a "
                              "non-missing satisfaction_score <= 2: their number -> at_risk_customer_count; their "
                              "churn rate in percent -> at_risk_churn_rate_pct."),
    AnalysisQuestion(question_id="q6", metric_keys=["tenure_mean", "tenure_median", "tenure_std",
                                                    "satisfaction_mean", "satisfaction_missing_count"], **_T,
                     question="Tenure and satisfaction summary (statistical summary): mean, median and sample "
                              "standard deviation (denominator n - 1) of tenure_months over all customers -> "
                              "tenure_mean, tenure_median, tenure_std; mean satisfaction_score over customers with a "
                              "non-missing score -> satisfaction_mean; number of customers with a missing "
                              "satisfaction_score -> satisfaction_missing_count."),
    AnalysisQuestion(question_id="q7", metric_keys=["ltv_basic", "ltv_standard", "ltv_premium",
                                                    "premium_vs_basic_ltv_change_pct"], **_T,
                     question="Lifetime value by plan (derived step): mean lifetime_value for each plan -> "
                              "ltv_basic, ltv_standard, ltv_premium; (ltv_premium - ltv_basic) / ltv_basic * 100 "
                              "-> premium_vs_basic_ltv_change_pct.",
                     direction_key="premium_vs_basic_ltv_change_pct",
                     ranking_labels={"ltv_basic": "Basic", "ltv_standard": "Standard",
                                     "ltv_premium": "Premium"}),
]

CLEANED_SCHEMA = [
    ColumnSpec(name="customer_id", dtype="str"),
    ColumnSpec(name="signup_date", dtype="date"),
    ColumnSpec(name="plan", dtype="category", allowed_values=list(PLANS)),
    ColumnSpec(name="contract_type", dtype="category", allowed_values=list(CONTRACTS)),
    ColumnSpec(name="monthly_fee", dtype="float", min_value=0.01, max_value=FEE_MAX),
    ColumnSpec(name="tenure_months", dtype="int", min_value=0, max_value=TENURE_MAX),
    ColumnSpec(name="support_tickets", dtype="int", min_value=0, max_value=TICKETS_MAX),
    ColumnSpec(name="satisfaction_score", dtype="int", nullable=True, min_value=1, max_value=5),
    ColumnSpec(name="churned", dtype="int", min_value=0, max_value=1),
    ColumnSpec(name="lifetime_value", dtype="float", min_value=0.0),
]


def project_spec() -> ProjectSpec:
    return ProjectSpec(
        project_id=PROJECT_ID, domain="subscription customers", seed=SEED,
        objective=("Clean the raw customer snapshot and analyse churn: the overall churn rate, differences "
                   "between plans, signup cohorts and contract types, an at-risk segment with many support "
                   "tickets and low satisfaction, lifetime value by plan, and the distribution of tenure and satisfaction, then report "
                   "the verified findings to business stakeholders."),
        raw_data_file="raw.csv",
        cleaning_requirements=CLEANING_REQUIREMENTS,
        cleaned_schema=CLEANED_SCHEMA,
        analysis_questions=QUESTIONS,
        reporting=ReportingRequirement(required_finding_ids=[q.question_id for q in QUESTIONS], max_words=600),
        canonical_cleaned_file="canonical/cleaned.csv",
        canonical_findings_file="canonical/findings.json",
        ground_truth_file="ground_truth.json",
        notes=("SYNTHETIC data. Known raw imperfections: duplicate customer_id rows (exact and re-formatted); "
               "five date formats; missing tokens ('', NA, N/A, null, None, '-'); plan and contract spelling/case "
               "variants and an unknown plan ('Enterprise'); fees with '$', 'USD', padding, unparseable 'TBD', "
               "negative or > 500 values; tenure written as '12 months' or '12.0', negative, fractional or > 120; "
               "missing/negative support_tickets; satisfaction scores out of 1-5 (kept as missing); churned "
               "encoded as Yes/No/Y/N/True/False/1/0/Churned/Active or unrecognised ('?'). findings.json is a flat "
               "JSON object mapping each metric_key to a number."),
    )


# --------------------------------------------------------------------------- generation

def _months_between(a: date, b: date) -> int:
    return (b.year - a.year) * 12 + (b.month - a.month)


def _base_records(rng: random.Random) -> list[dict]:
    start, span = date(2021, 1, 1), (date(2024, 6, 30) - date(2021, 1, 1)).days
    recs = []
    for _ in range(N_CUSTOMERS):
        signup = start + timedelta(days=rng.randint(0, span))
        plan = rng.choices(PLANS, weights=[45, 35, 20])[0]
        contract = "Monthly" if rng.random() < 0.6 else "Annual"
        tickets = rng.choices(range(0, 13), weights=[20, 18, 14, 11, 9, 7, 6, 5, 3, 3, 2, 1, 1])[0]
        sat = max(1, min(5, round(4.2 - 0.25 * tickets + rng.gauss(0, 0.8))))
        logit = -1.6 + 1.1 * (contract == "Monthly") + 0.18 * tickets - 0.45 * (sat - 3) - 0.3 * (plan == "Premium")
        churned = rng.random() < 1 / (1 + math.exp(-logit))
        max_tenure = max(1, _months_between(signup, SNAPSHOT))
        tenure = rng.randint(1, max_tenure) if churned else max_tenure
        recs.append({"signup": signup, "plan": plan, "contract": contract,
                     "fee": rng.choice(PLAN_FEES[plan]), "tenure": tenure, "tickets": tickets,
                     "sat": sat, "churned": churned})
    recs.sort(key=lambda r: r["signup"])
    for i, r in enumerate(recs):
        r["customer_id"] = f"CUST-{i + 1:04d}"
    return recs


def _inject_defects(rng: random.Random, recs: list[dict]) -> dict[str, int]:
    log: dict[str, int] = {}

    def hit(k: str) -> None:
        log[k] = log.get(k, 0) + 1

    for r in recs:
        u = rng.random()
        if u < 0.015:
            r["signup"] = None; hit("missing_signup_date")
        elif u < 0.025:
            r["plan"] = "Enterprise"; hit("unknown_plan")
        elif u < 0.035:
            r["contract"] = None; hit("missing_contract")
        elif u < 0.045:
            r["fee"] = rng.choice(["TBD", -r["fee"], 9999.0]); hit("invalid_fee")
        elif u < 0.055:
            r["fee"] = None; hit("missing_fee")
        elif u < 0.067:
            r["tenure"] = rng.choice([-3, 150, 6.5]); hit("invalid_tenure")
        elif u < 0.073:
            r["tickets"] = -1; hit("negative_tickets")
        elif u < 0.083:
            r["churned"] = rng.choice([None, "?"]); hit("missing_or_unrecognised_churned")
        if rng.random() < 0.04:
            r["tickets_missing"] = True; hit("missing_tickets")
        v = rng.random()
        if v < 0.04:
            r["sat"] = None; hit("missing_satisfaction")
        elif v < 0.06:
            r["sat"] = rng.choice([0, 6, 10]); hit("satisfaction_out_of_range")
    return log


def _render(rng: random.Random, r: dict) -> list[str]:
    def var(canon: str, extra: list[str]) -> str:
        opts = [canon, canon.lower(), canon.upper(), f" {canon} "] + extra
        return rng.choices(opts, weights=[60, 8, 8, 8] + [16 / max(1, len(extra))] * len(extra))[0]

    signup = missing_token(rng) if r["signup"] is None else render_date(
        r["signup"], rng.choices(list(DATE_FORMATS), weights=[50, 20, 15, 10, 5])[0])
    plan = r["plan"] if r["plan"] == "Enterprise" else var(
        r["plan"], [k.title() for k, v in PLAN_SYNONYMS.items() if v == r["plan"]])
    if r["contract"] is None:
        contract = missing_token(rng)
    else:
        contract = var(r["contract"], ["Month-to-month", "M2M"] if r["contract"] == "Monthly" else ["Yearly", "1 Year"])
    fee = r["fee"]
    if fee is None:
        fee_s = missing_token(rng)
    elif isinstance(fee, str):
        fee_s = fee
    else:
        sign = "-" if fee < 0 else ""
        fee_s = rng.choices([f"{fee:.2f}", f"{sign}${abs(fee):,.2f}", f"USD {fee:.2f}", f" {fee:.2f} "],
                            weights=[50, 30, 10, 10])[0]
    t = r["tenure"]
    tenure_s = str(t) if isinstance(t, float) else rng.choices(
        [str(t), f"{t}.0", f"{t} months", f"{t} Months"], weights=[70, 10, 15, 5])[0]
    if t == 1 and tenure_s.endswith("onths"):
        tenure_s = "1 month"
    tickets_s = missing_token(rng) if r.get("tickets_missing") else str(r["tickets"])
    sat = r["sat"]
    sat_s = missing_token(rng) if sat is None else rng.choices([str(sat), f"{sat}.0"], weights=[85, 15])[0]
    c = r["churned"]
    if c is None:
        churn_s = missing_token(rng)
    elif c == "?":
        churn_s = "?"
    elif c:
        churn_s = rng.choice(["Yes", "yes", "Y", "TRUE", "1", "Churned"])
    else:
        churn_s = rng.choice(["No", "no", "N", "False", "0", "Active"])
    cid = r["customer_id"] if rng.random() > 0.05 else f" {r['customer_id']} "
    return [cid, signup, plan, contract, fee_s, tenure_s, tickets_s, sat_s, churn_s]


def generate_raw(path: Path) -> dict:
    rng = random.Random(SEED)
    recs = _base_records(rng)
    injected = _inject_defects(rng, recs)
    keyed = [(float(i), _render(rng, r)) for i, r in enumerate(recs)]
    n_exact = 0
    for i in sorted(rng.sample(range(len(recs)), N_DUPLICATES)):
        if rng.random() < 0.5:
            row = list(keyed[i][1]); n_exact += 1
        else:
            row = _render(rng, recs[i])
            row[4] = "499.99"  # later duplicate differs so keep-first order affects the result
        keyed.append((i + rng.uniform(1.0, 60.0), row))
    keyed.sort(key=lambda t: t[0])
    write_csv(path, RAW_COLUMNS, [row for _, row in keyed])
    injected["duplicate_rows_exact"] = n_exact
    injected["duplicate_rows_changed_value"] = N_DUPLICATES - n_exact
    return {"raw_row_count": len(keyed), "base_record_count": len(recs), "injected": dict(sorted(injected.items()))}


# --------------------------------------------------------------------------- reference cleaning

def reference_clean(raw_path: Path, out_path: Path) -> dict:
    header, rows = read_csv_text(raw_path)
    assert header == RAW_COLUMNS, header
    log = {"raw_rows": len(rows)}

    def val(row: dict, col: str) -> str | None:
        v = (row[col] or "").strip()
        return None if is_missing(v) else v

    seen, deduped = set(), []
    for row in rows:
        k = row["customer_id"].strip()
        if k not in seen:
            seen.add(k); deduped.append(row)
    log["R2_duplicates_removed"] = len(rows) - len(deduped)

    drops = {k: 0 for k in ("R3_signup_date", "R4_plan", "R5_contract_type", "R6_monthly_fee",
                            "R7_tenure_months", "R8_support_tickets", "R10_churned")}
    sat_blanked = 0
    out = []
    for row in deduped:
        d = parse_date(val(row, "signup_date") or "")
        if d is None:
            drops["R3_signup_date"] += 1; continue
        plan = val(row, "plan")
        plan = PLAN_MAP.get(plan.lower()) if plan else None
        if plan is None:
            drops["R4_plan"] += 1; continue
        contract = val(row, "contract_type")
        contract = CONTRACT_MAP.get(contract.lower()) if contract else None
        if contract is None:
            drops["R5_contract_type"] += 1; continue
        fee = parse_number(val(row, "monthly_fee"), strip=("$", "USD", ","))
        if fee is None or not (0 < fee <= FEE_MAX):
            drops["R6_monthly_fee"] += 1; continue
        t = val(row, "tenure_months")
        if t is not None:
            low = t.lower()
            for suffix in ("months", "month"):
                if low.endswith(suffix):
                    t = t[: -len(suffix)].strip()
                    break
        tenure = whole_number(parse_number(t), 0, TENURE_MAX)
        if tenure is None:
            drops["R7_tenure_months"] += 1; continue
        tk = val(row, "support_tickets")
        tickets = 0 if tk is None else whole_number(parse_number(tk), 0, TICKETS_MAX)
        if tickets is None:
            drops["R8_support_tickets"] += 1; continue
        sat = whole_number(parse_number(val(row, "satisfaction_score")), 1, 5)
        ch = val(row, "churned")
        ch = ch.lower() if ch else None
        if ch in CHURN_TRUE:
            churned = 1
        elif ch in CHURN_FALSE:
            churned = 0
        else:
            drops["R10_churned"] += 1; continue
        sat_blanked += sat is None
        out.append([row["customer_id"].strip(), d.isoformat(), plan, contract, fmt_num(fee), str(tenure),
                    str(tickets), "" if sat is None else str(sat), str(churned), fmt_num(round(fee * tenure, 2))])
    out.sort(key=lambda r: r[0])
    write_csv(out_path, CLEAN_COLUMNS, out)
    log.update({f"dropped_{k}": v for k, v in drops.items()})
    log["R9_satisfaction_set_missing"] = sat_blanked
    log["cleaned_rows"] = len(out)
    return log


# --------------------------------------------------------------------------- reference analysis

def reference_analysis(cleaned_path: Path) -> dict[str, float]:
    header, rows = read_csv_text(cleaned_path)
    if missing := [c for c in CLEAN_COLUMNS if c not in header]:
        raise ValueError(f"cleaned file lacks columns {missing}")
    recs = [{"year": date.fromisoformat(r["signup_date"]).year, "plan": r["plan"], "contract": r["contract_type"],
             "fee": float(r["monthly_fee"]), "tenure": int(float(r["tenure_months"])),
             "tickets": int(float(r["support_tickets"])),
             "sat": None if r["satisfaction_score"].strip() == "" else int(float(r["satisfaction_score"])),
             "churned": int(float(r["churned"])), "ltv": float(r["lifetime_value"])} for r in rows]

    def rate(sel: list[dict]) -> float:
        return 100.0 * sum(r["churned"] for r in sel) / len(sel)

    m: dict[str, float] = {"customer_count": float(len(recs)), "churn_rate_pct": rate(recs),
                           "avg_monthly_fee": statistics.fmean(r["fee"] for r in recs)}
    for p in PLANS:
        m[f"churn_rate_{p.lower()}_pct"] = rate([r for r in recs if r["plan"] == p])
    for y in (2021, 2022, 2023, 2024):
        m[f"churn_rate_cohort_{y}_pct"] = rate([r for r in recs if r["year"] == y])
    m["churn_rate_monthly_pct"] = rate([r for r in recs if r["contract"] == "Monthly"])
    m["churn_rate_annual_pct"] = rate([r for r in recs if r["contract"] == "Annual"])
    m["churn_monthly_vs_annual_change_pct"] = ((m["churn_rate_monthly_pct"] - m["churn_rate_annual_pct"])
                                               / m["churn_rate_annual_pct"] * 100)
    risk = [r for r in recs if r["tickets"] >= 5 and r["sat"] is not None and r["sat"] <= 2]
    m["at_risk_customer_count"] = float(len(risk))
    m["at_risk_churn_rate_pct"] = rate(risk)
    ten = [r["tenure"] for r in recs]
    m["tenure_mean"] = statistics.fmean(ten)
    m["tenure_median"] = float(statistics.median(ten))
    m["tenure_std"] = statistics.stdev(ten)
    sats = [r["sat"] for r in recs if r["sat"] is not None]
    m["satisfaction_mean"] = statistics.fmean(sats)
    m["satisfaction_missing_count"] = float(len(recs) - len(sats))
    for p in PLANS:
        m[f"ltv_{p.lower()}"] = statistics.fmean(r["ltv"] for r in recs if r["plan"] == p)
    m["premium_vs_basic_ltv_change_pct"] = (m["ltv_premium"] - m["ltv_basic"]) / m["ltv_basic"] * 100
    return {k: r6(v) for k, v in m.items()}
