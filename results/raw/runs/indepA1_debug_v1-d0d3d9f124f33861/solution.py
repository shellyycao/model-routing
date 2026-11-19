def rank_key(item):
    word, count = item
    return (-count, word)

def top_k(counts, k):
    return sorted(counts.items(), key=rank_key)[:max(k, 0)]