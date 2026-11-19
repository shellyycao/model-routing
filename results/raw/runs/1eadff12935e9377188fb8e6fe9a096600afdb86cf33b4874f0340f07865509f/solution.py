def summarize_logs(lines):
    counts = {}
    errors = []
    for line in lines:
        parts = line.split('|')
        if len(parts) < 4:
            continue
        ts, level, service = parts[0], parts[1], parts[2]
        normalized = level.upper()
        counts.setdefault(service, {})
        counts[service][normalized] = counts[service].get(normalized, 0) + 1
        if normalized == 'ERROR':
            errors.append(ts)
    return {'counts': counts, 'first_error': min(errors) if errors else None}
