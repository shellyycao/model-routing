# SYNTHETIC_FIXTURE - independent pandas follower for the two-file project.
import pandas as pd

MISSING = {"", "na", "n/a", "null", "none", "-"}


def _s(v):
    x = str(v).strip()
    return None if x.lower() in MISSING else x


def clean(tickets: pd.DataFrame, bug=None, *, agents: pd.DataFrame) -> pd.DataFrame:
    t = tickets.astype(str).map(lambda x: x.strip()).drop_duplicates("ticket_id", keep="first").copy()
    a = agents.astype(str).map(lambda x: x.strip()).copy()
    a["agent_id"] = a["agent_id"].str.upper()
    a = a.drop_duplicates("agent_id", keep="first")
    a["team"] = a["team"].str.lower().map({"alpha": "Alpha", "team alpha": "Alpha",
                                              "beta": "Beta", "team beta": "Beta",
                                              "gamma": "Gamma", "team gamma": "Gamma"})
    a["region"] = a["region"].str.lower().map({"east": "East", "e": "East", "west": "West", "w": "West"})
    a["hourly_cost"] = pd.to_numeric(a["hourly_cost"].str.replace("USD", "", regex=False)
                                      .str.replace("$", "", regex=False).str.replace(",", "", regex=False),
                                      errors="coerce")
    a = a[a["team"].notna() & a["region"].notna() & (a["hourly_cost"] > 0)]
    t["agent_id"] = t["agent_id"].str.upper()
    t = t.merge(a, on="agent_id", how="inner")
    t["channel"] = t["channel"].str.lower().map({"email": "email", "e-mail": "email",
                                                    "chat": "chat", "live chat": "chat",
                                                    "phone": "phone", "call": "phone"})
    t["resolution_minutes"] = pd.to_numeric(t["resolution_minutes"].str.lower()
                                             .str.replace("minutes", "", regex=False)
                                             .str.replace("min", "", regex=False).str.strip(), errors="coerce")
    t = t[t["channel"].notna() & t["resolution_minutes"].between(1, 480)
          & (t["resolution_minutes"] % 1 == 0)]
    sat = pd.to_numeric(t["satisfaction_score"].map(_s), errors="coerce")
    t["satisfaction_score"] = sat.where(sat.between(1, 5) & (sat % 1 == 0))
    t["reopened"] = t["reopened"].str.lower().map({"yes": 1, "y": 1, "true": 1, "1": 1,
                                                      "no": 0, "n": 0, "false": 0, "0": 0})
    t = t[t["reopened"].notna()]
    t["resolution_minutes"] = t["resolution_minutes"].astype(int)
    t["reopened"] = t["reopened"].astype(int)
    t["labor_cost"] = (t["resolution_minutes"] / 60 * t["hourly_cost"]).round(2)
    cols = ["ticket_id", "agent_id", "team", "region", "channel", "resolution_minutes",
            "satisfaction_score", "reopened", "hourly_cost", "labor_cost"]
    return t[cols].sort_values("ticket_id").reset_index(drop=True)
