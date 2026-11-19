"""A2 information-extraction cases: gold record FIRST, then deterministic rendering to text.

Ground truth = the generating record (never a model). Each document contains distractors (a second
similar entity/number/date), at least one field that is genuinely missing (gold null), and one field whose
ambiguity is resolved by an explicit rule stated in the schema description.
"""

from __future__ import annotations

import random

SCHEMAS = {
    "purchase_order": {
        "po_number": "string: the purchase order number of THIS order (format PO-#####), not any referenced earlier order",
        "vendor_name": "string: the supplying company",
        "order_date": "date YYYY-MM-DD: the date the order was placed (not a delivery or quote date)",
        "total_usd": "number: final amount payable in USD AFTER any discount",
        "item_count": "integer: number of units ordered",
        "delivery_city": "string: city goods are delivered to",
        "payment_terms_days": "integer: payment due within N days; null if not stated",
    },
    "job_posting": {
        "job_title": "string",
        "company": "string: the hiring company (not a client or partner mentioned)",
        "city": "string: work location city; null if fully remote with no city",
        "salary_min_usd": "number: lower bound of the ANNUAL base salary in USD; null if not stated",
        "salary_max_usd": "number: upper bound of the ANNUAL base salary in USD; null if not stated",
        "years_experience": "integer: minimum years of experience required",
        "application_deadline": "date YYYY-MM-DD; null if not stated",
    },
    "incident_report": {
        "incident_id": "string: format INC-####",
        "system": "string: the affected system (not systems merely mentioned as unaffected)",
        "start_time": "string HH:MM (24h): when the outage began",
        "duration_minutes": "integer: total outage duration in minutes",
        "users_affected": "integer: number of users affected; null if unknown",
        "severity": "string: one of SEV1, SEV2, SEV3 as finally assigned (after any re-classification)",
        "root_cause": "string: short root cause phrase; null if still under investigation",
    },
    "clinical_trial": {
        "trial_id": "string: format CT-#####",
        "drug_name": "string: the investigational drug (not the comparator)",
        "phase": "integer: trial phase 1-4",
        "enrolled_patients": "integer: patients actually enrolled (not the planned target)",
        "primary_endpoint": "string",
        "sponsor": "string",
        "completion_year": "integer; null if not stated",
    },
    "rental_listing": {
        "listing_id": "string: format RL-####",
        "city": "string",
        "monthly_rent_usd": "number: rent per month in USD (convert if given per week as 52/12 x weekly)",
        "bedrooms": "integer",
        "deposit_usd": "number; null if not stated",
        "available_from": "date YYYY-MM-DD",
        "pets_allowed": "boolean; null if not stated",
    },
}

CITIES = ["Denver", "Austin", "Portland", "Raleigh", "Madison", "Tucson", "Boise", "Omaha"]
COMPANIES = ["Northwind Labs", "Bluepeak Systems", "Corvid Analytics", "Halden & Rowe", "Tessellate Inc", "Quarry Bio"]


def _date(rng, year=2026):
    return f"{year}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"


def _long_date(iso):
    y, m, d = iso.split("-")
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
              "October", "November", "December"]
    return f"{months[int(m) - 1]} {int(d)}, {y}"


def make_purchase_order(rng, missing):
    gold = {"po_number": f"PO-{rng.randint(10000, 99999)}", "vendor_name": rng.choice(COMPANIES),
            "order_date": _date(rng), "item_count": rng.randint(10, 400), "delivery_city": rng.choice(CITIES),
            "payment_terms_days": rng.choice([15, 30, 45])}
    list_price = round(gold["item_count"] * rng.uniform(5, 40), 2)
    discount = round(list_price * 0.1, 2)
    gold["total_usd"] = round(list_price - discount, 2)
    old_po = f"PO-{rng.randint(10000, 99999)}"
    quote_date = _date(rng)
    for f in missing:
        gold[f] = None
    lines = [f"Following up on our earlier order {old_po}, please find the new order details below.",
             f"This purchase order, {gold['po_number']}, was placed with {gold['vendor_name']} on "
             f"{_long_date(gold['order_date'])} (the vendor quote itself was dated {_long_date(quote_date)}).",
             f"We are ordering {gold['item_count']} units; list price ${list_price:,.2f} less a 10% volume discount of "
             f"${discount:,.2f}."]
    if gold["delivery_city"] is not None:
        lines.append(f"Ship to our warehouse in {gold['delivery_city']}; invoices go to head office in "
                     f"{rng.choice([c for c in CITIES if c != gold['delivery_city']])}.")
    if gold["payment_terms_days"] is not None:
        lines.append(f"Payment is due within {gold['payment_terms_days']} days of invoice.")
    return gold, " ".join(lines)


def make_job_posting(rng, missing):
    title = rng.choice(["Data Engineer", "Product Analyst", "Site Reliability Engineer", "ML Engineer"])
    smin = rng.choice([90000, 105000, 120000]); smax = smin + rng.choice([20000, 30000])
    gold = {"job_title": title, "company": rng.choice(COMPANIES), "city": rng.choice(CITIES),
            "salary_min_usd": smin, "salary_max_usd": smax, "years_experience": rng.randint(2, 7),
            "application_deadline": _date(rng)}
    for f in missing:
        gold[f] = None
    client = rng.choice([c for c in COMPANIES if c != gold["company"]])
    lines = [f"{gold['company']} is hiring a {title} to support projects for clients such as {client}."]
    lines.append(f"The role is based in {gold['city']} (hybrid)." if gold["city"] else "The role is fully remote.")
    if gold["salary_min_usd"] is not None:
        lines.append(f"Base pay is ${smin // 1000}k-${smax // 1000}k per year, plus a signing bonus of $5,000.")
    lines.append(f"You need at least {gold['years_experience']} years of experience; "
                 f"{gold['years_experience'] + 2}+ years is preferred.")
    if gold["application_deadline"]:
        lines.append(f"Apply by {_long_date(gold['application_deadline'])}.")
    return gold, " ".join(lines)


