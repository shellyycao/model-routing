"""A1 Python debugging cases (hand-authored, deterministic).

Each case: a clean REFERENCE implementation + exactly ONE injected bug (documented mutation operator),
a model-visible spec and 1-2 visible examples, and HIDDEN tests (Python expressions that must be True).
Ground truth is the reference behaviour; generate.py verifies that every hidden test passes on the
reference and at least one fails on the buggy version before anything is written.
"""

CASES = [
    dict(case_id="a1_01_moving_average", difficulty="easy", operator="off_by_one_range", func="moving_average",
         spec="moving_average(xs, k) returns the list of means of every contiguous window of length k in xs "
              "(len(xs) - k + 1 values). Return [] if k <= 0 or k > len(xs).",
         reference='''def moving_average(xs, k):
    if k <= 0 or k > len(xs):
        return []
    return [sum(xs[i:i + k]) / k for i in range(len(xs) - k + 1)]
''',
         buggy='''def moving_average(xs, k):
    if k <= 0 or k > len(xs):
        return []
    return [sum(xs[i:i + k]) / k for i in range(len(xs) - k)]
''',
         visible=["moving_average([1, 2, 3, 4], 2) == [1.5, 2.5, 3.5]"],
         hidden=["moving_average([1, 2, 3, 4], 2) == [1.5, 2.5, 3.5]", "moving_average([5], 1) == [5.0]",
                 "moving_average([1, 2, 3], 3) == [2.0]", "moving_average([1, 2, 3], 4) == []",
                 "moving_average([], 1) == []", "moving_average([1, 2], 0) == []",
                 "moving_average([2, 4, 6, 8, 10], 2) == [3.0, 5.0, 7.0, 9.0]",
                 "moving_average([1, 1, 1, 1], 1) == [1.0, 1.0, 1.0, 1.0]"]),
    dict(case_id="a1_02_is_leap", difficulty="easy", operator="missing_condition", func="is_leap",
         spec="is_leap(year) returns True for Gregorian leap years: divisible by 4, except centuries, "
              "except centuries divisible by 400.",
         reference='''def is_leap(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
''',
         buggy='''def is_leap(year):
    return year % 4 == 0 and year % 100 != 0
''',
         visible=["is_leap(2024) is True", "is_leap(1900) is False"],
         hidden=["is_leap(2024) is True", "is_leap(2023) is False", "is_leap(1900) is False", "is_leap(2000) is True",
                 "is_leap(2400) is True", "is_leap(2100) is False", "is_leap(4) is True", "is_leap(1) is False"]),
    dict(case_id="a1_03_median", difficulty="easy", operator="wrong_index_even_length", func="median",
         spec="median(xs) returns the median of a non-empty list of numbers (mean of the two middle values "
              "for even length). The input list must not be modified. Raise ValueError for an empty list.",
         reference='''def median(xs):
    if not xs:
        raise ValueError("empty")
    s = sorted(xs)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2
''',
         buggy='''def median(xs):
    if not xs:
        raise ValueError("empty")
    s = sorted(xs)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 else (s[mid] + s[mid + 1]) / 2 if mid + 1 < n else s[mid]
''',
         visible=["median([3, 1, 2]) == 2"],
         hidden=["median([3, 1, 2]) == 2", "median([4, 1, 3, 2]) == 2.5", "median([1, 2]) == 1.5", "median([7]) == 7",
                 "median([5, 5, 5, 5]) == 5", "median([10, 0, -10, 20]) == 5.0",
                 "(lambda a: (median(a), a)[1] == [3, 1, 2])([3, 1, 2])",
                 "_raises(lambda: median([]), ValueError)"]),
    dict(case_id="a1_04_count_words", difficulty="easy", operator="wrong_split", func="count_words",
         spec="count_words(text) returns a dict mapping each lower-cased word to its count. Words are separated "
              "by any whitespace (spaces, tabs, newlines, repeated). Empty or whitespace-only text gives {}.",
         reference='''def count_words(text):
    counts = {}
    for w in text.lower().split():
        counts[w] = counts.get(w, 0) + 1
    return counts
''',
         buggy='''def count_words(text):
    counts = {}
    for w in text.lower().split(" "):
        counts[w] = counts.get(w, 0) + 1
    return counts
''',
         visible=["count_words('a b a') == {'a': 2, 'b': 1}"],
         hidden=["count_words('a b a') == {'a': 2, 'b': 1}", "count_words('') == {}", "count_words('   ') == {}",
                 "count_words('Hello  hello') == {'hello': 2}", "count_words('x\\ty\\nx') == {'x': 2, 'y': 1}",
                 "count_words(' lead trail ') == {'lead': 1, 'trail': 1}", "count_words('One') == {'one': 1}"]),
    dict(case_id="a1_05_append_item", difficulty="medium", operator="mutable_default", func="append_item",
         spec="append_item(item, items=None) appends item to items and returns the list. When items is not "
              "given, a NEW empty list is used on every call (calls must not share state).",
         reference='''def append_item(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items
''',
         buggy='''def append_item(item, items=[]):
    items.append(item)
    return items
''',
         visible=["append_item(1) == [1]"],
         hidden=["append_item(1) == [1]", "(append_item(1), append_item(2))[1] == [2]",
                 "append_item('a', ['x']) == ['x', 'a']", "(lambda l: append_item(3, l) is l)([0])",
                 "[append_item(i) for i in range(3)] == [[0], [1], [2]]", "append_item(None) == [None]"]),
    dict(case_id="a1_06_binary_search", difficulty="medium", operator="loop_bound", func="binary_search",
         spec="binary_search(xs, target) returns an index i with xs[i] == target in the ascending sorted list xs, "
              "or -1 if target is absent.",
         reference='''def binary_search(xs, target):
    lo, hi = 0, len(xs) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if xs[mid] == target:
            return mid
        if xs[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
''',
         buggy='''def binary_search(xs, target):
    lo, hi = 0, len(xs) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if xs[mid] == target:
            return mid
        if xs[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
''',
         visible=["binary_search([1, 3, 5], 3) == 1"],
         hidden=["binary_search([1, 3, 5], 3) == 1", "binary_search([1, 3, 5], 5) == 2", "binary_search([1, 3, 5], 1) == 0",
                 "binary_search([1, 3, 5], 4) == -1", "binary_search([], 1) == -1", "binary_search([7], 7) == 0",
                 "binary_search([1, 2, 3, 4, 5, 6], 6) == 5", "binary_search([2, 4], 4) == 1"]),
    dict(case_id="a1_07_normalize", difficulty="medium", operator="integer_division", func="normalize",
         spec="normalize(scores) takes a dict name->non-negative number and returns name->share of the total "
              "as a float (shares sum to 1). If the total is 0, every share is 0.0.",
         reference='''def normalize(scores):
    total = sum(scores.values())
    if total == 0:
        return {k: 0.0 for k in scores}
    return {k: v / total for k, v in scores.items()}
''',
         buggy='''def normalize(scores):
    total = sum(scores.values())
    if total == 0:
        return {k: 0.0 for k in scores}
    return {k: v // total for k, v in scores.items()}
''',
         visible=["normalize({'a': 1, 'b': 1}) == {'a': 0.5, 'b': 0.5}"],
         hidden=["normalize({'a': 1, 'b': 1}) == {'a': 0.5, 'b': 0.5}", "normalize({'a': 3, 'b': 1}) == {'a': 0.75, 'b': 0.25}",
                 "normalize({'a': 0, 'b': 0}) == {'a': 0.0, 'b': 0.0}", "normalize({}) == {}", "normalize({'x': 5}) == {'x': 1.0}",
                 "abs(sum(normalize({'a': 1, 'b': 2, 'c': 3}).values()) - 1) < 1e-9",
                 "isinstance(normalize({'a': 2})['a'], float)"]),
    dict(case_id="a1_08_parse_duration", difficulty="medium", operator="wrong_constant", func="parse_duration",
         spec="parse_duration(s) converts strings like '1h30m', '45s', '2h', '1h0m5s' to total seconds (int). "
              "Units h, m, s each appear at most once, in that order. Raise ValueError for an empty or invalid string.",
         reference='''import re

def parse_duration(s):
    m = re.fullmatch(r"(?:(\\d+)h)?(?:(\\d+)m)?(?:(\\d+)s)?", s or "")
    if not s or not m:
        raise ValueError(s)
    h, mi, se = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + se
''',
         buggy='''import re

def parse_duration(s):
    m = re.fullmatch(r"(?:(\\d+)h)?(?:(\\d+)m)?(?:(\\d+)s)?", s or "")
    if not s or not m:
        raise ValueError(s)
    h, mi, se = (int(x) if x else 0 for x in m.groups())
    return h * 60 + mi * 60 + se
''',
         visible=["parse_duration('45s') == 45"],
         hidden=["parse_duration('45s') == 45", "parse_duration('1h30m') == 5400", "parse_duration('2h') == 7200",
                 "parse_duration('1h0m5s') == 3605", "parse_duration('10m') == 600", "_raises(lambda: parse_duration(''), ValueError)",
                 "_raises(lambda: parse_duration('5x'), ValueError)", "parse_duration('0s') == 0"]),
    dict(case_id="a1_09_top_k", difficulty="hard", operator="wrong_tie_break_two_functions", func="top_k",
         spec="top_k(counts, k) returns the k (word, count) pairs with the highest counts from dict counts, "
              "ordered by count descending and, for equal counts, by word ascending (alphabetical). "
              "rank_key(item) is the helper used for sorting. k larger than len(counts) returns all pairs.",
         reference='''def rank_key(item):
    word, count = item
    return (-count, word)

def top_k(counts, k):
    return sorted(counts.items(), key=rank_key)[:max(k, 0)]
''',
         buggy='''def rank_key(item):
    word, count = item
    return (count, word)

def top_k(counts, k):
    return sorted(counts.items(), key=rank_key, reverse=True)[:max(k, 0)]
''',
         visible=["top_k({'a': 3, 'b': 1}, 1) == [('a', 3)]"],
         hidden=["top_k({'a': 3, 'b': 1}, 1) == [('a', 3)]", "top_k({'b': 2, 'a': 2, 'c': 1}, 2) == [('a', 2), ('b', 2)]",
                 "top_k({'x': 1, 'y': 1, 'z': 1}, 3) == [('x', 1), ('y', 1), ('z', 1)]", "top_k({}, 3) == []",
                 "top_k({'a': 1}, 5) == [('a', 1)]", "top_k({'a': 5, 'b': 9}, 0) == []",
                 "top_k({'d': 4, 'c': 4, 'b': 7}, 3) == [('b', 7), ('c', 4), ('d', 4)]"]),
    dict(case_id="a1_10_merge_intervals", difficulty="hard", operator="unsorted_and_touching", func="merge_intervals",
         spec="merge_intervals(intervals) merges overlapping or touching closed intervals [start, end] given in any "
              "order and returns them sorted by start as a list of [start, end] lists. Touching means "
              "next.start == current.end. The input must not be modified.",
         reference='''def merge_intervals(intervals):
    out = []
    for s, e in sorted([list(iv) for iv in intervals]):
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out
''',
         buggy='''def merge_intervals(intervals):
    out = []
    for s, e in [list(iv) for iv in intervals]:
        if out and s < out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out
''',
         visible=["merge_intervals([[1, 3], [2, 6]]) == [[1, 6]]"],
         hidden=["merge_intervals([[1, 3], [2, 6]]) == [[1, 6]]", "merge_intervals([[1, 2], [2, 3]]) == [[1, 3]]",
                 "merge_intervals([[5, 6], [1, 2]]) == [[1, 2], [5, 6]]", "merge_intervals([[4, 8], [1, 5]]) == [[1, 8]]",
                 "merge_intervals([]) == []", "merge_intervals([[1, 10], [2, 3]]) == [[1, 10]]",
                 "(lambda a: (merge_intervals(a), a)[1] == [[3, 4], [1, 2]])([[3, 4], [1, 2]])",
                 "merge_intervals([[1, 1]]) == [[1, 1]]"]),
]
