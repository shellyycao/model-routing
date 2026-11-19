# Workflow cost analysis — post-hoc / exploratory

## Key findings

- Across 156 saved runs, executed spend was $7.6923; every run had complete recorded usage (**not single-run evidence overall**).
- Frozen v3 found 28/156 feasible runs (17.9%); post-hoc v3.1 found 38/156 (24.4%). Spend is identical; only feasibility denominators change.
- Cost per feasible completion was $0.2747 under v3 and $0.2024 under v3.1 (pooled exploratory evidence).
- The cost-first token-conversion view was estimable for 8/20 frozen traces and changed 1/20 selections; it is not a prospective dollar prediction.
- Cost-counterfactual direction matched in 29/32 estimable pairs; a token-agnostic unit-price baseline matched 30/32 on the same pairs, so cost direction is largely price-ordered.

## Scope and provenance

This offline analysis prices the saved Experiment B v3 calls with the verified A/B/C prices in `configs/models.yaml`. Frozen v3 feasibility is primary; existing post-hoc v3.1 labels are secondary. `retail_sales` is pilot-exposed, so the pooled view contains one pilot-exposed project. No Router trace, prediction, validation, or raw record was changed.

## Integrity and cost reconciliation

Audit: **PASS**. 156 unique workflow records map to 339 primary API calls and 17 non-billable parse children. Ledger calls and tokens reconcile exactly. Missing-usage calls: 0; failed attempts: 0.

## Project-level path costs

`single-run evidence` means the project/path cell has n=1. Cost is unchanged across validator views.

