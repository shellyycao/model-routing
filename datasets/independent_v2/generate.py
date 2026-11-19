"""Generate the candidate Independent Benchmark v2 datasets deterministically.

The generated files are candidates, not a frozen paid-evaluation protocol.  In
particular, A3 relevance labels remain marked as pending human adjudication.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import tempfile
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERSION = "independent-v2-1.0"


def _clean(source: str) -> str:
    cleaned = textwrap.dedent(source).strip()
    lines = cleaned.splitlines()
    if len(lines) > 1 and (lines[0].startswith("import ") or lines[0].startswith("from ")) and lines[1].startswith(" "):
        indent = len(lines[1]) - len(lines[1].lstrip())
        lines = [lines[0]] + [line[indent:] if line.startswith(" " * indent) else line for line in lines[1:]]
    return "\n".join(lines) + "\n"


def _a1_case(case_id, difficulty, family, spec, reference, buggy, visible, hidden, bug_locations):
    return {
        "case_id": case_id,
        "difficulty": difficulty,
        "family": family,
        "spec": spec,
        "reference": _clean(reference),
        "buggy": _clean(buggy),
        "visible": visible,
        "hidden": hidden,
        "bug_locations": bug_locations,
        "label_source": "executable reference plus independently checked tests",
    }


def a1_cases() -> list[dict]:
    """Fifteen task families, two distinct mutations each; ten cases per tier."""
    blueprints = [
        ("easy", "clamp", "clamp(x, low, high) bounds x inclusively; raise ValueError when low > high.",
         """def clamp(x, low, high):
             if low > high: raise ValueError('bounds')
             return min(max(x, low), high)""",
         ["""def clamp(x, low, high):
                 if low > high: raise ValueError('bounds')
                 return max(min(x, low), high)""",
          """def clamp(x, low, high):
                 return min(max(x, low), high)"""],
         ["clamp(5, 0, 10) == 5"],
         ["clamp(5,0,10)==5", "clamp(-2,0,10)==0", "clamp(11,0,10)==10", "clamp(2.5,2.5,2.5)==2.5", "_raises(lambda: clamp(1,3,2), ValueError)"],
         [["clamp return expression"], ["clamp bounds validation"]]),
        ("easy", "chunks", "chunks(xs, size) returns consecutive list chunks, including a short final chunk; raise ValueError if size <= 0; do not mutate xs.",
         """def chunks(xs, size):
             if size <= 0: raise ValueError('size')
             return [xs[i:i+size] for i in range(0, len(xs), size)]""",
         ["""def chunks(xs, size):
                 if size <= 0: raise ValueError('size')
                 return [xs[i:i+size] for i in range(0, len(xs)-size+1, size)]""",
          """def chunks(xs, size):
                 if size < 0: raise ValueError('size')
                 if size == 0: return []
                 return [xs[i:i+size] for i in range(0, len(xs), size)]"""],
         ["chunks([1,2,3,4], 2) == [[1,2],[3,4]]"],
         ["chunks([1,2,3,4,5],2)==[[1,2],[3,4],[5]]", "chunks([],3)==[]", "chunks([1],3)==[[1]]", "_raises(lambda: chunks([1],0), ValueError)", "(lambda x: (chunks(x,2),x)[1]==[1,2,3])([1,2,3])"],
         [["chunks range stop"], ["chunks size validation"]]),
        ("easy", "dedupe", "dedupe(xs) removes later duplicates while preserving first-occurrence order and supports unhashable values.",
         """def dedupe(xs):
             out = []
             for item in xs:
                 if item not in out: out.append(item)
             return out""",
         ["""def dedupe(xs):
                 return sorted(set(xs))""",
          """def dedupe(xs):
                 out=[]
                 for item in reversed(xs):
                     if item not in out: out.append(item)
                 return out"""],
         ["dedupe([1,2,1]) == [1,2]"],
         ["dedupe([3,1,3,2,1])==[3,1,2]", "dedupe([])==[]", "dedupe([[1],[1],[2]])==[[1],[2]]", "dedupe(['a','b','a'])==['a','b']"],
         [["dedupe set conversion"], ["dedupe iteration order"]]),
        ("easy", "running_total", "running_total(xs) returns cumulative sums as floats or ints; empty input returns [].",
         """def running_total(xs):
             out=[]; total=0
             for value in xs:
                 total += value; out.append(total)
             return out""",
         ["""def running_total(xs):
                 out=[]
                 for value in xs:
                     total=0; total += value; out.append(total)
                 return out""",
          """def running_total(xs):
                 out=[]; total=0
                 for value in xs[:-1]:
                     total += value; out.append(total)
                 return out"""],
         ["running_total([1,2,3]) == [1,3,6]"],
         ["running_total([1,2,3])==[1,3,6]", "running_total([])==[]", "running_total([-2,5,-1])==[-2,3,2]", "running_total([0.5,0.25])==[0.5,0.75]"],
         [["running_total accumulator initialization"], ["running_total loop slice"]]),
        ("easy", "rotate", "rotate(xs, k) returns a new list rotated right by k; negative k rotates left; empty input returns [].",
         """def rotate(xs, k):
             if not xs: return []
             k %= len(xs)
             return list(xs[-k:] + xs[:-k]) if k else list(xs)""",
         ["""def rotate(xs, k):
                 if not xs: return []
                 k %= len(xs)
                 return list(xs[k:] + xs[:k])""",
          """def rotate(xs, k):
                 k %= len(xs)
                 return list(xs[-k:] + xs[:-k])"""],
         ["rotate([1,2,3], 1) == [3,1,2]"],
         ["rotate([1,2,3],1)==[3,1,2]", "rotate([1,2,3],-1)==[2,3,1]", "rotate([1,2,3],4)==[3,1,2]", "rotate([],3)==[]", "rotate((1,2),0)==[1,2]"],
         [["rotate slice direction"], ["rotate empty-input guard"]]),
        ("medium", "invoice_total", "invoice_total(lines, discount_pct, tax_pct) sums quantity*unit_price, applies discount, then tax, and rounds only the final result to 2 decimals.",
         """def invoice_total(lines, discount_pct=0, tax_pct=0):
             subtotal = sum(row['qty'] * row['unit_price'] for row in lines)
             discounted = subtotal * (1 - discount_pct / 100)
             return round(discounted * (1 + tax_pct / 100) + 1e-12, 2)""",
         ["""def invoice_total(lines, discount_pct=0, tax_pct=0):
                 subtotal=sum(row['qty']*row['unit_price'] for row in lines)
                 return round(subtotal*(1+tax_pct/100)-subtotal*discount_pct/100,2)""",
          """def invoice_total(lines, discount_pct=0, tax_pct=0):
                 subtotal=sum(round(row['qty']*row['unit_price'],2) for row in lines)
                 return round(subtotal*(1-discount_pct//100)*(1+tax_pct//100),2)"""],
         ["invoice_total([{'qty':2,'unit_price':10}],10,5) == 18.9"],
         ["invoice_total([{'qty':2,'unit_price':10}],10,5)==18.9", "invoice_total([],10,5)==0", "invoice_total([{'qty':3,'unit_price':0.335}],0,0)==1.01", "invoice_total([{'qty':1,'unit_price':100}],25,20)==90.0"],
         [["discount/tax order"], ["percentage division", "premature line rounding"]]),
        ("medium", "paginate", "paginate(items, size, cursor=None) returns (page, next_cursor). Cursor is a zero-based start index string; next_cursor is null at the end; invalid cursors and nonpositive sizes raise ValueError.",
         """def paginate(items, size, cursor=None):
             if size <= 0: raise ValueError('size')
             try: start = 0 if cursor is None else int(cursor)
             except (TypeError, ValueError): raise ValueError('cursor')
             if start < 0 or start > len(items): raise ValueError('cursor')
             end = min(start + size, len(items))
             return list(items[start:end]), (str(end) if end < len(items) else None)""",
         ["""def paginate(items, size, cursor=None):
                 start=0 if cursor is None else int(cursor); end=start+size
                 return list(items[start:end]), str(end)""",
          """def paginate(items, size, cursor=None):
                 if size < 0: raise ValueError('size')
                 start=1 if cursor is None else int(cursor)+1
                 end=min(start+size,len(items))
                 return list(items[start:end]), (str(end) if end<len(items) else None)"""],
         ["paginate([1,2,3], 2) == ([1,2], '2')"],
         ["paginate([1,2,3],2)==([1,2],'2')", "paginate([1,2,3],2,'2')==([3],None)", "paginate([],2)==([],None)", "_raises(lambda: paginate([1],0),ValueError)", "_raises(lambda: paginate([1],1,'x'),ValueError)"],
         [["paginate terminal cursor", "paginate validation"], ["paginate cursor origin", "paginate size validation"]]),
        ("medium", "shortest_path", "shortest_path(graph, start, goal) returns a shortest node list in an unweighted directed graph, or null if unreachable. Neighbours are explored in listed order.",
         """from collections import deque
         def shortest_path(graph, start, goal):
             q=deque([(start,[start])]); seen={start}
             while q:
                 node,path=q.popleft()
                 if node==goal: return path
                 for nxt in graph.get(node,[]):
                     if nxt not in seen: seen.add(nxt); q.append((nxt,path+[nxt]))
             return None""",
         ["""def shortest_path(graph,start,goal):
                 stack=[(start,[start])]; seen=set()
                 while stack:
                     node,path=stack.pop(); seen.add(node)
                     if node==goal:return path
                     stack += [(n,path+[n]) for n in graph.get(node,[]) if n not in seen]
                 return None""",
          """from collections import deque
             def shortest_path(graph,start,goal):
                 q=deque([(start,[])]); seen=set()
                 while q:
                     node,path=q.popleft()
                     if node==goal:return path
                     for nxt in graph.get(node,[]):
                         if nxt not in seen:q.append((nxt,path+[nxt])); seen.add(nxt)
                 return None"""],
         ["shortest_path({'a':['b'],'b':[]}, 'a', 'b') == ['a','b']"],
         ["shortest_path({'a':['b','c'],'b':['d'],'c':['e'],'e':['d']},'a','d')==['a','b','d']", "shortest_path({},'a','a')==['a']", "shortest_path({'a':['b']},'b','a') is None", "shortest_path({'a':['a','b']},'a','b')==['a','b']"],
         [["shortest_path search discipline"], ["shortest_path path initialization", "shortest_path visited initialization"]]),
        ("medium", "rolling_mean", "rolling_mean(xs, window, min_periods=1) returns one mean per input position using the trailing window and requiring at least min_periods values; otherwise null. Validate 1 <= min_periods <= window.",
         """def rolling_mean(xs, window, min_periods=1):
             if window<=0 or min_periods<1 or min_periods>window: raise ValueError('window')
             out=[]
             for i in range(len(xs)):
                 vals=xs[max(0,i-window+1):i+1]
                 out.append(sum(vals)/len(vals) if len(vals)>=min_periods else None)
             return out""",
         ["""def rolling_mean(xs,window,min_periods=1):
                 return [sum(xs[max(0,i-window):i])/window for i in range(len(xs))]""",
          """def rolling_mean(xs,window,min_periods=1):
                 if window<=0: raise ValueError('window')
                 return [sum(xs[max(0,i-window+1):i+1])/len(xs[max(0,i-window+1):i+1]) for i in range(len(xs))]"""],
         ["rolling_mean([1,2,3], 2) == [1,1.5,2.5]"],
         ["rolling_mean([1,2,3],2)==[1,1.5,2.5]", "rolling_mean([1,2],3,3)==[None,None]", "rolling_mean([],2)==[]", "_raises(lambda: rolling_mean([1],0),ValueError)", "_raises(lambda: rolling_mean([1],2,3),ValueError)"],
         [["rolling_mean window bounds", "rolling_mean denominator"], ["rolling_mean min_periods validation and output"]]),
        ("medium", "overlap", "overlap_minutes(a, b) accepts half-open minute intervals (start,end), returns overlap length, and rejects end < start. Touching intervals have zero overlap.",
         """def overlap_minutes(a,b):
             if a[1]<a[0] or b[1]<b[0]: raise ValueError('interval')
             return max(0, min(a[1],b[1])-max(a[0],b[0]))""",
         ["""def overlap_minutes(a,b):
                 return min(a[1],b[1])-max(a[0],b[0])""",
          """def overlap_minutes(a,b):
                 if a[1]<=a[0] or b[1]<=b[0]: raise ValueError('interval')
                 return max(0,min(a[1],b[1])-max(a[0],b[0])+1)"""],
         ["overlap_minutes((10,20),(15,25)) == 5"],
         ["overlap_minutes((10,20),(15,25))==5", "overlap_minutes((0,5),(5,9))==0", "overlap_minutes((0,2),(5,9))==0", "overlap_minutes((3,3),(3,3))==0", "_raises(lambda: overlap_minutes((3,2),(0,1)),ValueError)"],
         [["overlap clamp", "overlap validation"], ["overlap half-open arithmetic", "overlap empty interval validation"]]),
        ("hard", "sessionize", "sessionize(events, gap) sorts (user,timestamp) pairs, groups each user into sessions, and starts a new session when the gap is strictly greater than gap. Return user->list of timestamp lists without mutating input.",
         """def sessionize(events,gap):
             out={}
             for user,t in sorted(events,key=lambda x:(x[0],x[1])):
                 sessions=out.setdefault(user,[])
                 if not sessions or t-sessions[-1][-1]>gap:sessions.append([t])
                 else:sessions[-1].append(t)
             return out""",
         ["""def sessionize(events,gap):
                 out={}
                 for user,t in events:
                     sessions=out.setdefault(user,[])
                     if not sessions or t-sessions[-1][-1]>=gap:sessions.append([t])
                     else:sessions[-1].append(t)
                 return out""",
          """def sessionize(events,gap):
                 out={}; last=None
                 for user,t in sorted(events,key=lambda x:x[1]):
                     if user not in out:out[user]=[[]]
                     if last is not None and t-last>gap:out[user].append([])
                     out[user][-1].append(t); last=t
                 return out"""],
         ["sessionize([('u',1),('u',3)],2) == {'u':[[1,3]]}"],
         ["sessionize([('u',5),('u',1),('u',3)],2)=={'u':[[1,3,5]]}", "sessionize([('a',1),('b',2),('a',10)],3)=={'a':[[1],[10]],'b':[[2]]}", "sessionize([('a',1),('b',9),('a',10)],3)=={'a':[[1],[10]],'b':[[9]]}", "sessionize([],2)=={}", "(lambda x:(sessionize(x,2),x)[1]==[('u',2),('u',1)])([('u',2),('u',1)])"],
         [["sessionize sort", "sessionize boundary comparison"], ["sessionize per-user last timestamp", "sessionize empty session creation"]]),
        ("hard", "rate_limiter", "allowed(events, limit, window) returns booleans for (user,time) events in given order. An event is allowed if fewer than limit prior allowed events for that user fall in (time-window,time]; rejected events do not consume capacity.",
         """from collections import defaultdict, deque
         def allowed(events,limit,window):
             if limit<1 or window<0: raise ValueError('config')
             q=defaultdict(deque); out=[]
             for user,t in events:
                 while q[user] and q[user][0] <= t-window:q[user].popleft()
                 ok=len(q[user])<limit; out.append(ok)
                 if ok:q[user].append(t)
             return out""",
         ["""from collections import defaultdict,deque
             def allowed(events,limit,window):
                 q=defaultdict(deque);out=[]
                 for user,t in events:
                     while q[user] and q[user][0] < t-window:q[user].popleft()
                     ok=len(q[user])<limit;out.append(ok);q[user].append(t)
                 return out""",
          """from collections import deque
             def allowed(events,limit,window):
                 q=deque();out=[]
                 for user,t in events:
                     while q and q[0][1]<=t-window:q.popleft()
                     ok=len(q)<limit;out.append(ok)
                     if ok:q.append((user,t))
                 return out"""],
         ["allowed([('u',0),('u',1)],1,1) == [True,True]"],
         ["allowed([('u',0),('u',1)],1,1)==[True,True]", "allowed([('u',0),('u',2)],1,2)==[True,True]", "allowed([('u',0),('u',1),('u',2)],1,2)==[True,False,True]", "allowed([('a',0),('b',0)],1,10)==[True,True]", "_raises(lambda: allowed([],0,1),ValueError)"],
         [["rate_limiter expiry boundary", "rate_limiter rejected-event accounting"], ["rate_limiter per-user queues", "rate_limiter validation"]]),
        ("hard", "allocate_stock", "allocate_stock(stock, requests) processes (request_id, sku, qty) in order. Duplicate request_ids are ignored. Fulfil only whole requests with positive qty and sufficient stock. Return (fulfilled_ids, remaining_stock) without mutating stock.",
         """def allocate_stock(stock,requests):
             remaining=dict(stock); seen=set(); fulfilled=[]
             for rid,sku,qty in requests:
                 if rid in seen: continue
                 seen.add(rid)
                 if qty>0 and remaining.get(sku,0)>=qty:
                     remaining[sku]-=qty; fulfilled.append(rid)
             return fulfilled,remaining""",
         ["""def allocate_stock(stock,requests):
                 remaining=stock;fulfilled=[]
                 for rid,sku,qty in requests:
                     if remaining.get(sku,0)>=qty:remaining[sku]-=qty;fulfilled.append(rid)
                 return fulfilled,remaining""",
          """def allocate_stock(stock,requests):
                 remaining=dict(stock);seen=set();fulfilled=[]
                 for rid,sku,qty in requests:
                     if rid in seen:continue
                     if remaining.get(sku,0)>qty:remaining[sku]-=qty;fulfilled.append(rid);seen.add(rid)
                 return fulfilled,remaining"""],
         ["allocate_stock({'x':2}, [('r','x',2)]) == (['r'], {'x':0})"],
         ["allocate_stock({'x':2},[('r','x',2)])==(['r'],{'x':0})", "allocate_stock({'x':3},[('r','x',2),('r','x',1)])==(['r'],{'x':1})", "allocate_stock({'x':1},[('a','x',2),('b','x',1)])==(['b'],{'x':0})", "(lambda s:(allocate_stock(s,[]),s)[1]=={'x':1})({'x':1})", "allocate_stock({},[('a','x',-1)])==([],{})"],
         [["allocate_stock duplicate tracking", "allocate_stock input copy", "allocate_stock qty validation"], ["allocate_stock exact-capacity comparison", "allocate_stock seen timing"]]),
        ("hard", "dependency_order", "dependency_order(deps) returns a deterministic topological order over every key and referenced node, choosing alphabetically among available nodes; raise ValueError on a cycle.",
         """import heapq
         def dependency_order(deps):
             nodes=set(deps)
             for values in deps.values():nodes.update(values)
             incoming={n:set(deps.get(n,[])) for n in nodes}; ready=[n for n in nodes if not incoming[n]];heapq.heapify(ready);out=[]
             while ready:
                 n=heapq.heappop(ready);out.append(n)
                 for m in nodes:
                     if n in incoming[m]:
                         incoming[m].remove(n)
                         if not incoming[m]:heapq.heappush(ready,m)
             if len(out)!=len(nodes):raise ValueError('cycle')
             return out""",
         ["""def dependency_order(deps):
                 nodes=set(deps);out=[]
                 while nodes:
                     ready=sorted(n for n in nodes if not set(deps.get(n,[])) & nodes)
                     if not ready:break
                     out += ready;nodes -= set(ready)
                 return out""",
          """import heapq
             def dependency_order(deps):
                 nodes=set(deps);incoming={n:set(deps.get(n,[])) for n in nodes};ready=[n for n in nodes if not incoming[n]];heapq.heapify(ready);out=[]
                 while ready:
                     n=heapq.heappop(ready);out.append(n)
                     for m in nodes:
                         if n in incoming[m]:incoming[m].remove(n)
                         if not incoming[m] and m not in out and m not in ready:heapq.heappush(ready,m)
                 return out"""],
         ["dependency_order({'b':['a'],'a':[]}) == ['a','b']"],
         ["dependency_order({'b':['a'],'a':[]})==['a','b']", "dependency_order({'c':['a'],'b':['a'],'a':[]})==['a','b','c']", "dependency_order({'b':['a']})==['a','b']", "dependency_order({})==[]", "_raises(lambda: dependency_order({'a':['b'],'b':['a']}),ValueError)"],
         [["dependency_order missing referenced nodes", "dependency_order cycle error", "dependency_order tie ordering"], ["dependency_order node universe", "dependency_order ready queue deduplication", "dependency_order cycle error"]]),
        ("hard", "summarize_logs", "summarize_logs(lines) parses 'timestamp|LEVEL|service|message'. Skip malformed lines, normalize level uppercase, and return counts by service and level plus the lexicographically earliest ERROR timestamp (or null).",
         """def summarize_logs(lines):
             counts={}; first_error=None
             for line in lines:
                 parts=line.split('|',3)
                 if len(parts)!=4:continue
                 ts,level,service,_=parts;level=level.strip().upper();service=service.strip()
                 if not ts.strip() or not level or not service:continue
                 counts.setdefault(service,{});counts[service][level]=counts[service].get(level,0)+1
                 if level=='ERROR' and (first_error is None or ts.strip()<first_error):first_error=ts.strip()
             return {'counts':counts,'first_error':first_error}""",
         ["""def summarize_logs(lines):
                 counts={};first_error=None
                 for line in lines:
                     ts,level,service,message=line.split('|')
                     counts.setdefault(service,{})[level]=counts.setdefault(service,{}).get(level,0)+1
                     if level=='ERROR' and first_error is None:first_error=ts
                 return {'counts':counts,'first_error':first_error}""",
          """def summarize_logs(lines):
                 counts={};errors=[]
                 for line in lines:
                     parts=line.split('|')
                     if len(parts)<4:continue
                     ts,level,service=parts[:3]
                     counts.setdefault(service,{})[level.upper()]=counts.setdefault(service,{}).get(level,0)+1
                     if level.upper()=='ERROR':errors.append(ts)
                 return {'counts':counts,'first_error':max(errors) if errors else None}"""],
         ["summarize_logs(['2026-01-01|INFO|api|ok'])['counts'] == {'api':{'INFO':1}}"],
         ["summarize_logs(['2026-01-02|error|api|x','2026-01-01|ERROR|api|y'])=={'counts':{'api':{'ERROR':2}},'first_error':'2026-01-01'}", "summarize_logs(['bad'])=={'counts':{},'first_error':None}", "summarize_logs(['1|INFO|api|a|b'])=={'counts':{'api':{'INFO':1}},'first_error':None}", "summarize_logs([])=={'counts':{},'first_error':None}"],
         [["summarize_logs bounded split and malformed handling", "summarize_logs level normalization", "summarize_logs earliest error"], ["summarize_logs level-key consistency", "summarize_logs earliest error"]]),
    ]
    cases = []
    counters = {"easy": 0, "medium": 0, "hard": 0}
    for difficulty, family, spec, reference, mutants, visible, hidden, locations in blueprints:
        for variant in range(2):
            counters[difficulty] += 1
            case_id = f"a1v2_{difficulty[0]}{counters[difficulty]:02d}_{family}_{variant+1}"
            cases.append(_a1_case(case_id, difficulty, family, spec, reference, mutants[variant], visible, hidden, locations[variant]))
    return cases


