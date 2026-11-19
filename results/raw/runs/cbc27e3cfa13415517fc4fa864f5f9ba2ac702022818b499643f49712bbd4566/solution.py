def summarize_logs(lines):
    counts={};errors=[]
    for line in lines:
        parts=line.split('|')
        if len(parts)<4:continue
        ts,level,service=parts[:3]
        norm_level=level.upper()
        counts.setdefault(service,{})
        counts[service][norm_level]=counts[service].get(norm_level,0)+1
        if norm_level=='ERROR':errors.append(ts)
    return {'counts':counts,'first_error':min(errors) if errors else None}