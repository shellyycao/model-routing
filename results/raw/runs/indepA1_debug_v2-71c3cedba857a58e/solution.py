def sessionize(events, gap):
    """Group events into user sessions.

    Args:
        events: Iterable of (user, timestamp) pairs.
        gap: Maximum allowed gap (inclusive) between consecutive timestamps
             within the same session. A new session starts when the gap is
             strictly greater than this value.

    Returns:
        Dict mapping each user to a list of sessions, where each session is a
        list of timestamps in chronological order.
    """
    # Output dictionary: user -> list of session lists
    out = {}
    # Keep track of the last timestamp seen for each user separately
    last_timestamp = {}

    # Sort by user first, then timestamp to ensure events for each user are
    # processed in chronological order without interleaving different users.
    for user, t in sorted(events, key=lambda x: (x[0], x[1])):
        # Initialise structures for a new user
        if user not in out:
            out[user] = [[]]          # start with the first session list
            last_timestamp[user] = None

        # Determine whether to start a new session for this user
        if last_timestamp[user] is not None and t - last_timestamp[user] > gap:
            out[user].append([])      # start a new session list

        # Append the timestamp to the current (most recent) session
        out[user][-1].append(t)
        # Update the last seen timestamp for this user
        last_timestamp[user] = t

    return out