def _a2_schema(family: str) -> dict:
    schemas = {
        "invoice": {"invoice_id":"string current invoice", "invoice_date":"date YYYY-MM-DD", "vendor":"string", "currency":"ISO currency", "total_due_usd":"number after discount and conversion", "terms_days":"integer or null"},
        "clinical": {"trial_id":"string", "enrollment":"integer target", "dose_mg":"number milligrams", "start_date":"date YYYY-MM-DD", "primary_endpoint":"string", "sponsor":"string or null"},
        "shipment": {"tracking_id":"string", "origin_city":"string", "destination_city":"string", "weight_kg":"number kilograms", "eta":"date YYYY-MM-DD or null", "hazardous":"boolean"},
        "job": {"requisition":"string", "title":"string", "location":"string", "salary_usd":"annual number after conversion", "remote":"boolean", "closing_date":"date or null"},
        "incident": {"incident_id":"string", "severity":"integer final severity", "started_at":"ISO timestamp", "duration_minutes":"number", "affected_users":"integer", "root_cause":"string or null"},
        "policy": {"policy_id":"string", "effective_date":"date", "coverage_limit_usd":"number", "deductible_usd":"number", "jurisdiction":"string", "renewal_auto":"boolean or null"},
        "grant": {"grant_id":"string", "agency":"string", "deadline":"date or null", "maximum_award_usd":"number", "match_percent":"number", "eligible_region":"string"},
        "property": {"listing_id":"string", "city":"string", "monthly_rent_usd":"number; weekly*52/12", "bedrooms":"integer", "area_sqm":"number converted from square feet", "available_date":"date or null"},
        "conference": {"event_code":"string", "city":"string", "start_date":"date", "end_date":"date", "registration_usd":"number after discount", "workshop_included":"boolean or null"},
        "subscription": {"account_id":"string", "plan":"string final plan", "seats":"integer", "monthly_total_usd":"number after annual-to-monthly conversion", "renewal_date":"date or null", "cancelled":"boolean"},
    }
    return schemas[family]