| Project | Path | Evidence | Spend | Mean/run | v3 feasible | v3 cost/feasible | v3.1 feasible | v3.1 cost/feasible |
|---|---|---|---:|---:|---:|---:|---:|---:|
| customer_churn | A-A-A | repeated evidence (n=3) | $0.4620 | $0.1540 | 0/3 | not estimable | 3/3 | $0.1540 |
| customer_churn | A-A-B | single-run evidence (n=1) | $0.1212 | $0.1212 | 1/1 | $0.1212 | 1/1 | $0.1212 |
| customer_churn | A-A-C | repeated evidence (n=3) | $0.3159 | $0.1053 | 1/3 | $0.3159 | 3/3 | $0.1053 |
| customer_churn | A-B-A | single-run evidence (n=1) | $0.0680 | $0.0680 | 0/1 | not estimable | 0/1 | not estimable |
| customer_churn | A-B-B | single-run evidence (n=1) | $0.0679 | $0.0679 | 0/1 | not estimable | 0/1 | not estimable |
| customer_churn | A-B-C | single-run evidence (n=1) | $0.0742 | $0.0742 | 0/1 | not estimable | 0/1 | not estimable |
| customer_churn | A-C-A | repeated evidence (n=3) | $0.3350 | $0.1117 | 0/3 | not estimable | 2/3 | $0.1675 |
| customer_churn | A-C-B | single-run evidence (n=1) | $0.0746 | $0.0746 | 1/1 | $0.0746 | 1/1 | $0.0746 |
| customer_churn | A-C-C | repeated evidence (n=3) | $0.2033 | $0.0678 | 1/3 | $0.2033 | 3/3 | $0.0678 |
| customer_churn | B-A-A | single-run evidence (n=1) | $0.0070 | $0.0070 | 0/1 | not estimable | 0/1 | not estimable |
| customer_churn | B-A-B | single-run evidence (n=1) | $0.0073 | $0.0073 | 0/1 | not estimable | 0/1 | not estimable |
| customer_churn | B-A-C | single-run evidence (n=1) | $0.0072 | $0.0072 | 0/1 | not estimable | 0/1 | not estimable |
| customer_churn | B-B-A | single-run evidence (n=1) | $0.0073 | $0.0073 | 0/1 | not estimable | 0/1 | not estimable |
| customer_churn | B-B-B | repeated evidence (n=3) | $0.0234 | $0.0078 | 0/3 | not estimable | 0/3 | not estimable |
| customer_churn | B-B-C | single-run evidence (n=1) | $0.0071 | $0.0071 | 0/1 | not estimable | 0/1 | not estimable |
| customer_churn | B-C-A | single-run evidence (n=1) | $0.0080 | $0.0080 | 0/1 | not estimable | 0/1 | not estimable |
| customer_churn | B-C-B | single-run evidence (n=1) | $0.0078 | $0.0078 | 0/1 | not estimable | 0/1 | not estimable |
| customer_churn | B-C-C | single-run evidence (n=1) | $0.0076 | $0.0076 | 0/1 | not estimable | 0/1 | not estimable |
| customer_churn | C-A-A | single-run evidence (n=1) | $0.0926 | $0.0926 | 0/1 | not estimable | 1/1 | $0.0926 |
| customer_churn | C-A-B | single-run evidence (n=1) | $0.0564 | $0.0564 | 0/1 | not estimable | 0/1 | not estimable |
| customer_churn | C-A-C | single-run evidence (n=1) | $0.0028 | $0.0028 | 0/1 | not estimable | 0/1 | not estimable |
| customer_churn | C-B-A | single-run evidence (n=1) | $0.0098 | $0.0098 | 0/1 | not estimable | 0/1 | not estimable |
| customer_churn | C-B-B | single-run evidence (n=1) | $0.0102 | $0.0102 | 0/1 | not estimable | 0/1 | not estimable |
| customer_churn | C-B-C | single-run evidence (n=1) | $0.0026 | $0.0026 | 0/1 | not estimable | 0/1 | not estimable |
| customer_churn | C-C-A | single-run evidence (n=1) | $0.0513 | $0.0513 | 0/1 | not estimable | 0/1 | not estimable |
| customer_churn | C-C-B | single-run evidence (n=1) | $0.0131 | $0.0131 | 1/1 | $0.0131 | 1/1 | $0.0131 |
| customer_churn | C-C-C | repeated evidence (n=3) | $0.0204 | $0.0068 | 0/3 | not estimable | 0/3 | not estimable |
| energy_consumption | A-A-A | repeated evidence (n=3) | $0.4441 | $0.1480 | 0/3 | not estimable | 0/3 | not estimable |
| energy_consumption | A-A-B | single-run evidence (n=1) | $0.1074 | $0.1074 | 0/1 | not estimable | 0/1 | not estimable |
| energy_consumption | A-A-C | repeated evidence (n=3) | $0.3055 | $0.1018 | 3/3 | $0.1018 | 3/3 | $0.1018 |
| energy_consumption | A-B-A | single-run evidence (n=1) | $0.0622 | $0.0622 | 0/1 | not estimable | 0/1 | not estimable |
| energy_consumption | A-B-B | single-run evidence (n=1) | $0.0629 | $0.0629 | 0/1 | not estimable | 0/1 | not estimable |
| energy_consumption | A-B-C | single-run evidence (n=1) | $0.0629 | $0.0629 | 0/1 | not estimable | 0/1 | not estimable |
| energy_consumption | A-C-A | repeated evidence (n=3) | $0.2597 | $0.0866 | 2/3 | $0.1299 | 2/3 | $0.1299 |
| energy_consumption | A-C-B | single-run evidence (n=1) | $0.0667 | $0.0667 | 1/1 | $0.0667 | 1/1 | $0.0667 |
| energy_consumption | A-C-C | repeated evidence (n=3) | $0.1752 | $0.0584 | 2/3 | $0.0876 | 2/3 | $0.0876 |
| energy_consumption | B-A-A | single-run evidence (n=1) | $0.0074 | $0.0074 | 0/1 | not estimable | 0/1 | not estimable |
| energy_consumption | B-A-B | single-run evidence (n=1) | $0.0081 | $0.0081 | 0/1 | not estimable | 0/1 | not estimable |
| energy_consumption | B-A-C | single-run evidence (n=1) | $0.0070 | $0.0070 | 0/1 | not estimable | 0/1 | not estimable |
| energy_consumption | B-B-A | single-run evidence (n=1) | $0.0070 | $0.0070 | 0/1 | not estimable | 0/1 | not estimable |
| energy_consumption | B-B-B | repeated evidence (n=3) | $0.0225 | $0.0075 | 0/3 | not estimable | 0/3 | not estimable |
| energy_consumption | B-B-C | single-run evidence (n=1) | $0.0070 | $0.0070 | 0/1 | not estimable | 0/1 | not estimable |
| energy_consumption | B-C-A | single-run evidence (n=1) | $0.0078 | $0.0078 | 0/1 | not estimable | 0/1 | not estimable |
| energy_consumption | B-C-B | single-run evidence (n=1) | $0.0073 | $0.0073 | 0/1 | not estimable | 0/1 | not estimable |
| energy_consumption | B-C-C | single-run evidence (n=1) | $0.0076 | $0.0076 | 0/1 | not estimable | 0/1 | not estimable |
| energy_consumption | C-A-A | single-run evidence (n=1) | $0.0933 | $0.0933 | 0/1 | not estimable | 0/1 | not estimable |
| energy_consumption | C-A-B | single-run evidence (n=1) | $0.0025 | $0.0025 | 0/1 | not estimable | 0/1 | not estimable |
| energy_consumption | C-A-C | single-run evidence (n=1) | $0.0021 | $0.0021 | 0/1 | not estimable | 0/1 | not estimable |
| energy_consumption | C-B-A | single-run evidence (n=1) | $0.0027 | $0.0027 | 0/1 | not estimable | 0/1 | not estimable |
| energy_consumption | C-B-B | single-run evidence (n=1) | $0.0089 | $0.0089 | 0/1 | not estimable | 0/1 | not estimable |
| energy_consumption | C-B-C | single-run evidence (n=1) | $0.0091 | $0.0091 | 0/1 | not estimable | 0/1 | not estimable |
| energy_consumption | C-C-A | single-run evidence (n=1) | $0.0512 | $0.0512 | 0/1 | not estimable | 0/1 | not estimable |
| energy_consumption | C-C-B | single-run evidence (n=1) | $0.0133 | $0.0133 | 1/1 | $0.0133 | 1/1 | $0.0133 |
| energy_consumption | C-C-C | repeated evidence (n=3) | $0.0073 | $0.0024 | 0/3 | not estimable | 0/3 | not estimable |
| retail_sales | A-A-A | repeated evidence (n=3) | $0.4004 | $0.1335 | 3/3 | $0.1335 | 3/3 | $0.1335 |
| retail_sales | A-A-B | single-run evidence (n=1) | $0.0992 | $0.0992 | 0/1 | not estimable | 0/1 | not estimable |
| retail_sales | A-A-C | repeated evidence (n=3) | $0.2804 | $0.0935 | 1/3 | $0.2804 | 1/3 | $0.2804 |
| retail_sales | A-B-A | single-run evidence (n=1) | $0.1003 | $0.1003 | 1/1 | $0.1003 | 1/1 | $0.1003 |
| retail_sales | A-B-B | single-run evidence (n=1) | $0.0654 | $0.0654 | 0/1 | not estimable | 0/1 | not estimable |
| retail_sales | A-B-C | single-run evidence (n=1) | $0.0606 | $0.0606 | 0/1 | not estimable | 0/1 | not estimable |
| retail_sales | A-C-A | repeated evidence (n=3) | $0.2894 | $0.0965 | 3/3 | $0.0965 | 3/3 | $0.0965 |
| retail_sales | A-C-B | single-run evidence (n=1) | $0.0599 | $0.0599 | 1/1 | $0.0599 | 1/1 | $0.0599 |
| retail_sales | A-C-C | repeated evidence (n=3) | $0.1678 | $0.0559 | 0/3 | not estimable | 0/3 | not estimable |
| retail_sales | B-A-A | single-run evidence (n=1) | $0.0076 | $0.0076 | 0/1 | not estimable | 0/1 | not estimable |
| retail_sales | B-A-B | single-run evidence (n=1) | $0.0076 | $0.0076 | 0/1 | not estimable | 0/1 | not estimable |
| retail_sales | B-A-C | single-run evidence (n=1) | $0.0078 | $0.0078 | 0/1 | not estimable | 0/1 | not estimable |
| retail_sales | B-B-A | single-run evidence (n=1) | $0.0083 | $0.0083 | 0/1 | not estimable | 0/1 | not estimable |
| retail_sales | B-B-B | repeated evidence (n=3) | $0.0215 | $0.0072 | 0/3 | not estimable | 0/3 | not estimable |
| retail_sales | B-B-C | single-run evidence (n=1) | $0.0074 | $0.0074 | 0/1 | not estimable | 0/1 | not estimable |
| retail_sales | B-C-A | single-run evidence (n=1) | $0.0068 | $0.0068 | 0/1 | not estimable | 0/1 | not estimable |
| retail_sales | B-C-B | single-run evidence (n=1) | $0.0078 | $0.0078 | 0/1 | not estimable | 0/1 | not estimable |
| retail_sales | B-C-C | single-run evidence (n=1) | $0.0079 | $0.0079 | 0/1 | not estimable | 0/1 | not estimable |
| retail_sales | C-A-A | single-run evidence (n=1) | $0.0848 | $0.0848 | 0/1 | not estimable | 0/1 | not estimable |
| retail_sales | C-A-B | single-run evidence (n=1) | $0.0497 | $0.0497 | 0/1 | not estimable | 0/1 | not estimable |
| retail_sales | C-A-C | single-run evidence (n=1) | $0.0458 | $0.0458 | 0/1 | not estimable | 0/1 | not estimable |
| retail_sales | C-B-A | single-run evidence (n=1) | $0.0515 | $0.0515 | 0/1 | not estimable | 0/1 | not estimable |
| retail_sales | C-B-B | single-run evidence (n=1) | $0.0166 | $0.0166 | 1/1 | $0.0166 | 1/1 | $0.0166 |
| retail_sales | C-B-C | single-run evidence (n=1) | $0.0115 | $0.0115 | 0/1 | not estimable | 0/1 | not estimable |
| retail_sales | C-C-A | single-run evidence (n=1) | $0.0445 | $0.0445 | 1/1 | $0.0445 | 1/1 | $0.0445 |
| retail_sales | C-C-B | single-run evidence (n=1) | $0.0123 | $0.0123 | 1/1 | $0.0123 | 1/1 | $0.0123 |
| retail_sales | C-C-C | repeated evidence (n=3) | $0.0114 | $0.0038 | 0/3 | not estimable | 0/3 | not estimable |
| support_operations | A-A-A | repeated evidence (n=3) | $0.4262 | $0.1421 | 1/3 | $0.4262 | 1/3 | $0.4262 |
| support_operations | A-A-B | single-run evidence (n=1) | $0.1069 | $0.1069 | 0/1 | not estimable | 0/1 | not estimable |
| support_operations | A-A-C | repeated evidence (n=3) | $0.3139 | $0.1046 | 0/3 | not estimable | 0/3 | not estimable |
| support_operations | A-B-A | single-run evidence (n=1) | $0.0650 | $0.0650 | 0/1 | not estimable | 0/1 | not estimable |
| support_operations | A-B-B | single-run evidence (n=1) | $0.0617 | $0.0617 | 0/1 | not estimable | 0/1 | not estimable |
| support_operations | A-B-C | single-run evidence (n=1) | $0.0675 | $0.0675 | 0/1 | not estimable | 0/1 | not estimable |
| support_operations | A-C-A | repeated evidence (n=3) | $0.2643 | $0.0881 | 0/3 | not estimable | 0/3 | not estimable |
| support_operations | A-C-B | single-run evidence (n=1) | $0.0698 | $0.0698 | 0/1 | not estimable | 0/1 | not estimable |
| support_operations | A-C-C | repeated evidence (n=3) | $0.1856 | $0.0619 | 0/3 | not estimable | 0/3 | not estimable |
| support_operations | B-A-A | single-run evidence (n=1) | $0.0073 | $0.0073 | 0/1 | not estimable | 0/1 | not estimable |
| support_operations | B-A-B | single-run evidence (n=1) | $0.0528 | $0.0528 | 1/1 | $0.0528 | 1/1 | $0.0528 |
| support_operations | B-A-C | single-run evidence (n=1) | $0.0510 | $0.0510 | 0/1 | not estimable | 0/1 | not estimable |
| support_operations | B-B-A | single-run evidence (n=1) | $0.0066 | $0.0066 | 0/1 | not estimable | 0/1 | not estimable |
| support_operations | B-B-B | repeated evidence (n=3) | $0.0232 | $0.0077 | 0/3 | not estimable | 0/3 | not estimable |
| support_operations | B-B-C | single-run evidence (n=1) | $0.0075 | $0.0075 | 0/1 | not estimable | 0/1 | not estimable |
| support_operations | B-C-A | single-run evidence (n=1) | $0.0076 | $0.0076 | 0/1 | not estimable | 0/1 | not estimable |
| support_operations | B-C-B | single-run evidence (n=1) | $0.0070 | $0.0070 | 0/1 | not estimable | 0/1 | not estimable |
| support_operations | B-C-C | single-run evidence (n=1) | $0.0081 | $0.0081 | 0/1 | not estimable | 0/1 | not estimable |
| support_operations | C-A-A | single-run evidence (n=1) | $0.0027 | $0.0027 | 0/1 | not estimable | 0/1 | not estimable |
| support_operations | C-A-B | single-run evidence (n=1) | $0.0474 | $0.0474 | 0/1 | not estimable | 0/1 | not estimable |
| support_operations | C-A-C | single-run evidence (n=1) | $0.0466 | $0.0466 | 0/1 | not estimable | 0/1 | not estimable |
| support_operations | C-B-A | single-run evidence (n=1) | $0.0081 | $0.0081 | 0/1 | not estimable | 0/1 | not estimable |
| support_operations | C-B-B | single-run evidence (n=1) | $0.0081 | $0.0081 | 0/1 | not estimable | 0/1 | not estimable |
| support_operations | C-B-C | single-run evidence (n=1) | $0.0086 | $0.0086 | 0/1 | not estimable | 0/1 | not estimable |
| support_operations | C-C-A | single-run evidence (n=1) | $0.0023 | $0.0023 | 0/1 | not estimable | 0/1 | not estimable |
| support_operations | C-C-B | single-run evidence (n=1) | $0.0027 | $0.0027 | 0/1 | not estimable | 0/1 | not estimable |
| support_operations | C-C-C | repeated evidence (n=3) | $0.0170 | $0.0057 | 0/3 | not estimable | 0/3 | not estimable |

