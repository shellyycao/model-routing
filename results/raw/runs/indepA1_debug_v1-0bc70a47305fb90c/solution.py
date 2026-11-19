import re

def parse_duration(s):
    if not s:
        raise ValueError(s)
    m = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?", s)
    if not m or not m.group(0):
        raise ValueError(s)
    h, mi, se = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + se
