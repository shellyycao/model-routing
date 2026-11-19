import json
import os

import numpy as np
import pandas as pd

MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-"}

TEAM_MAP = {
    "alpha": "Alpha", "team alpha": "Alpha",
    "beta": "Beta", "team beta": "Beta",
    "gamma": "Gamma", "team gamma": "Gamma",
}
REGION_MAP = {"east": "East", "e": "East", "west": "West", "w": "West"}
CHANNEL_MAP = {
    "email": "email", "e-mail": "email",
    "chat": "chat", "live chat": "chat",
    "phone": "phone", "call": "phone",
}
REOPENED_MAP = {
    "yes": 1, "y": 1, "true": 1, "1": 1,
    "no": 0, "n": 0, "false": 0, "0": 0,
}


def read_text_csv(path):
    """R1: read everything as text, strip whitespace, normalise missing tokens to NA."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df.columns = [str(c).strip() for c in df.columns]
    for col in df.columns:
        s = df[col].astype(str).str.strip()
        df[col] = s.where(~s.str.lower().isin(MISSING_TOKENS), pd.NA)
    return df


def parse_whole_number(value):
    """Return an int for whole-number text (incl. '47.0'), else NaN."""
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        pass
    try:
        f = float(str(value).strip())
        if np.isfinite(f) and f.is_integer():
            return int(f)
    except (TypeError, ValueError):
        pass
    return np.nan


def main():
    input_dir = os.environ["INPUT_DIR"]
    output_dir = os.environ["OUTPUT_DIR"]
    os.makedirs(output_dir, exist_ok=True)

    tickets = read_text_csv(os.path.join(input_dir, "tickets.csv"))
    agents = read_text_csv(os.path.join(input_dir, "agents.csv"))
    summary = {"raw_rows": int(len(tickets)), "agents_raw_rows": int(len(agents))}

    # R2: drop duplicate ticket_id rows first, keeping the first in raw-file order.
    n = len(tickets)
    tickets = tickets.drop_duplicates(subset="ticket_id", keep="first")
    summary["duplicate_ticket_rows_removed"] = int(n - len(tickets))

    # ticket_id is not nullable in the output schema.
    n = len(tickets)
    tickets = tickets[tickets["ticket_id"].notna()]
    summary["tickets_dropped_missing_ticket_id"] = int(n - len(tickets))

    # R3: normalise roster agent_id to upper case, dedupe keeping the first row.
    agents["agent_id"] = agents["agent_id"].str.upper()
    n = len(agents)
    agents = agents.drop_duplicates(subset="agent_id", keep="first")
    summary["duplicate_agent_rows_removed"] = int(n - len(agents))

    # R4: normalise team/region/hourly_cost and exclude invalid roster rows.
    agents["team_clean"] = agents["team"].str.lower().map(TEAM_MAP)
    agents["region_clean"] = agents["region"].str.lower().map(REGION_MAP)
    cost_text = (
        agents["hourly_cost"].fillna("").astype(str)
        .str.replace(r"(?i)usd", "", regex=True)
        .str.replace(r"[$,]", "", regex=True)
        .str.strip()
    )
    agents["hourly_cost_num"] = pd.to_numeric(cost_text, errors="coerce")
    valid_roster = (
        agents["agent_id"].notna()
        & agents["team_clean"].notna()
        & agents["region_clean"].notna()
        & agents["hourly_cost_num"].notna()
        & (agents["hourly_cost_num"] > 0)
    )
    n = len(agents)
    roster = agents.loc[
        valid_roster, ["agent_id", "team_clean", "region_clean", "hourly_cost_num"]
    ].rename(columns={
        "team_clean": "team",
        "region_clean": "region",
        "hourly_cost_num": "hourly_cost",
    })
    summary["roster_rows_excluded_invalid"] = int(n - len(roster))

    # R5: normalise ticket agent_id and inner-join to the cleaned roster.
    tickets["agent_id"] = tickets["agent_id"].str.upper()
    n = len(tickets)
    df = tickets.merge(roster, on="agent_id", how="inner")
    summary["tickets_dropped_no_matching_agent"] = int(n - len(df))

    # R6: map channel case-insensitively, drop invalid channels.
    df["channel_clean"] = df["channel"].str.lower().map(CHANNEL_MAP)
    n = len(df)
    df = df[df["channel_clean"].notna()]
    summary["tickets_dropped_invalid_channel"] = int(n - len(df))

    # R7: resolution_minutes -> whole number 1..480, drop invalid rows.
    res_text = (
        df["resolution_minutes"].fillna("").astype(str)
        .str.replace(r"(?i)\s*(minutes|min)\s*$", "", regex=True)
        .str.strip()
    )
    df["resolution_num"] = res_text.map(parse_whole_number)
    n = len(df)
    df = df[df["resolution_num"].notna() & df["resolution_num"].between(1, 480)]
    summary["tickets_dropped_invalid_resolution_minutes"] = int(n - len(df))

    # R8: satisfaction_score -> whole number 1..5; invalid/missing become empty.
    sat = df["satisfaction_score"].map(parse_whole_number)
    df["satisfaction_num"] = sat.where(sat.notna() & sat.between(1, 5)).astype("Int64")
    summary["tickets_satisfaction_score_set_empty"] = int(df["satisfaction_num"].isna().sum())

    # R9: reopened -> 1/0; drop invalid or missing values.
    df["reopened_num"] = df["reopened"].str.lower().map(REOPENED_MAP)
    n = len(df)
    df = df[df["reopened_num"].notna()]
    summary["tickets_dropped_invalid_reopened"] = int(n - len(df))

    # R10: labor cost derived from resolution time and hourly cost.
    df["labor_cost"] = (df["resolution_num"] / 60.0 * df["hourly_cost"]).round(2)

    # R11: final schema, sort by ticket_id, write CSV without index.
    out = pd.DataFrame({
        "ticket_id": df["ticket_id"].astype(str),
        "agent_id": df["agent_id"].astype(str),
        "team": pd.Categorical(df["team"], categories=["Alpha", "Beta", "Gamma"]),
        "region": pd.Categorical(df["region"], categories=["East", "West"]),
        "channel": pd.Categorical(df["channel_clean"], categories=["email", "chat", "phone"]),
        "resolution_minutes": df["resolution_num"].astype("int64"),
        "satisfaction_score": df["satisfaction_num"].astype("Int64"),
        "reopened": df["reopened_num"].astype("int64"),
        "hourly_cost": df["hourly_cost"].astype("float64"),
        "labor_cost": df["labor_cost"].astype("float64"),
    })
    out = out.sort_values("ticket_id", kind="mergesort").reset_index(drop=True)
    out.to_csv(os.path.join(output_dir, "cleaned.csv"), index=False)

    summary["cleaned_rows"] = int(len(out))
    with open(os.path.join(output_dir, "cleaning_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)


if __name__ == "__main__":
    main()