## Pooled path costs

This is a **pooled post-hoc view**, not an equal-weighted project comparison. It includes pilot-exposed `retail_sales`.

| Path | Evidence | Spend | Mean/run | v3 feasible | v3 cost/feasible | v3.1 feasible | v3.1 cost/feasible |
|---|---|---:|---:|---:|---:|---:|---:|
| A-A-A | repeated evidence (n=12) | $1.7328 | $0.1444 | 4/12 | $0.4332 | 7/12 | $0.2475 |
| A-A-B | repeated evidence (n=4) | $0.4347 | $0.1087 | 1/4 | $0.4347 | 1/4 | $0.4347 |
| A-A-C | repeated evidence (n=12) | $1.2157 | $0.1013 | 5/12 | $0.2431 | 7/12 | $0.1737 |
| A-B-A | repeated evidence (n=4) | $0.2956 | $0.0739 | 1/4 | $0.2956 | 1/4 | $0.2956 |
| A-B-B | repeated evidence (n=4) | $0.2579 | $0.0645 | 0/4 | not estimable | 0/4 | not estimable |
| A-B-C | repeated evidence (n=4) | $0.2652 | $0.0663 | 0/4 | not estimable | 0/4 | not estimable |
| A-C-A | repeated evidence (n=12) | $1.1485 | $0.0957 | 5/12 | $0.2297 | 7/12 | $0.1641 |
| A-C-B | repeated evidence (n=4) | $0.2709 | $0.0677 | 3/4 | $0.0903 | 3/4 | $0.0903 |
| A-C-C | repeated evidence (n=12) | $0.7319 | $0.0610 | 3/12 | $0.2440 | 5/12 | $0.1464 |
| B-A-A | repeated evidence (n=4) | $0.0293 | $0.0073 | 0/4 | not estimable | 0/4 | not estimable |
| B-A-B | repeated evidence (n=4) | $0.0758 | $0.0189 | 1/4 | $0.0758 | 1/4 | $0.0758 |
| B-A-C | repeated evidence (n=4) | $0.0730 | $0.0182 | 0/4 | not estimable | 0/4 | not estimable |
| B-B-A | repeated evidence (n=4) | $0.0291 | $0.0073 | 0/4 | not estimable | 0/4 | not estimable |
| B-B-B | repeated evidence (n=12) | $0.0905 | $0.0075 | 0/12 | not estimable | 0/12 | not estimable |
| B-B-C | repeated evidence (n=4) | $0.0290 | $0.0072 | 0/4 | not estimable | 0/4 | not estimable |
| B-C-A | repeated evidence (n=4) | $0.0302 | $0.0075 | 0/4 | not estimable | 0/4 | not estimable |
| B-C-B | repeated evidence (n=4) | $0.0299 | $0.0075 | 0/4 | not estimable | 0/4 | not estimable |
| B-C-C | repeated evidence (n=4) | $0.0312 | $0.0078 | 0/4 | not estimable | 0/4 | not estimable |
| C-A-A | repeated evidence (n=4) | $0.2734 | $0.0684 | 0/4 | not estimable | 1/4 | $0.2734 |
| C-A-B | repeated evidence (n=4) | $0.1560 | $0.0390 | 0/4 | not estimable | 0/4 | not estimable |
| C-A-C | repeated evidence (n=4) | $0.0972 | $0.0243 | 0/4 | not estimable | 0/4 | not estimable |
| C-B-A | repeated evidence (n=4) | $0.0721 | $0.0180 | 0/4 | not estimable | 0/4 | not estimable |
| C-B-B | repeated evidence (n=4) | $0.0437 | $0.0109 | 1/4 | $0.0437 | 1/4 | $0.0437 |
| C-B-C | repeated evidence (n=4) | $0.0317 | $0.0079 | 0/4 | not estimable | 0/4 | not estimable |
| C-C-A | repeated evidence (n=4) | $0.1492 | $0.0373 | 1/4 | $0.1492 | 1/4 | $0.1492 |
| C-C-B | repeated evidence (n=4) | $0.0415 | $0.0104 | 3/4 | $0.0138 | 3/4 | $0.0138 |
| C-C-C | repeated evidence (n=12) | $0.0561 | $0.0047 | 0/12 | not estimable | 0/12 | not estimable |

