def summarize_logs(lines):
    counts = {}
    first_error = None
    for line in lines:
        parts = line.split('|')
        if len(parts) != 4:
            continue
        ts, level, service, message = parts
        level = level.upper()
        service_counts = counts.setdefault(service, {})
        service_counts[level] = service_counts.get(level, 0) + 1
        if level == 'ERROR' and (first_error is None or ts < first_error):
            first_error = ts
    return {'counts': counts, 'first_error': first_error}
