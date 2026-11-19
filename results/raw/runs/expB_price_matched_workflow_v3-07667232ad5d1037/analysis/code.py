import json
import os

import numpy as np
import pandas as pd

METRIC_KEYS = [
    'ticket_count',
    'mean_resolution_minutes',
    'total_labor_cost',
    'labor_cost_alpha',
    'labor_cost_beta',
    'labor_cost_gamma',
    'resolution_email',
    'resolution_chat',
    'resolution_phone',
    'reopen_rate_email_pct',
    'reopen_rate_chat_pct',
    'email_vs_chat_reopen_change_pct',
    'high_cost_low_sat_count',
    'high_cost_low_sat_reopen_pct',
    'resolution_median',
    'resolution_std',
    'satisfaction_mean',
    'satisfaction_missing_count',
    'unique_agent_count',
    'top_agent_ticket_count',
    'top_agent_ticket_share_pct',
]


def finite(value, default=0.0):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float(default)
    if not np.isfinite(result):
        return float(default)
    return result


def main():
    input_path = os.path.join(os.environ['INPUT_DIR'], 'cleaned.csv')
    output_path = os.path.join(os.environ['OUTPUT_DIR'], 'findings.json')

    df = pd.read_csv(input_path)

    resolution = pd.to_numeric(df['resolution_minutes'], errors='coerce')
    labor = pd.to_numeric(df['labor_cost'], errors='coerce')
    reopened = pd.to_numeric(df['reopened'], errors='coerce')
    satisfaction = pd.to_numeric(df['satisfaction_score'], errors='coerce')

    ticket_count = int(len(df))

    team_labor = labor.groupby(df['team']).sum()
    channel_resolution = resolution.groupby(df['channel']).mean()
    channel_reopen_pct = reopened.groupby(df['channel']).mean() * 100.0

    reopen_rate_email_pct = finite(channel_reopen_pct.get('email'))
    reopen_rate_chat_pct = finite(channel_reopen_pct.get('chat'))
    if reopen_rate_chat_pct == 0.0:
        email_vs_chat_reopen_change_pct = 0.0
    else:
        email_vs_chat_reopen_change_pct = (reopen_rate_email_pct - reopen_rate_chat_pct) / reopen_rate_chat_pct * 100.0

    segment_mask = (labor >= 100.0) & satisfaction.notna() & (satisfaction <= 2)
    segment_count = int(segment_mask.sum())
    if segment_count > 0:
        segment_reopen_pct = finite(reopened[segment_mask].mean() * 100.0)
    else:
        segment_reopen_pct = 0.0

    if ticket_count > 0:
        agent_counts = df['agent_id'].value_counts()
        unique_agent_count = int(df['agent_id'].nunique())
        top_agent_ticket_count = int(agent_counts.max())
        top_agent_ticket_share_pct = finite(top_agent_ticket_count / ticket_count * 100.0)
    else:
        unique_agent_count = 0
        top_agent_ticket_count = 0
        top_agent_ticket_share_pct = 0.0

    metrics = {
        'ticket_count': ticket_count,
        'mean_resolution_minutes': finite(resolution.mean()),
        'total_labor_cost': finite(labor.sum()),
        'labor_cost_alpha': finite(team_labor.get('Alpha')),
        'labor_cost_beta': finite(team_labor.get('Beta')),
        'labor_cost_gamma': finite(team_labor.get('Gamma')),
        'resolution_email': finite(channel_resolution.get('email')),
        'resolution_chat': finite(channel_resolution.get('chat')),
        'resolution_phone': finite(channel_resolution.get('phone')),
        'reopen_rate_email_pct': reopen_rate_email_pct,
        'reopen_rate_chat_pct': reopen_rate_chat_pct,
        'email_vs_chat_reopen_change_pct': finite(email_vs_chat_reopen_change_pct),
        'high_cost_low_sat_count': segment_count,
        'high_cost_low_sat_reopen_pct': segment_reopen_pct,
        'resolution_median': finite(resolution.median()),
        'resolution_std': finite(resolution.std(ddof=1)),
        'satisfaction_mean': finite(satisfaction.mean()),
        'satisfaction_missing_count': int(satisfaction.isna().sum()),
        'unique_agent_count': unique_agent_count,
        'top_agent_ticket_count': top_agent_ticket_count,
        'top_agent_ticket_share_pct': top_agent_ticket_share_pct,
    }

    if set(metrics) != set(METRIC_KEYS):
        raise ValueError('Metric keys do not match the required contract')

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as handle:
        json.dump(metrics, handle, allow_nan=False)


if __name__ == '__main__':
    main()
