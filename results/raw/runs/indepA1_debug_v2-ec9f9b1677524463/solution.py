def summarize_logs(lines):
    counts = {}
    first_error = None
    for line in lines:
        parts = line.split('|')
        if len(parts)!= 4:
            continue
        ts, level, service, message = parts
        level = level.upper()
        if service not in counts:
            counts[service] = {}
        if level not in counts[service]:
            counts[service][level] = 0
        counts[service][level] += 1
        if level == 'ERROR' and (first_error is None or ts < first_error):
            first_error = ts
    return {'counts': counts, 'first_error': first_error}
