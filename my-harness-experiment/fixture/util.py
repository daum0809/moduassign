def chunk(items, size):
    return [items[i:i + size] for i in range(0, len(items), size)]


def safe_div(a, b):
    if b == 0:
        return None
    return a / b


def word_count(text, ignore=None):
    ignore = set(ignore or [])
    counts = {}
    for w in text.lower().split():
        if w in ignore:
            continue
        counts[w] = counts.get(w, 0) + 1
    return counts
