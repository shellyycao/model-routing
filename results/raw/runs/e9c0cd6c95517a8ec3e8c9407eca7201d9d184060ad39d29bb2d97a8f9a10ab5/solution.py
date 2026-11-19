def summarize_logs(lines):
    counts = {}
    errors = []
    for line in lines:
        parts = line.split('|')
        if len(parts) < 4:
            continue
        ts, level, service = parts[:3]
        level = level.upper()
        counts.setdefault(service, {})
        counts[service][level] = counts[service].get(level, 0) + 1
        if level == 'ERROR':
            errors.append(ts)
    return {'counts': counts, 'first_error': min(errors) if errors else None}