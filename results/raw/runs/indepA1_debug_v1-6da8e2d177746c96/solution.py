def count_words(text):
    counts = {}
    for w in text.lower().split():
        if w:  # Ensure the word is not empty
            counts[w] = counts.get(w, 0) + 1
    return counts