## Quality–cost Pareto frontiers

Axes are mean executed cost per saved run (lower) and feasibility among non-void runs (higher). Frontiers retain ties and are listed separately by validator.

- **customer_churn, frozen_v3:** C-B-C ($0.0026, 0/1, single-run evidence), C-C-B ($0.0131, 1/1, single-run evidence)
- **customer_churn, posthoc_v31:** C-B-C ($0.0026, 0/1, single-run evidence), C-C-B ($0.0131, 1/1, single-run evidence)
- **energy_consumption, frozen_v3:** C-A-C ($0.0021, 0/1, single-run evidence), C-C-B ($0.0133, 1/1, single-run evidence)
- **energy_consumption, posthoc_v31:** C-A-C ($0.0021, 0/1, single-run evidence), C-C-B ($0.0133, 1/1, single-run evidence)
- **retail_sales, frozen_v3:** C-C-C ($0.0038, 0/3, repeated evidence), C-C-B ($0.0123, 1/1, single-run evidence)
- **retail_sales, posthoc_v31:** C-C-C ($0.0038, 0/3, repeated evidence), C-C-B ($0.0123, 1/1, single-run evidence)
- **support_operations, frozen_v3:** C-C-A ($0.0023, 0/1, single-run evidence), B-A-B ($0.0528, 1/1, single-run evidence)
- **support_operations, posthoc_v31:** C-C-A ($0.0023, 0/1, single-run evidence), B-A-B ($0.0528, 1/1, single-run evidence)
- **Pooled post-hoc, frozen_v3:** C-C-C ($0.0047, 0/12, n=12), C-C-B ($0.0104, 3/4, n=4)
- **Pooled post-hoc, posthoc_v31:** C-C-C ($0.0047, 0/12, n=12), C-C-B ($0.0104, 3/4, n=4)

