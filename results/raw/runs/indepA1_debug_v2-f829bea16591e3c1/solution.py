def summarize_logs(lines):
    counts = {}
    errors = []
    for line in lines:
        parts = line.split('|')
        if len(parts)!= 4:
            continue
        ts, level, service, message = parts
        if not ts or not level or not service or not message:
            continue
        counts.setdefault(service, {}).setdefault(level.upper(), 0)
        counts[service][level.upper()] += 1
        if level.upper() == 'ERROR':
            errors.append(ts)
    return {'counts': counts, 'first_error': min(errors) if errors else None}