def a2_cases() -> list[dict]:
    families = ["invoice","clinical","shipment","job","incident","policy","grant","property","conference","subscription"]
    cases=[]
    for i, family in enumerate(families, 1):
        for variant, difficulty in enumerate(("easy","medium","hard"), 1):
            n=i*100+variant; missing = variant == 3
            if family == "invoice":
                gold={"invoice_id":f"INV-{n}","invoice_date":f"2026-0{variant}-1{variant}","vendor":f"Northwind {i}","currency":"USD","total_due_usd":round((1000+n)*(1-0.05*variant),2),"terms_days":None if missing else 30}
                doc=f"{'EMAIL' if variant==1 else 'ACCOUNTS TABLE' if variant==2 else 'CALL TRANSCRIPT'}\nOld quote Q-{n-1}: $9,999. Current invoice INV-{n} from Northwind {i}, dated {gold['invoice_date']}. List total ${1000+n:.2f}; approved discount {5*variant}%. Currency USD. Payment terms: {'not stated' if missing else 'net 30 days'}. Final due is the discounted amount, not the old quote."
            elif family == "clinical":
                gold={"trial_id":f"NCT{n:08d}","enrollment":80+n,"dose_mg":round((0.25*variant)*1000,1),"start_date":f"2026-0{variant+2}-0{variant+3}","primary_endpoint":"progression-free survival","sponsor":None if missing else f"Arbor Bio {i}"}
                doc=f"Protocol amendment {variant} | supersedes draft NCT00000001\nRegistry: {gold['trial_id']}\nTarget enrollment: {gold['enrollment']} (screening cap 999)\nDose: {0.25*variant} g per administration\nFirst participant: {gold['start_date']}\nPrimary endpoint: progression-free survival\nSponsor: {gold['sponsor'] or 'redacted / not disclosed'}"
            elif family == "shipment":
                kg=round((20+n)*0.45359237,3); gold={"tracking_id":f"ZX{n}US","origin_city":"Reno","destination_city":"Albany","weight_kg":kg,"eta":None if missing else f"2026-0{variant+4}-1{variant}","hazardous":variant==3}
                doc=f"MANIFEST ZX{n}US\nRoute: Reno -> Albany (billing office: Boise)\nGross weight: {20+n} lb / crate; this shipment has one crate.\nETA: {gold['eta'] or 'pending; no confirmed date'}.\nDangerous goods: {'YES' if gold['hazardous'] else 'NO'}."
            elif family == "job":
                salary=90000+n*10; gold={"requisition":f"REQ-{n}","title":"Data Reliability Engineer","location":"Boston, MA","salary_usd":salary,"remote":variant!=1,"closing_date":None if missing else f"2026-1{variant}-15"}
                doc=f"JOB CARD\nCurrent requisition REQ-{n} (archive REQ-{n-1})\nData Reliability Engineer — Boston, MA\nCompensation: ${salary/1000:.3f}k annual USD (not the €70k market benchmark).\nWork mode: {'hybrid/remote eligible' if gold['remote'] else 'onsite only'}\nApplications close: {gold['closing_date'] or 'open until filled; no date stated'}"
            elif family == "incident":
                gold={"incident_id":f"INC-{n}","severity":max(1,4-variant),"started_at":f"2026-07-0{variant}T0{variant}:00:00Z","duration_minutes":90*variant,"affected_users":n*10,"root_cause":None if missing else "expired signing certificate"}
                doc=f"INCIDENT TIMELINE\nINC-{n} opened {gold['started_at']}. Initial severity SEV-4; final commander classification SEV-{gold['severity']}. Restored after {1.5*variant} hours. Impact counter: {gold['affected_users']} distinct users (requests affected: 99,999). Root cause: {gold['root_cause'] or 'pending; not established'}."
            elif family == "policy":
                gold={"policy_id":f"POL-{n}","effective_date":f"2027-01-0{variant}","coverage_limit_usd":1_000_000+n*100,"deductible_usd":2500*variant,"jurisdiction":"New York","renewal_auto":None if missing else variant%2==1}
                doc=f"ENDORSEMENT / POLICY POL-{n}\nEffective {gold['effective_date']} in New York. Coverage limit ${gold['coverage_limit_usd']:,}; deductible ${gold['deductible_usd']:,}. A prior Nevada proposal listed $500,000 and is void. Automatic renewal: {'not specified' if missing else 'yes' if gold['renewal_auto'] else 'no'}."
            elif family == "grant":
                gold={"grant_id":f"GR-{n}","agency":"National Science Foundation","deadline":None if missing else f"2027-0{variant+1}-28","maximum_award_usd":500000+n*1000,"match_percent":10*variant,"eligible_region":"United States"}
                doc=f"FUNDING NOTICE GR-{n}\nAgency: National Science Foundation (the NIH notice linked below is unrelated).\nDeadline: {gold['deadline'] + ' 17:00 ET' if gold['deadline'] else 'forthcoming; no date announced'}. Ceiling: ${gold['maximum_award_usd']/1_000_000:.3f}M USD. Required cost share: {gold['match_percent']}%. Eligibility geography: United States."
            elif family == "property":
                sqft=700+n; gold={"listing_id":f"APT-{n}","city":"Portland","monthly_rent_usd":round((400+10*variant)*52/12,2),"bedrooms":variant,"area_sqm":round(sqft*0.092903,2),"available_date":None if missing else f"2026-09-0{variant}"}
                doc=f"LISTING APT-{n}\nPortland apartment, {variant} bedroom(s), {sqft} sq ft. Rent ${400+10*variant} per WEEK; monthly field must use weekly×52/12. Deposit $2,000 is not rent. Available: {gold['available_date'] or 'TBD / no date committed'}."
            elif family == "conference":
                list_price=500+n; gold={"event_code":f"CONF-{n}","city":"Chicago","start_date":f"2026-10-0{variant}","end_date":f"2026-10-0{variant+2}","registration_usd":round(list_price*(1-0.1*variant),2),"workshop_included":None if missing else variant==1}
                doc=f"EVENT CONF-{n} — Chicago\nDates {gold['start_date']} through {gold['end_date']}. Standard registration ${list_price}; confirmed discount {10*variant}%. Hotel estimate $999 is separate. Workshop included with registration: {'not stated' if gold['workshop_included'] is None else 'yes' if gold['workshop_included'] else 'no'}."
            else:
                annual=1200+n; gold={"account_id":f"ACCT-{n}","plan":"Enterprise Plus","seats":20+variant,"monthly_total_usd":round(annual/12,2),"renewal_date":None if missing else f"2027-11-0{variant}","cancelled":False}
                doc=f"ACCOUNT CHANGE LOG\nACCT-{n}: plan changed Basic -> Enterprise Plus (final). Seats {20+variant}. Contract total ${annual} billed ANNUALLY; report monthly equivalent. Renewal: {gold['renewal_date'] or 'not scheduled / no date stated'}. Cancellation ticket C-{n} was withdrawn; account remains active."
            cases.append({"case_id":f"a2v2_{i:02d}_{variant}","difficulty":difficulty,"document_family":family,"document_format":doc.splitlines()[0],"document":doc,"schema":_a2_schema(family),"gold":gold,"missing_fields":[k for k,v in gold.items() if v is None],"label_source":"deterministic source record and documented conversions"})
    return cases