## Router cost-first sensitivity

This is a **post-hoc conversion of the Router's token predictions**. The frozen Router never predicted dollars. Candidate estimates, evidence, constraints, and traces remain frozen.

The previously reported sensitivity views remain alongside this addition: `frozen_v3`, `feasibility_only`, `strict_quality`, `token_first`, and `maximum_reliability`.

| Trace | Strategy | Project | Frozen selection | Cost-first conversion | Comparable/eligible | Changed |
|---|---|---|---|---|---:|---:|
| S1_single_model:customer_churn:default_v1:632cdd3c12a0:A-A-A | S1_single_model | customer_churn | A-A-A | A-A-A | 1/1 | no |
| S1_single_model:customer_churn:default_v1:11ac6ab4c248:B-B-B | S1_single_model | customer_churn | none | not estimable | 0/0 | no |
| S1_single_model:customer_churn:default_v1:425cb9e0e018:C-C-C | S1_single_model | customer_churn | none | not estimable | 0/0 | no |
| S2_greedy_task_only:customer_churn:default_v1:bc2f278d27af | S2_greedy_task_only | customer_churn | A-C-A | C-C-A | 4/4 | yes |
| S3_workflow_aware:customer_churn:default_v1:d360c862f7bc | S3_workflow_aware | customer_churn | A-C-B | A-C-B | 2/2 | no |
| S1_single_model:energy_consumption:default_v1:be7fc7642f39:A-A-A | S1_single_model | energy_consumption | none | not estimable | 0/0 | no |
| S1_single_model:energy_consumption:default_v1:2c3ae27618dc:B-B-B | S1_single_model | energy_consumption | none | not estimable | 0/0 | no |
| S1_single_model:energy_consumption:default_v1:3950886d3907:C-C-C | S1_single_model | energy_consumption | none | not estimable | 0/0 | no |
| S2_greedy_task_only:energy_consumption:default_v1:f9da8d2b7923 | S2_greedy_task_only | energy_consumption | none | not estimable | 0/0 | no |
| S3_workflow_aware:energy_consumption:default_v1:de5963898da0 | S3_workflow_aware | energy_consumption | A-C-B | A-C-B | 1/1 | no |
| S1_single_model:retail_sales:default_v1:c52844ac4e60:A-A-A | S1_single_model | retail_sales | none | not estimable | 0/0 | no |
| S1_single_model:retail_sales:default_v1:86b14b1ce3ed:B-B-B | S1_single_model | retail_sales | none | not estimable | 0/0 | no |
| S1_single_model:retail_sales:default_v1:be661918d410:C-C-C | S1_single_model | retail_sales | none | not estimable | 0/0 | no |
| S2_greedy_task_only:retail_sales:default_v1:cc35ac998cb2 | S2_greedy_task_only | retail_sales | none | not estimable | 0/0 | no |
| S3_workflow_aware:retail_sales:default_v1:38b5b168969e | S3_workflow_aware | retail_sales | C-C-B | C-C-B | 2/2 | no |
| S1_single_model:support_operations:default_v1:19904e3196d2:A-A-A | S1_single_model | support_operations | A-A-A | A-A-A | 1/1 | no |
| S1_single_model:support_operations:default_v1:1ee566b2ec31:B-B-B | S1_single_model | support_operations | none | not estimable | 0/0 | no |
| S1_single_model:support_operations:default_v1:856220dc76c6:C-C-C | S1_single_model | support_operations | none | not estimable | 0/0 | no |
| S2_greedy_task_only:support_operations:default_v1:3e7fc794e9d2 | S2_greedy_task_only | support_operations | A-C-A | A-C-A | 2/2 | no |
| S3_workflow_aware:support_operations:default_v1:7a94bb6aede2 | S3_workflow_aware | support_operations | C-C-B | C-C-B | 3/3 | no |

