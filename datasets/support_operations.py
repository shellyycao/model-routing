"""Two-file benchmark project: support tickets joined to an agent roster."""

from __future__ import annotations

import math
import random
import statistics
from pathlib import Path

from src.contracts import AnalysisQuestion, ColumnSpec, InputFile, ProjectSpec, ReportingRequirement

from .common import fmt_num, is_missing, parse_number, r6, read_csv_text, whole_number, write_csv

PROJECT_ID = "support_operations"
SEED = 20261121
N_TICKETS = 360
N_AGENTS = 18
N_DUPLICATES = 20
KEY_COLUMN = "ticket_id"

RAW_COLUMNS = ["ticket_id", "agent_id", "channel", "resolution_minutes", "satisfaction_score", "reopened"]
AGENT_COLUMNS = ["agent_id", "team", "region", "hourly_cost"]
CLEAN_COLUMNS = ["ticket_id", "agent_id", "team", "region", "channel", "resolution_minutes",
                 "satisfaction_score", "reopened", "hourly_cost", "labor_cost"]

TEAMS = ("Alpha", "Beta", "Gamma")
REGIONS = ("East", "West")
CHANNELS = ("email", "chat", "phone")
TEAM_MAP = {"alpha": "Alpha", "team alpha": "Alpha", "beta": "Beta", "team beta": "Beta",
            "gamma": "Gamma", "team gamma": "Gamma"}
REGION_MAP = {"east": "East", "e": "East", "west": "West", "w": "West"}
CHANNEL_MAP = {"email": "email", "e-mail": "email", "chat": "chat", "live chat": "chat",
               "phone": "phone", "call": "phone"}

CLEAN_VALUE_ABS_TOL = 0.011
CLEAN_VALUE_REL_TOL = 1e-6

CLEANING_REQUIREMENTS = [
    "R1. Read both tickets.csv and agents.csv as text. Strip whitespace. Treat empty, NA, N/A, null, None and - as missing.",
    "R2. In tickets.csv, remove duplicate ticket_id rows before any filtering; keep the first in raw-file order.",
    "R3. In agents.csv, normalise agent_id to upper case and remove duplicate agent_id rows, keeping the first.",
    "R4. Agent roster: map team case-insensitively from Alpha/Team Alpha, Beta/Team Beta, Gamma/Team Gamma; "
    "map region East/E and West/W; parse hourly_cost after removing $, USD and commas. Exclude roster rows with an invalid field or cost <= 0.",
    "R5. Tickets: normalise agent_id to upper case. Join to the cleaned agent roster by agent_id and drop tickets without a matching agent.",
    "R6. Map channel case-insensitively: Email/E-mail -> email, Chat/Live Chat -> chat, Phone/Call -> phone. Drop invalid channels.",
    "R7. resolution_minutes: remove a trailing 'min' or 'minutes', parse a whole number from 1 through 480, and drop invalid rows.",
    "R8. satisfaction_score: parse a whole number from 1 through 5. Invalid or missing values become an empty cell and the row is kept.",
    "R9. reopened: map Yes/Y/True/1 to 1 and No/N/False/0 to 0, case-insensitively. Drop invalid or missing values.",
    "R10. Add labor_cost = resolution_minutes / 60 * hourly_cost, rounded to 2 decimals.",
    "R11. Output exactly: ticket_id, agent_id, team, region, channel, resolution_minutes, satisfaction_score, "
    "reopened, hourly_cost, labor_cost. Sort by ticket_id and write CSV without an index.",
]

