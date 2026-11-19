"""Project `energy_consumption`: synthetic daily smart-meter readings for 12 buildings in 2024.

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
    write_csv,
)

PROJECT_ID = "energy_consumption"
SEED = 20261119
N_READINGS = 1500
N_DUPLICATES = 60
KEY_COLUMN = "reading_id"

RAW_COLUMNS = ["reading_id", "reading_date", "meter_id", "building_type", "tariff", "energy", "temperature"]
CLEAN_COLUMNS = ["reading_id", "reading_date", "meter_id", "building_type", "tariff", "energy_kwh",
                 "temperature_c"]

TYPES = ("Residential", "Commercial", "Industrial")
TYPE_SYNONYMS = {"res": "Residential", "resi": "Residential", "comm": "Commercial", "ind": "Industrial"}
TYPE_MAP = {t.lower(): t for t in TYPES} | TYPE_SYNONYMS
TARIFF_MAP = {"peak": "peak", "off-peak": "off-peak", "offpeak": "off-peak", "off peak": "off-peak"}
METERS = {f"M{i:02d}": TYPES[(i - 1) // 4] for i in range(1, 13)}
BASE_KWH = {"Residential": 25.0, "Commercial": 300.0, "Industrial": 1500.0}
ENERGY_MAX = 100000.0
TEMP_MIN, TEMP_MAX = -40.0, 50.0
HOT = 25.0

CLEAN_VALUE_ABS_TOL = 0.01
CLEAN_VALUE_REL_TOL = 1e-6

CLEANING_REQUIREMENTS = [
    "R1. Read every column of the raw CSV as text. Strip leading and trailing whitespace from every value. "
    "Treat the following values as missing (compare case-insensitively, after stripping): empty string, "
    "'NA', 'N/A', 'null', 'None', '-'.",
    "R2. Remove duplicate records BEFORE applying any other row filter: rows that share the same reading_id "
    "are duplicates; keep only the first occurrence in raw-file order and discard the later ones.",
    "R3. reading_date: parse each value using exactly one of these formats: YYYY-MM-DD; MM/DD/YYYY (month first); "
    "DD-Mon-YYYY with an English 3-letter month abbreviation (e.g. 05-Mar-2024); YYYY/MM/DD; "
    "'Month D, YYYY' with the full English month name (e.g. March 5, 2024). Drop rows whose reading_date is "
    "missing or cannot be parsed. Write reading_date as YYYY-MM-DD.",
    "R4. meter_id: convert to upper case (e.g. 'm05' -> 'M05'). Drop rows whose meter_id is missing.",
    "R5. building_type: map case-insensitively to one of Residential, Commercial, Industrial. Also map these "
    "variants (case-insensitive): 'Res' and 'Resi' -> Residential; 'Comm' -> Commercial; 'Ind' -> Industrial. "
    "Drop rows whose building_type is missing or maps to none of the three types.",
    "R6. tariff: map case-insensitively 'peak' -> peak and 'off-peak', 'offpeak', 'off peak' -> off-peak. "
    "Drop rows whose tariff is missing or not one of these.",
    "R7. energy -> energy_kwh: remove ',' characters. If the value ends with 'MWh' (case-insensitive, optional "
    "space before the unit) remove the unit and multiply the number by 1000; if it ends with 'kWh' "
    "(case-insensitive) remove the unit; a value without a unit is already in kWh. Drop rows whose energy is "
    "missing, not a number, < 0, or > 100000 kWh (after conversion). Round energy_kwh to 2 decimals.",
    "R8. temperature -> temperature_c: remove a trailing degree sign and unit. A value ending with 'F' "
    "(case-insensitive, optionally written '°F') is Fahrenheit: convert with (F - 32) * 5 / 9. A value ending "
    "with 'C' or '°C', or without a unit, is already Celsius. Round to 1 decimal. If the temperature is missing, "
    "not a number, or outside -40 to 50 °C after conversion, set temperature_c to missing (empty cell) and KEEP "
    "the row.",
    "R9. Output exactly these columns in this order: reading_id, reading_date, meter_id, building_type, tariff, "
    "energy_kwh, temperature_c. Sort rows by reading_id ascending. Write a CSV with a header row and no index "
    "column; numbers are written without units or thousands separators; a missing temperature_c is an empty "
    "cell.",
]

QUESTIONS = [
    AnalysisQuestion(question_id="q1", metric_keys=["total_kwh", "reading_count", "mean_kwh_per_reading"],
                     abs_tolerance=0.01, rel_tolerance=1e-4,
                     question="Overall (aggregation): sum of energy_kwh -> total_kwh; number of readings (rows) -> "
                              "reading_count; total_kwh / reading_count -> mean_kwh_per_reading."),
    AnalysisQuestion(question_id="q2", metric_keys=["kwh_residential", "kwh_commercial", "kwh_industrial"],
                     abs_tolerance=0.011, rel_tolerance=1e-4,
                     question="Building types (group comparison): total energy_kwh per building_type -> "
                              "kwh_residential, kwh_commercial, kwh_industrial.",
                     ranking_labels={"kwh_residential": "Residential", "kwh_commercial": "Commercial",
                                     "kwh_industrial": "Industrial"}),
    AnalysisQuestion(question_id="q3", metric_keys=["kwh_q1", "kwh_q2", "kwh_q3", "kwh_q4"],
                     abs_tolerance=0.011, rel_tolerance=1e-4,
                     question="Quarterly trend (trend): total energy_kwh of readings dated in each calendar quarter "
                              "of 2024 (Q1 = Jan-Mar, Q2 = Apr-Jun, Q3 = Jul-Sep, Q4 = Oct-Dec) -> kwh_q1, kwh_q2, "
                              "kwh_q3, kwh_q4.",
                     ranking_labels={f"kwh_q{i}": f"Q{i}" for i in range(1, 5)}),
    AnalysisQuestion(question_id="q4", metric_keys=["kwh_h1", "kwh_h2", "kwh_h2_vs_h1_change_pct"],
                     abs_tolerance=0.011, rel_tolerance=1e-4,
                     question="Half-year change (percentage change): total energy_kwh for January-June -> kwh_h1; "
                              "July-December -> kwh_h2; (kwh_h2 - kwh_h1) / kwh_h1 * 100 -> kwh_h2_vs_h1_change_pct "
                              "(in percent).",
                     direction_key="kwh_h2_vs_h1_change_pct"),
    AnalysisQuestion(question_id="q5", metric_keys=["hot_commercial_reading_count", "hot_commercial_mean_kwh"],
                     abs_tolerance=0.01, rel_tolerance=1e-4,
                     question="Hot-day commercial load (conditional filtering): readings with building_type "
                              "Commercial and a non-missing temperature_c >= 25: their number -> "
                              "hot_commercial_reading_count; their mean energy_kwh -> hot_commercial_mean_kwh."),
    AnalysisQuestion(question_id="q6", metric_keys=["kwh_median", "kwh_std", "temperature_mean",
                                                    "temperature_missing_count", "commercial_temp_kwh_corr"],
                     abs_tolerance=1e-4, rel_tolerance=1e-4,
                     question="Distribution summary (statistical summary): median and sample standard deviation "
                              "(denominator n - 1) of energy_kwh over all readings -> kwh_median, kwh_std; mean "
                              "temperature_c over readings with a non-missing temperature -> temperature_mean; "
                              "number of readings with missing temperature_c -> temperature_missing_count; Pearson "
                              "correlation between temperature_c and energy_kwh over Commercial readings with a "
                              "non-missing temperature -> commercial_temp_kwh_corr."),
    AnalysisQuestion(question_id="q7", metric_keys=["kwh_peak", "kwh_off_peak", "peak_kwh_share_pct",
                                                    "unique_meter_count", "highest_use_meter_kwh"],
                     abs_tolerance=0.011, rel_tolerance=1e-4,
                     question="Tariff and meter usage (derived step): total energy_kwh for peak and off-peak "
                              "tariffs -> kwh_peak, kwh_off_peak; kwh_peak / total_kwh * 100 -> "
                              "peak_kwh_share_pct; number of distinct meter_id values -> unique_meter_count; "
                              "largest total energy_kwh for any single meter_id -> highest_use_meter_kwh.",
                     ranking_labels={"kwh_peak": "peak", "kwh_off_peak": "off-peak"}),
]

CLEANED_SCHEMA = [
    ColumnSpec(name="reading_id", dtype="str"),
    ColumnSpec(name="reading_date", dtype="date"),
    ColumnSpec(name="meter_id", dtype="str"),
    ColumnSpec(name="building_type", dtype="category", allowed_values=list(TYPES)),
    ColumnSpec(name="tariff", dtype="category", allowed_values=["peak", "off-peak"]),
    ColumnSpec(name="energy_kwh", dtype="float", min_value=0.0, max_value=ENERGY_MAX),
    ColumnSpec(name="temperature_c", dtype="float", nullable=True, min_value=TEMP_MIN, max_value=TEMP_MAX),
]


def project_spec() -> ProjectSpec:
    return ProjectSpec(
        project_id=PROJECT_ID, domain="energy", seed=SEED,
        objective=("Clean the raw 2024 smart-meter export and analyse electricity consumption: total and "
                   "per-building-type usage, the quarterly trend, the change between the first and second half "
                   "of the year, tariff and meter usage, commercial load on hot days and the distribution of consumption and temperature, "
                   "then report the verified findings to business stakeholders."),
        raw_data_file="raw.csv",
        cleaning_requirements=CLEANING_REQUIREMENTS,
        cleaned_schema=CLEANED_SCHEMA,
        analysis_questions=QUESTIONS,
        reporting=ReportingRequirement(required_finding_ids=[q.question_id for q in QUESTIONS], max_words=600),
        canonical_cleaned_file="canonical/cleaned.csv",
        canonical_findings_file="canonical/findings.json",
        ground_truth_file="ground_truth.json",
        notes=("SYNTHETIC data. Known raw imperfections: duplicate reading_id rows (exact and re-formatted); five "
               "date formats; missing tokens ('', NA, N/A, null, None, '-'); lower-case/padded meter ids; "
               "building-type and tariff spelling/case variants and an unknown type ('Agricultural'); energy with "
               "'kWh'/'MWh' units (mixed scales), thousands separators, unparseable 'ERR' and negative values; "
               "temperatures in Celsius and Fahrenheit with/without '°', and sensor errors (999, -99) kept as "
               "missing. findings.json is a flat JSON object mapping each metric_key to a number."),
    )


# --------------------------------------------------------------------------- generation

def _base_records(rng: random.Random) -> list[dict]:
    days = [date(2024, 1, 1) + timedelta(days=i) for i in range(366)]
    pairs = rng.sample([(d, m) for d in days for m in METERS], N_READINGS)
    pairs.sort()
    recs = []
    for i, (d, meter) in enumerate(pairs):
        btype = METERS[meter]
        doy = d.timetuple().tm_yday
        temp = round(12.0 - 11.0 * math.cos(2 * math.pi * (doy - 15) / 366) + rng.gauss(0, 3.0), 1)
        growth = 1.0 + 0.10 * (doy / 366)
        kwh = BASE_KWH[btype] * growth * (1 + 0.035 * abs(temp - 18.0)) * rng.uniform(0.8, 1.2)
        recs.append({"reading_id": f"E{i + 1:06d}", "date": d, "meter": meter, "type": btype,
                     "tariff": "peak" if rng.random() < 0.5 else "off-peak",
                     "kwh": round(kwh, 2), "temp": temp})
    return recs


def _inject_defects(rng: random.Random, recs: list[dict]) -> dict[str, int]:
    log: dict[str, int] = {}

    def hit(k: str) -> None:
        log[k] = log.get(k, 0) + 1

    for r in recs:
        u = rng.random()
        if u < 0.012:
            r["date"] = None; hit("missing_date")
        elif u < 0.020:
            r["meter"] = None; hit("missing_meter")
        elif u < 0.026:
            r["type"] = "Agricultural"; hit("unknown_building_type")
        elif u < 0.034:
            r["tariff"] = None; hit("missing_tariff")
        elif u < 0.044:
            r["kwh"] = None; hit("missing_energy")
        elif u < 0.050:
            r["kwh"] = "ERR"; hit("unparseable_energy")
        elif u < 0.056:
            r["kwh"] = -r["kwh"]; hit("negative_energy")
        v = rng.random()
        if v < 0.04:
            r["temp"] = None; hit("missing_temperature")
        elif v < 0.055:
            r["temp"] = rng.choice([999.0, -99.0]); hit("temperature_sensor_error")
    return log


def _render(rng: random.Random, r: dict) -> list[str]:
    date_s = missing_token(rng) if r["date"] is None else render_date(
        r["date"], rng.choices(list(DATE_FORMATS), weights=[50, 20, 15, 10, 5])[0])
    meter_s = missing_token(rng) if r["meter"] is None else rng.choices(
        [r["meter"], r["meter"].lower(), f" {r['meter']}"], weights=[80, 15, 5])[0]
    t = r["type"]
    if t == "Agricultural":
        type_s = t
    else:
        syn = [k.title() for k, v in TYPE_SYNONYMS.items() if v == t]
        type_s = rng.choices([t, t.lower(), t.upper(), f"{t} "] + syn, weights=[60, 10, 10, 5] + [15 / len(syn)] * len(syn))[0]
    if r["tariff"] is None:
        tariff_s = missing_token(rng)
    elif r["tariff"] == "peak":
        tariff_s = rng.choice(["peak", "Peak", "PEAK"])
    else:
        tariff_s = rng.choice(["off-peak", "Off-Peak", "offpeak", "Off peak", "OFF-PEAK"])
    k = r["kwh"]
    if k is None:
        energy_s = missing_token(rng)
    elif isinstance(k, str):
        energy_s = k
    else:
        style = rng.choices(["plain", "kwh", "comma", "mwh", "kwh_nospace"], weights=[45, 25, 10, 10, 10])[0]
        if style == "mwh" and abs(k) >= 100:
            energy_s = f"{k / 1000:.5f} MWh"
        elif style == "comma":
            energy_s = f"{k:,.2f}"
        elif style == "kwh":
            energy_s = f"{k:.2f} kWh"
        elif style == "kwh_nospace":
            energy_s = f"{k:.2f}kwh"
        else:
            energy_s = f"{k:.2f}"
    c = r["temp"]
    if c is None:
        temp_s = missing_token(rng)
    else:
        style = rng.choices(["plain", "C", "degC", "F", "degF"], weights=[50, 15, 10, 15, 10])[0]
        f = c * 9 / 5 + 32
        temp_s = {"plain": f"{c:.1f}", "C": f"{c:.1f}C", "degC": f"{c:.1f}°C",
                  "F": f"{f:.2f}F", "degF": f"{f:.2f} °F"}[style]
    rid = r["reading_id"]
    return [rid, date_s, meter_s, type_s, tariff_s, energy_s, temp_s]


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
            row[5] = "99999 kWh"  # later duplicate differs so raw-file order matters
        keyed.append((i + rng.uniform(1.0, 80.0), row))
    keyed.sort(key=lambda t: t[0])
    write_csv(path, RAW_COLUMNS, [row for _, row in keyed])
    injected["duplicate_rows_exact"] = n_exact
    injected["duplicate_rows_changed_value"] = N_DUPLICATES - n_exact
    return {"raw_row_count": len(keyed), "base_record_count": len(recs), "injected": dict(sorted(injected.items()))}


# --------------------------------------------------------------------------- reference cleaning

def parse_energy_kwh(text: str | None) -> float | None:
    if text is None:
        return None
    s = text.replace(",", "").strip()
    factor = 1.0
    if s.lower().endswith("mwh"):
        s, factor = s[:-3], 1000.0
    elif s.lower().endswith("kwh"):
        s = s[:-3]
    x = parse_number(s)
    return None if x is None else x * factor


def parse_temperature_c(text: str | None) -> float | None:
    if text is None:
        return None
    s = text.strip()
    fahrenheit = False
    if s[-1:].lower() == "f":
        s, fahrenheit = s[:-1], True
    elif s[-1:].lower() == "c":
        s = s[:-1]
    s = s.strip().removesuffix("°").strip()
    x = parse_number(s)
    if x is None:
        return None
    c = round((x - 32) * 5 / 9 if fahrenheit else x, 1)
    return c if TEMP_MIN <= c <= TEMP_MAX else None


def reference_clean(raw_path: Path, out_path: Path) -> dict:
    header, rows = read_csv_text(raw_path)
    assert header == RAW_COLUMNS, header
    log = {"raw_rows": len(rows)}

    def val(row: dict, col: str) -> str | None:
        v = (row[col] or "").strip()
        return None if is_missing(v) else v

    seen, deduped = set(), []
    for row in rows:
        k = row["reading_id"].strip()
        if k not in seen:
            seen.add(k); deduped.append(row)
    log["R2_duplicates_removed"] = len(rows) - len(deduped)

    drops = {k: 0 for k in ("R3_reading_date", "R4_meter_id", "R5_building_type", "R6_tariff", "R7_energy")}
    temp_blanked = 0
    out = []
    for row in deduped:
        d = parse_date(val(row, "reading_date") or "")
        if d is None:
            drops["R3_reading_date"] += 1; continue
        meter = val(row, "meter_id")
        if meter is None:
            drops["R4_meter_id"] += 1; continue
        btype = val(row, "building_type")
        btype = TYPE_MAP.get(btype.lower()) if btype else None
        if btype is None:
            drops["R5_building_type"] += 1; continue
        tariff = val(row, "tariff")
        tariff = TARIFF_MAP.get(tariff.lower()) if tariff else None
        if tariff is None:
            drops["R6_tariff"] += 1; continue
        kwh = parse_energy_kwh(val(row, "energy"))
        if kwh is None or not (0 <= kwh <= ENERGY_MAX):
            drops["R7_energy"] += 1; continue
        temp = parse_temperature_c(val(row, "temperature"))
        if temp is None:
            temp_blanked += 1
        out.append([row["reading_id"].strip(), d.isoformat(), meter.upper(), btype, tariff,
                    fmt_num(round(kwh, 2)), "" if temp is None else fmt_num(temp, 1)])
    out.sort(key=lambda r: r[0])
    write_csv(out_path, CLEAN_COLUMNS, out)
    log.update({f"dropped_{k}": v for k, v in drops.items()})
    log["R8_temperature_set_missing"] = temp_blanked
    log["cleaned_rows"] = len(out)
    return log


# --------------------------------------------------------------------------- reference analysis

def reference_analysis(cleaned_path: Path) -> dict[str, float]:
    header, rows = read_csv_text(cleaned_path)
    if missing := [c for c in CLEAN_COLUMNS if c not in header]:
        raise ValueError(f"cleaned file lacks columns {missing}")
    recs = [{"date": date.fromisoformat(r["reading_date"]), "type": r["building_type"],
             "meter": r["meter_id"], "tariff": r["tariff"],
             "kwh": float(r["energy_kwh"]),
             "temp": None if r["temperature_c"].strip() == "" else float(r["temperature_c"])} for r in rows]
    kwh = [r["kwh"] for r in recs]

    def total(pred) -> float:
        return math.fsum(r["kwh"] for r in recs if pred(r))

    m: dict[str, float] = {"total_kwh": math.fsum(kwh), "reading_count": float(len(recs))}
    m["mean_kwh_per_reading"] = m["total_kwh"] / len(recs)
    for t in TYPES:
        m[f"kwh_{t.lower()}"] = total(lambda r, t=t: r["type"] == t)
    for q in range(1, 5):
        m[f"kwh_q{q}"] = total(lambda r, q=q: r["date"].year == 2024 and (r["date"].month - 1) // 3 + 1 == q)
    m["kwh_h1"] = total(lambda r: r["date"].month <= 6)
    m["kwh_h2"] = total(lambda r: r["date"].month >= 7)
    m["kwh_h2_vs_h1_change_pct"] = (m["kwh_h2"] - m["kwh_h1"]) / m["kwh_h1"] * 100
    hot = [r["kwh"] for r in recs if r["type"] == "Commercial" and r["temp"] is not None and r["temp"] >= HOT]
    m["hot_commercial_reading_count"] = float(len(hot))
    m["hot_commercial_mean_kwh"] = statistics.fmean(hot)
    m["kwh_median"] = statistics.median(kwh)
    m["kwh_std"] = statistics.stdev(kwh)
    temps = [r["temp"] for r in recs if r["temp"] is not None]
    m["temperature_mean"] = statistics.fmean(temps)
    m["temperature_missing_count"] = float(len(recs) - len(temps))
    comm = [(r["temp"], r["kwh"]) for r in recs if r["type"] == "Commercial" and r["temp"] is not None]
    m["commercial_temp_kwh_corr"] = statistics.correlation([t for t, _ in comm], [k for _, k in comm])
    m["kwh_peak"] = total(lambda r: r["tariff"] == "peak")
    m["kwh_off_peak"] = total(lambda r: r["tariff"] == "off-peak")
    m["peak_kwh_share_pct"] = m["kwh_peak"] / m["total_kwh"] * 100
    by_meter: dict[str, float] = {}
    for r in recs:
        by_meter[r["meter"]] = by_meter.get(r["meter"], 0.0) + r["kwh"]
    m["unique_meter_count"] = float(len(by_meter))
    m["highest_use_meter_kwh"] = max(by_meter.values())
    return {k: r6(v) for k, v in m.items()}