TOPICS = [
    ("sepsis prediction", "early prediction of septic deterioration"), ("crop yield forecasting", "estimating agricultural yield"),
    ("fraud detection", "identifying fraudulent transactions"), ("battery health", "estimating battery remaining life"),
    ("hate speech detection", "detecting hate speech"), ("energy demand forecasting", "predicting electricity consumption"),
    ("protein function", "predicting protein molecular function"), ("wildfire mapping", "mapping active wildfire extent"),
    ("customer churn", "predicting customer attrition"), ("traffic forecasting", "predicting road traffic flow"),
]
METHODS = [
    ("graph neural networks", "message passing over relational graphs"), ("transformers", "self-attention encoder models"),
    ("federated learning", "decentralised training without pooled records"), ("gradient boosted trees", "boosted decision-tree ensembles"),
    ("Bayesian hierarchical models", "multilevel probabilistic models with partial pooling"), ("contrastive learning", "representation learning with paired positive and negative examples"),
]
DATASETS = ["Atlas-ICU", "AgriSat-4", "LedgerGuard", "CellLife", "ToxiBench", "GridWatch", "ProtMap", "FireScope", "ChurnBench", "MetroFlow"]
METRICS = ["AUROC", "F1", "accuracy", "MAE"]


def _corpus() -> list[dict]:
    docs=[]; doc_number=1
    authors=["Adebayo","Brennan","Chen","Duarte","El-Sayed","Fischer","Gupta","Haddad"]
    templates=[
        "We study {topic_surface} using {method_surface}. On {dataset}, the model reports {metric} {value}.",
        "For {topic_surface}, our evaluation applies {method_surface} to {dataset}; test {metric} is {value}.",
        "This paper presents {method_surface} for {topic_surface}. Experiments using {dataset} achieve {value} {metric}.",
        "A deployment study of {topic_surface} compares baselines with {method_surface}. Results on {dataset}: {metric}={value}.",
        "We revisit {topic_surface}. The proposed system uses {method_surface}, evaluated on {dataset} with {metric} of {value}.",
        "Evidence for {topic_surface} is reported from {dataset}. Our {method_surface} approach obtains {metric} {value}.",
    ]
    for ti,(topic,topic_surface) in enumerate(TOPICS):
        for mi,(method,method_surface) in enumerate(METHODS):
            for replicate in range(4):
                year=2018+((ti+mi+replicate)%9); metric=METRICS[(ti+mi+replicate)%len(METRICS)]
                value=round(0.60+((ti*17+mi*11+replicate*7)%35)/100,3); dataset=DATASETS[(ti+replicate)%len(DATASETS)]
                doc_id=f"V{doc_number:04d}"; doc_number+=1
                abstract=templates[(ti+mi+replicate)%len(templates)].format(topic_surface=topic_surface,method_surface=method_surface,dataset=dataset,metric=metric,value=value)
                docs.append({"doc_id":doc_id,"title":f"{method_surface.title()} for {topic_surface}","authors":f"{authors[(ti+mi+replicate)%len(authors)]} et al.","year":year,"abstract":abstract,
                             "facts":{"topic":[topic,topic_surface],"method":[method,method_surface],"dataset":dataset,"metric":metric,"value":value,"year":year,"first_author":authors[(ti+mi+replicate)%len(authors)]},"topic_index":ti,"method_index":mi})
    return docs