T = dict(abs_tolerance=0.011, rel_tolerance=1e-4)
QUESTIONS = [
    AnalysisQuestion(question_id="q1", **T,
                     metric_keys=["ticket_count", "mean_resolution_minutes", "total_labor_cost"],
                     question="Overall: number of tickets -> ticket_count; mean resolution_minutes -> "
                              "mean_resolution_minutes; sum of labor_cost -> total_labor_cost."),
    AnalysisQuestion(question_id="q2", **T,
                     metric_keys=["labor_cost_alpha", "labor_cost_beta", "labor_cost_gamma"],
                     question="Team comparison: total labor_cost for Alpha, Beta and Gamma -> labor_cost_alpha, "
                              "labor_cost_beta, labor_cost_gamma.",
                     ranking_labels={"labor_cost_alpha": "Alpha", "labor_cost_beta": "Beta",
                                     "labor_cost_gamma": "Gamma"}),
    AnalysisQuestion(question_id="q3", **T,
                     metric_keys=["resolution_email", "resolution_chat", "resolution_phone"],
                     question="Channel comparison: mean resolution_minutes by channel -> resolution_email, "
                              "resolution_chat, resolution_phone.",
                     ranking_labels={"resolution_email": "email", "resolution_chat": "chat",
                                     "resolution_phone": "phone"}),
    AnalysisQuestion(question_id="q4", **T,
                     metric_keys=["reopen_rate_email_pct", "reopen_rate_chat_pct",
                                  "email_vs_chat_reopen_change_pct"],
                     question="Reopening change: reopened percentage for email and chat -> reopen_rate_email_pct, "
                              "reopen_rate_chat_pct; (email rate - chat rate) / chat rate * 100 -> "
                              "email_vs_chat_reopen_change_pct.",
                     direction_key="email_vs_chat_reopen_change_pct"),
    AnalysisQuestion(question_id="q5", **T,
                     metric_keys=["high_cost_low_sat_count", "high_cost_low_sat_reopen_pct"],
                     question="High-cost low-satisfaction segment: tickets with labor_cost >= 100 and a non-missing "
                              "satisfaction_score <= 2 -> count and reopened percentage as "
                              "high_cost_low_sat_count and high_cost_low_sat_reopen_pct."),
    AnalysisQuestion(question_id="q6", **T,
                     metric_keys=["resolution_median", "resolution_std", "satisfaction_mean",
                                  "satisfaction_missing_count"],
                     question="Distribution: median and sample standard deviation of resolution_minutes -> "
                              "resolution_median, resolution_std; mean non-missing satisfaction_score -> "
                              "satisfaction_mean; missing satisfaction count -> satisfaction_missing_count."),
    AnalysisQuestion(question_id="q7", **T,
                     metric_keys=["unique_agent_count", "top_agent_ticket_count", "top_agent_ticket_share_pct"],
                     question="Agent concentration (derived step): distinct agent_id count -> unique_agent_count; "
                              "largest ticket count for one agent -> top_agent_ticket_count; top_agent_ticket_count "
                              "/ ticket_count * 100 -> top_agent_ticket_share_pct."),
]

CLEANED_SCHEMA = [
    ColumnSpec(name="ticket_id", dtype="str"), ColumnSpec(name="agent_id", dtype="str"),
    ColumnSpec(name="team", dtype="category", allowed_values=list(TEAMS)),
    ColumnSpec(name="region", dtype="category", allowed_values=list(REGIONS)),
    ColumnSpec(name="channel", dtype="category", allowed_values=list(CHANNELS)),
    ColumnSpec(name="resolution_minutes", dtype="int", min_value=1, max_value=480),
    ColumnSpec(name="satisfaction_score", dtype="int", nullable=True, min_value=1, max_value=5),
    ColumnSpec(name="reopened", dtype="int", min_value=0, max_value=1),
    ColumnSpec(name="hourly_cost", dtype="float", min_value=0.01),
    ColumnSpec(name="labor_cost", dtype="float", min_value=0.0),
]


def project_spec() -> ProjectSpec:
    return ProjectSpec(
        project_id=PROJECT_ID, domain="customer support operations", seed=SEED,
        objective="Clean and join a support-ticket export with an agent roster, analyse cost, speed, reopening, satisfaction and agent concentration, then report verified findings.",
        raw_data_file="raw.csv",
        input_files=[InputFile(name="tickets.csv", path="raw.csv", description="support tickets"),
                     InputFile(name="agents.csv", path="agents.csv", description="agent roster")],
        cleaning_requirements=CLEANING_REQUIREMENTS, cleaned_schema=CLEANED_SCHEMA,
        analysis_questions=QUESTIONS,
        reporting=ReportingRequirement(required_finding_ids=[q.question_id for q in QUESTIONS], max_words=650),
        canonical_cleaned_file="canonical/cleaned.csv", canonical_findings_file="canonical/findings.json",
        ground_truth_file="ground_truth.json",
        notes="SYNTHETIC two-file join. Later duplicate tickets deliberately disagree in value; roster and ticket fields contain case, whitespace, currency, unit and missing-value variants.")


def _render_agent(rng: random.Random, a: dict) -> list[str]:
    aid = a["agent_id"].lower() if rng.random() < .25 else a["agent_id"]
    team = rng.choice([a["team"], a["team"].lower(), f"Team {a['team']}"])
    region = rng.choice([a["region"], a["region"].lower(), a["region"][0]])
    cost = rng.choice([f"{a['cost']:.2f}", f"${a['cost']:.2f}", f"USD {a['cost']:.2f}"])
    return [aid, team, region, cost]


