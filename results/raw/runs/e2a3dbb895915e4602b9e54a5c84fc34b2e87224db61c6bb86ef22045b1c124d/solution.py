def summarize_logs(lines):
    counts = {}
    errors = []
    for line in lines:
        parts = line.split('|')
        if len(parts) < 4:
            continue
        ts, level, service = parts[:3]
        lvl = level.upper()
        service_counts = counts.setdefault(service, {})
        service_counts[lvl] = service_counts.get(lvl, 0) + 1
        if lvl == 'ERROR':
            errors.append(ts)
    return {'counts': counts, 'first_error': min(errors) if errors else None}
