def summarize_logs(lines):
    counts = {}
    first_error = None
    for line in lines:
        parts = line.split('|')
        if len(parts) != 4:
            continue
        ts, level, service, message = parts
        level = level.upper()
        counts.setdefault(service, {})
        counts[service][level] = counts[service].get(level, 0) + 1
        if level == 'ERROR':
            if first_error is None or ts < first_error:
                first_error = ts
    return {'counts': counts, 'first_error': first_error}
