def summarize_logs(lines):
    counts = {}
    errors = []
    for line in lines:
        parts = line.split('|')
        if len(parts) < 4:
            continue
        ts, level, service = parts[0], parts[1], parts[2]
        level_upper = level.upper()
        counts.setdefault(service, {})
        counts[service][level_upper] = counts[service].get(level_upper, 0) + 1
        if level_upper == 'ERROR':
            errors.append(ts)
    return {'counts': counts, 'first_error': min(errors) if errors else None}