def _render_ticket(rng: random.Random, t: dict) -> list[str]:
    channel_variants = {"email": ["Email", "E-mail"], "chat": ["Chat", "Live Chat"], "phone": ["Phone", "Call"]}
    aid = t["agent_id"].lower() if rng.random() < .2 else t["agent_id"]
    mins = rng.choice([str(t["minutes"]), f"{t['minutes']} min", f"{t['minutes']} minutes"])
    sat = "" if t["sat"] is None else str(t["sat"])
    reopened = rng.choice(["Yes", "Y", "1"]) if t["reopened"] else rng.choice(["No", "N", "0"])
    channel = rng.choice(channel_variants[t["channel"]]) if t["channel"] in channel_variants else t["channel"]
    return [t["ticket_id"], aid, channel, mins, sat, reopened]


def generate_raw(path: Path) -> dict:
    rng = random.Random(SEED)
    agents = [{"agent_id": f"A{i:03d}", "team": TEAMS[(i - 1) % 3], "region": REGIONS[i % 2],
               "cost": 42.0 + i * 2.25} for i in range(1, N_AGENTS + 1)]
    write_csv(path.parent / "agents.csv", AGENT_COLUMNS, [_render_agent(rng, a) for a in agents])
    tickets = []
    for i in range(1, N_TICKETS + 1):
        channel = rng.choices(CHANNELS, weights=[45, 35, 20])[0]
        minutes = max(5, min(450, round(rng.lognormvariate(4.1, .65))))
        sat = max(1, min(5, round(5.2 - minutes / 80 + rng.gauss(0, .8))))
        reopened = rng.random() < (.08 + .08 * (channel == "email") + .05 * (sat <= 2))
        tickets.append({"ticket_id": f"T{i:05d}", "agent_id": rng.choice(agents)["agent_id"],
                        "channel": channel, "minutes": minutes, "sat": sat, "reopened": reopened})
    injected = {"invalid_agent": 0, "invalid_channel": 0, "invalid_minutes": 0,
                "missing_satisfaction": 0, "invalid_reopened": 0}
    for t in tickets:
        u = rng.random()
        if u < .015:
            t["agent_id"] = "A999"; injected["invalid_agent"] += 1
        elif u < .025:
            t["channel"] = "fax"; injected["invalid_channel"] += 1
        elif u < .04:
            t["minutes"] = 999; injected["invalid_minutes"] += 1
        if rng.random() < .05:
            t["sat"] = None; injected["missing_satisfaction"] += 1
    keyed = [(float(i), _render_ticket(rng, t)) for i, t in enumerate(tickets)]
    exact = 0
    for i in sorted(rng.sample(range(len(tickets)), N_DUPLICATES)):
        if rng.random() < .5:
            row = list(keyed[i][1]); exact += 1
        else:
            row = _render_ticket(rng, tickets[i]); row[3] = "480 min"
        keyed.append((i + rng.uniform(1, 35), row))
    keyed.sort(key=lambda x: x[0])
    write_csv(path, RAW_COLUMNS, [r for _, r in keyed])
    injected["duplicate_rows_exact"] = exact
    injected["duplicate_rows_changed_value"] = N_DUPLICATES - exact
    return {"raw_row_count": len(keyed), "agent_row_count": len(agents), "injected": injected}


