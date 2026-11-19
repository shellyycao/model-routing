def summarize_logs(lines):
    """Parse log lines and produce a summary.

    Each line is expected to be in the form:
        timestamp|LEVEL|service|message
    The function:
    * Skips lines that do not contain exactly four fields.
    * Normalises the log level to upper‑case.
    * Counts occurrences per *service* and per *level*.
    * Returns the lexicographically earliest timestamp of an ``ERROR`` line,
      or ``None`` if no error is present.
    """
    counts = {}
    first_error = None
    for line in lines:
        # Split into at most 4 parts so that a message may contain '|'.
        parts = line.split('|', 3)
        if len(parts) != 4:
            # Malformed line – ignore it.
            continue
        ts, level, service, _ = parts
        # Normalise level to upper‑case as required by the spec.
        level = level.upper()
        # Update the per‑service, per‑level counters.
        service_counts = counts.setdefault(service, {})
        service_counts[level] = service_counts.get(level, 0) + 1
        # Track the earliest ERROR timestamp.
        if level == 'ERROR':
            if first_error is None or ts < first_error:
                first_error = ts
    return {"counts": counts, "first_error": first_error}