## Cost counterfactual: post-hoc conversion of token predictions

Predicted direction uses the post-hoc token conversion; executed direction uses recorded tokens × verified prices. This does not retroactively validate a prospective dollar forecast.

On the common estimable subset, token conversion matched 29/32 and the naive unit-price ordering baseline matched 30/32. Across all executed-cost pairs the naive baseline matched 42/50. By contrast, the frozen Router's feasibility direction matched only 22/50 (44.0%): feasibility, not cost ordering, was the difficult decision-relevant quantity.

| Strategy/project | Selected → alternative | Predicted Δ | Executed Δ | Runs selected/alternative | Direction match |
|---|---|---:|---:|---:|---:|
| S2_greedy_task_only / customer_churn | A-C-A → B-C-A | not estimable | $-0.1037 | 3/1 | not estimable |
| S2_greedy_task_only / customer_churn | A-C-A → C-C-A | $-0.0509 | $-0.0604 | 3/1 | yes |
| S2_greedy_task_only / customer_churn | A-C-A → A-A-A | $0.0364 | $0.0423 | 3/3 | yes |
| S2_greedy_task_only / customer_churn | A-C-A → A-B-A | not estimable | $-0.0437 | 3/1 | not estimable |
| S2_greedy_task_only / customer_churn | A-C-A → A-C-B | $-0.0350 | $-0.0371 | 3/1 | yes |
| S2_greedy_task_only / customer_churn | A-C-A → A-C-C | $-0.0395 | $-0.0439 | 3/3 | yes |
| S2_greedy_task_only / customer_churn | A-C-A → B-B-B | not estimable | $-0.1039 | 3/3 | not estimable |
| S2_greedy_task_only / customer_churn | A-C-A → C-C-C | $-0.0903 | $-0.1049 | 3/3 | yes |
| S3_workflow_aware / customer_churn | A-C-B → B-C-B | not estimable | $-0.0667 | 1/1 | not estimable |
| S3_workflow_aware / customer_churn | A-C-B → C-C-B | $-0.0509 | $-0.0614 | 1/1 | yes |
| S3_workflow_aware / customer_churn | A-C-B → A-A-B | $0.0364 | $0.0466 | 1/1 | yes |
| S3_workflow_aware / customer_churn | A-C-B → A-B-B | not estimable | $-0.0066 | 1/1 | not estimable |
| S3_workflow_aware / customer_churn | A-C-B → A-C-A | $0.0391 | $0.0371 | 1/3 | yes |
| S3_workflow_aware / customer_churn | A-C-B → A-C-C | $-0.0029 | $-0.0068 | 1/3 | no |
| S3_workflow_aware / customer_churn | A-C-B → A-A-A | $0.0738 | $0.0794 | 1/3 | yes |
| S3_workflow_aware / customer_churn | A-C-B → B-B-B | not estimable | $-0.0668 | 1/3 | not estimable |
| S3_workflow_aware / customer_churn | A-C-B → C-C-C | $-0.0553 | $-0.0678 | 1/3 | yes |
| S3_workflow_aware / energy_consumption | A-C-B → B-C-B | not estimable | $-0.0593 | 1/1 | not estimable |
| S3_workflow_aware / energy_consumption | A-C-B → C-C-B | $-0.0592 | $-0.0534 | 1/1 | yes |
| S3_workflow_aware / energy_consumption | A-C-B → A-A-B | $0.0353 | $0.0407 | 1/1 | yes |
| S3_workflow_aware / energy_consumption | A-C-B → A-B-B | not estimable | $-0.0037 | 1/1 | not estimable |
| S3_workflow_aware / energy_consumption | A-C-B → A-C-A | $0.0343 | $0.0199 | 1/3 | yes |
| S3_workflow_aware / energy_consumption | A-C-B → A-C-C | $-0.0074 | $-0.0083 | 1/3 | yes |
| S3_workflow_aware / energy_consumption | A-C-B → A-A-A | $0.0661 | $0.0814 | 1/3 | yes |
| S3_workflow_aware / energy_consumption | A-C-B → B-B-B | not estimable | $-0.0592 | 1/3 | not estimable |
| S3_workflow_aware / energy_consumption | A-C-B → C-C-C | $-0.0645 | $-0.0642 | 1/3 | yes |
| S3_workflow_aware / retail_sales | C-C-B → A-C-B | $0.0608 | $0.0475 | 1/1 | yes |
| S3_workflow_aware / retail_sales | C-C-B → B-C-B | not estimable | $-0.0045 | 1/1 | not estimable |
| S3_workflow_aware / retail_sales | C-C-B → C-A-B | $0.0348 | $0.0374 | 1/1 | yes |
| S3_workflow_aware / retail_sales | C-C-B → C-B-B | not estimable | $0.0042 | 1/1 | not estimable |
| S3_workflow_aware / retail_sales | C-C-B → C-C-A | $0.0340 | $0.0322 | 1/1 | yes |
| S3_workflow_aware / retail_sales | C-C-B → C-C-C | $-0.0054 | $-0.0085 | 1/3 | yes |
| S3_workflow_aware / retail_sales | C-C-B → A-A-A | $0.1274 | $0.1211 | 1/3 | yes |
| S3_workflow_aware / retail_sales | C-C-B → B-B-B | not estimable | $-0.0052 | 1/3 | not estimable |
| S2_greedy_task_only / support_operations | A-C-A → B-C-A | not estimable | $-0.0805 | 3/1 | not estimable |
| S2_greedy_task_only / support_operations | A-C-A → C-C-A | $-0.0559 | $-0.0858 | 3/1 | yes |
| S2_greedy_task_only / support_operations | A-C-A → A-A-A | $0.0368 | $0.0540 | 3/3 | yes |
| S2_greedy_task_only / support_operations | A-C-A → A-B-A | not estimable | $-0.0231 | 3/1 | not estimable |
| S2_greedy_task_only / support_operations | A-C-A → A-C-B | $-0.0345 | $-0.0183 | 3/1 | yes |
| S2_greedy_task_only / support_operations | A-C-A → A-C-C | $-0.0409 | $-0.0262 | 3/3 | yes |
| S2_greedy_task_only / support_operations | A-C-A → B-B-B | not estimable | $-0.0804 | 3/3 | not estimable |
| S2_greedy_task_only / support_operations | A-C-A → C-C-C | $-0.0967 | $-0.0824 | 3/3 | yes |
| S3_workflow_aware / support_operations | C-C-B → A-C-B | $0.0579 | $0.0671 | 1/1 | yes |
| S3_workflow_aware / support_operations | C-C-B → B-C-B | not estimable | $0.0043 | 1/1 | not estimable |
| S3_workflow_aware / support_operations | C-C-B → C-A-B | $0.0368 | $0.0447 | 1/1 | yes |
| S3_workflow_aware / support_operations | C-C-B → C-B-B | not estimable | $0.0054 | 1/1 | not estimable |
| S3_workflow_aware / support_operations | C-C-B → C-C-A | $0.0345 | $-0.0004 | 1/1 | no |
| S3_workflow_aware / support_operations | C-C-B → C-C-C | $-0.0063 | $0.0030 | 1/3 | no |
| S3_workflow_aware / support_operations | C-C-B → A-A-A | $0.1297 | $0.1394 | 1/3 | yes |
| S3_workflow_aware / support_operations | C-C-B → B-B-B | not estimable | $0.0050 | 1/3 | not estimable |

## Limitations

- Most project/path cells are single-run evidence.
- The pooled view includes retail_sales, which is pilot-exposed.
- v3.1 is a post-hoc secondary label view; frozen v3 remains primary.
- Router dollar quantities are post-hoc conversions of frozen token predictions, not prospective dollar predictions.
- No path should be called the cheapest combination without its feasibility denominator, evidence count, and cost-completeness status.