def reference_clean(raw_path: Path, out_path: Path) -> dict:
    _, agent_rows = read_csv_text(raw_path.parent / "agents.csv")
    roster = {}
    for row in agent_rows:
        aid = row["agent_id"].strip().upper()
        if aid in roster:
            continue
        team = TEAM_MAP.get(row["team"].strip().lower())
        region = REGION_MAP.get(row["region"].strip().lower())
        cost = parse_number(row["hourly_cost"], strip=("$", "USD", ","))
        if aid and team and region and cost is not None and cost > 0:
            roster[aid] = (team, region, cost)
    _, rows = read_csv_text(raw_path)
    seen, deduped = set(), []
    for row in rows:
        tid = row["ticket_id"].strip()
        if tid not in seen:
            seen.add(tid); deduped.append(row)
    log = {"raw_rows": len(rows), "R2_duplicates_removed": len(rows) - len(deduped),
           "R3_agent_roster_rows": len(roster)}
    drops = {"R5_agent_join": 0, "R6_channel": 0, "R7_resolution": 0, "R9_reopened": 0}
    sat_missing, out = 0, []
    for row in deduped:
        aid = row["agent_id"].strip().upper()
        if aid not in roster:
            drops["R5_agent_join"] += 1; continue
        channel = CHANNEL_MAP.get(row["channel"].strip().lower())
        if channel is None:
            drops["R6_channel"] += 1; continue
        raw_minutes = row["resolution_minutes"].strip().lower()
        for suffix in ("minutes", "min"):
            if raw_minutes.endswith(suffix):
                raw_minutes = raw_minutes[:-len(suffix)].strip(); break
        minutes = whole_number(parse_number(raw_minutes), 1, 480)
        if minutes is None:
            drops["R7_resolution"] += 1; continue
        sat_raw = row["satisfaction_score"].strip()
        sat = None if is_missing(sat_raw) else whole_number(parse_number(sat_raw), 1, 5)
        sat_missing += sat is None
        rr = row["reopened"].strip().lower()
        if rr in {"yes", "y", "true", "1"}: reopened = 1
        elif rr in {"no", "n", "false", "0"}: reopened = 0
        else:
            drops["R9_reopened"] += 1; continue
        team, region, cost = roster[aid]
        labor = round(minutes / 60 * cost, 2)
        out.append([row["ticket_id"].strip(), aid, team, region, channel, str(minutes),
                    "" if sat is None else str(sat), str(reopened), fmt_num(cost), fmt_num(labor)])
    out.sort(key=lambda r: r[0])
    write_csv(out_path, CLEAN_COLUMNS, out)
    log.update({f"dropped_{k}": v for k, v in drops.items()})
    log["R8_satisfaction_set_missing"] = sat_missing
    log["cleaned_rows"] = len(out)
    return log


def reference_analysis(cleaned_path: Path) -> dict[str, float]:
    header, rows = read_csv_text(cleaned_path)
    if missing := [c for c in CLEAN_COLUMNS if c not in header]:
        raise ValueError(f"cleaned file lacks columns {missing}")
    recs = [{"agent": r["agent_id"], "team": r["team"], "channel": r["channel"],
             "minutes": int(r["resolution_minutes"]),
             "sat": None if not r["satisfaction_score"].strip() else int(r["satisfaction_score"]),
             "reopened": int(r["reopened"]), "labor": float(r["labor_cost"])} for r in rows]
    rate = lambda xs: 100 * sum(r["reopened"] for r in xs) / len(xs)
    m = {"ticket_count": float(len(recs)),
         "mean_resolution_minutes": statistics.fmean(r["minutes"] for r in recs),
         "total_labor_cost": math.fsum(r["labor"] for r in recs)}
    for team in TEAMS:
        m[f"labor_cost_{team.lower()}"] = math.fsum(r["labor"] for r in recs if r["team"] == team)
    for channel in CHANNELS:
        m[f"resolution_{channel}"] = statistics.fmean(r["minutes"] for r in recs if r["channel"] == channel)
    email, chat = ([r for r in recs if r["channel"] == c] for c in ("email", "chat"))
    m["reopen_rate_email_pct"], m["reopen_rate_chat_pct"] = rate(email), rate(chat)
    m["email_vs_chat_reopen_change_pct"] = ((m["reopen_rate_email_pct"] - m["reopen_rate_chat_pct"])
                                               / m["reopen_rate_chat_pct"] * 100)
    segment = [r for r in recs if r["labor"] >= 100 and r["sat"] is not None and r["sat"] <= 2]
    m["high_cost_low_sat_count"] = float(len(segment))
    m["high_cost_low_sat_reopen_pct"] = rate(segment)
    mins = [r["minutes"] for r in recs]
    sats = [r["sat"] for r in recs if r["sat"] is not None]
    m.update(resolution_median=float(statistics.median(mins)), resolution_std=statistics.stdev(mins),
             satisfaction_mean=statistics.fmean(sats), satisfaction_missing_count=float(len(recs) - len(sats)))
    by_agent = {a: sum(r["agent"] == a for r in recs) for a in {r["agent"] for r in recs}}
    m["unique_agent_count"] = float(len(by_agent))
    m["top_agent_ticket_count"] = float(max(by_agent.values()))
    m["top_agent_ticket_share_pct"] = m["top_agent_ticket_count"] / m["ticket_count"] * 100
    return {k: r6(v) for k, v in m.items()}