def make_incident_report(rng, missing):
    systems = ["payments API", "search cluster", "auth service", "billing database", "CDN edge"]
    sys_ = rng.choice(systems); other = rng.choice([s for s in systems if s != sys_])
    h, m = rng.randint(0, 22), rng.choice([0, 15, 30, 45]); dur = rng.choice([25, 40, 75, 130])
    gold = {"incident_id": f"INC-{rng.randint(1000, 9999)}", "system": sys_, "start_time": f"{h:02d}:{m:02d}",
            "duration_minutes": dur, "users_affected": rng.randint(200, 50000), "severity": "SEV1",
            "root_cause": rng.choice(["expired TLS certificate", "bad config rollout", "disk exhaustion"])}
    for f in missing:
        gold[f] = None
    lines = [f"Incident {gold['incident_id']}: the {sys_} was unavailable starting at {gold['start_time']} UTC; "
             f"the {other} remained healthy throughout.",
             f"Service was restored after {dur // 60} hours and {dur % 60} minutes." if dur >= 60 else
             f"Service was restored after {dur} minutes.",
             "Initially filed as SEV2, it was re-classified to SEV1 during the review."]
    if gold["users_affected"] is not None:
        lines.append(f"Approximately {gold['users_affected']:,} users were affected.")
    lines.append(f"Root cause: {gold['root_cause']}." if gold["root_cause"] else "Root cause is still under investigation.")
    return gold, " ".join(lines)


def make_clinical_trial(rng, missing):
    drug = rng.choice(["veltoramab", "cizolinib", "parsatide", "ombrexin"]); comp = "placebo-matched standard care"
    target = rng.choice([300, 400, 500]); enrolled = target - rng.randint(5, 60)
    gold = {"trial_id": f"CT-{rng.randint(10000, 99999)}", "drug_name": drug, "phase": rng.choice([2, 3]),
            "enrolled_patients": enrolled, "primary_endpoint": rng.choice(["progression-free survival", "HbA1c reduction",
                                                                          "time to first relapse"]),
            "sponsor": rng.choice(COMPANIES), "completion_year": rng.choice([2027, 2028])}
    for f in missing:
        gold[f] = None
    lines = [f"Trial {gold['trial_id']} is a Phase {gold['phase']} study of {drug} versus {comp}, sponsored by {gold['sponsor']}.",
             f"The planned enrolment target was {target} patients; {enrolled} patients were ultimately enrolled.",
             f"The primary endpoint is {gold['primary_endpoint']}; secondary endpoints include quality of life."]
    if gold["completion_year"]:
        lines.append(f"Completion is expected in {gold['completion_year']}, with interim results in {gold['completion_year'] - 1}.")
    return gold, " ".join(lines)


def make_rental_listing(rng, missing):
    weekly = rng.choice([450, 520, 600])
    gold = {"listing_id": f"RL-{rng.randint(1000, 9999)}", "city": rng.choice(CITIES),
            "monthly_rent_usd": round(weekly * 52 / 12, 2), "bedrooms": rng.randint(1, 4),
            "deposit_usd": rng.choice([1000, 1500, 2000]), "available_from": _date(rng), "pets_allowed": rng.choice([True, False])}
    for f in missing:
        gold[f] = None
    lines = [f"Listing {gold['listing_id']}: a {gold['bedrooms']}-bedroom flat in {gold['city']}, "
             f"${weekly} per week (a similar unit next door rents for ${weekly + 80} per week).",
             f"Available from {_long_date(gold['available_from'])}."]
    if gold["deposit_usd"] is not None:
        lines.append(f"A deposit of ${gold['deposit_usd']:,} is required.")
    if gold["pets_allowed"] is not None:
        lines.append("Pets are welcome." if gold["pets_allowed"] else "No pets, please.")
    return gold, " ".join(lines)


MAKERS = {"purchase_order": make_purchase_order, "job_posting": make_job_posting,
          "incident_report": make_incident_report, "clinical_trial": make_clinical_trial,
          "rental_listing": make_rental_listing}
# Fields that may be omitted (genuinely missing) per type; one chosen per case.
OPTIONAL = {"purchase_order": ["payment_terms_days", "delivery_city"],
            "job_posting": ["salary_min_usd", "application_deadline", "city"],
            "incident_report": ["users_affected", "root_cause"],
            "clinical_trial": ["completion_year"],
            "rental_listing": ["deposit_usd", "pets_allowed"]}


def build_cases(seed: int = 20261118) -> list[dict]:
    rng = random.Random(seed)
    cases = []
    for i, t in enumerate(sorted(MAKERS) * 2):
        miss = [rng.choice(OPTIONAL[t])]
        if t == "job_posting" and "salary_min_usd" in miss:
            miss.append("salary_max_usd")
        gold, text = MAKERS[t](rng, miss)
        cases.append({"case_id": f"a2_{i + 1:02d}_{t}", "doc_type": t, "document": text,
                      "schema": SCHEMAS[t], "gold": gold, "missing_fields": sorted(miss)})
    return cases
