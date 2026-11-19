def rank_key(item):
    word, count = item
    # Use negative count so that sorting ascending puts highest counts first,
    # while word remains natural (ascending) for tie‑breaks.
    return (-count, word)

def top_k(counts, k):
    # Sort using the corrected key and take the first k items (or all if k exceeds length).
    return sorted(counts.items(), key=rank_key)[:max(k, 0)]