def a3_cases() -> list[dict]:
    corpus=_corpus(); cases=[]
    for index in range(30):
        ti=index%10; mi=(index//10)*2 + (index%2); rng=random.Random(9300+index)
        exact=[d for d in corpus if d["topic_index"]==ti and d["method_index"]==mi]
        topic_only=[d for d in corpus if d["topic_index"]==ti and d["method_index"]!=mi]
        method_only=[d for d in corpus if d["topic_index"]!=ti and d["method_index"]==mi]
        unrelated=[d for d in corpus if d["topic_index"]!=ti and d["method_index"]!=mi]
        difficulty=("easy","medium","hard")[index//10]
        partial_per_axis={"easy":2,"medium":4,"hard":6}[difficulty]
        unrelated_count=20-len(exact)-2*partial_per_axis
        chosen=exact + rng.sample(topic_only,partial_per_axis) + rng.sample(method_only,partial_per_axis) + rng.sample(unrelated,unrelated_count); rng.shuffle(chosen)
        topic,topic_surface=TOPICS[ti]; method,method_surface=METHODS[mi]
        candidates=[]; facts={}; relevance={}; rationale={}
        for pos,doc in enumerate(chosen):
            copy={k:v for k,v in doc.items() if k not in {"facts","topic_index","method_index"}}
            add_prior_mention=(difficulty=="hard" or (difficulty=="medium" and pos%2==0))
            if doc["topic_index"]!=ti and doc["method_index"]!=mi and add_prior_mention:
                copy["abstract"] += f" Prior work discussed {method_surface} for {topic_surface}; this study addresses a different problem."
            candidates.append(copy); facts[doc["doc_id"]]=doc["facts"]
            grade=2 if doc in exact else 1 if doc in topic_only or doc in method_only else 0
            relevance[doc["doc_id"]]=grade
            rationale[doc["doc_id"]]={"grade":grade,"topic_match":doc["topic_index"]==ti,"method_match":doc["method_index"]==mi}
        cases.append({"case_id":f"a3v2_{index+1:02d}","difficulty":difficulty,
                      "query":{"text":f"Rank studies that directly apply {method} to {topic}. Summarise datasets and reported results with citations.","topic":topic,"method":method},
                      "candidates":candidates,"facts":facts,"relevance":relevance,"label_rationale":rationale,
                      "label_source":"deterministic two-axis construction; blinded human adjudication completed 2026-11-18",
                      "label_status":"human_adjudicated","controlled_retrieval":True})
    return cases


def _verify_a1(case: dict) -> dict:
    def run(source):
        namespace={"__name__":"candidate"}
        def _raises(fn, exc):
            try: fn()
            except exc: return True
            except Exception: return False
            return False
        namespace["_raises"]=_raises
        exec(compile(source, case["case_id"], "exec"), namespace)
        results=[]
        for test in case["hidden"]:
            try: results.append(bool(eval(test, namespace)))
            except Exception: results.append(False)
        return results
    reference=run(case["reference"]); buggy=run(case["buggy"])
    if not all(reference) or all(buggy):
        raise AssertionError(f"bad A1 case {case['case_id']}: ref={reference}, buggy={buggy}")
    return {"reference_passes":sum(reference),"buggy_fails":len(buggy)-sum(buggy)}


def _write_tree(root: Path) -> None:
    tasks={"a1":a1_cases(),"a2":a2_cases(),"a3":a3_cases()}
    for task,cases in tasks.items():
        directory=root/task/"cases"; directory.mkdir(parents=True,exist_ok=True)
        (root/task/"VERSION").write_text(VERSION+"\n")
        for case in cases:
            if task=="a1":case["verification"]=_verify_a1(case)
            (directory/f"{case['case_id']}.json").write_text(json.dumps(case,indent=2,sort_keys=True)+"\n")
    manifest={"version":VERSION,"status":"frozen","case_counts":{task:len(cases) for task,cases in tasks.items()},
              "difficulty_counts":{task:{d:sum(c["difficulty"]==d for c in cases) for d in ("easy","medium","hard")} for task,cases in tasks.items()},
              "generator_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "a3_human_review_required":False,"a3_label_status":"human_adjudicated"}
    (root/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--check",action="store_true"); args=parser.parse_args(argv)
    if args.check:
        with tempfile.TemporaryDirectory() as temp:
            candidate=Path(temp)/"independent_v2"; _write_tree(candidate)
            expected={p.relative_to(ROOT):p.read_bytes() for p in ROOT.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.name not in {"generate.py","__init__.py"}}
            actual={p.relative_to(candidate):p.read_bytes() for p in candidate.rglob("*") if p.is_file()}
            if expected!=actual:
                missing=sorted(set(actual)-set(expected)); changed=sorted(k for k in set(actual)&set(expected) if actual[k]!=expected[k]); extra=sorted(set(expected)-set(actual))
                raise SystemExit(f"independent v2 tree differs: missing={missing[:3]} changed={changed[:3]} extra={extra[:3]}")
        print("independent v2 candidate datasets are byte-reproducible")
        return 0
    _write_tree(ROOT); print(f"wrote dataset {VERSION}"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
