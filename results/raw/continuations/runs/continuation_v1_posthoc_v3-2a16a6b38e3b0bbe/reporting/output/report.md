# 2024 Smart-Meter Electricity Consumption: Verified Findings Report

Total 2024 electricity consumption reached 1,207,699.96 kWh across 1,428 meter readings (mean 845.73 kWh per reading). Industrial sites drove 82.42% of usage. Demand was seasonal — strongest in Q4 and Q1, weakest in Q3 — and rose 4.71% in the second half versus the first. Peak and off-peak tariffs were nearly balanced (49.65% peak share). Commercial consumption correlates moderately negatively (-0.64) with temperature, and hot-day commercial load averaged just 415.29 kWh.

## Key findings
- [q1] In 2024 the portfolio consumed 1,207,699.96 kWh in total across 1,428 smart-meter readings, an average of 845.73 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
  - Direction: not_applicable
- [q2] Industrial buildings dominate consumption at 995,362.16 kWh (82.42% of the total), followed by Commercial at 196,367.15 kWh (16.26%) and Residential at 15,970.65 kWh (1.32%).
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Direction: not_applicable
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.42
  - Derived share(kwh_commercial, total_kwh): 16.26
  - Derived share(kwh_residential, total_kwh): 1.32
- [q3] Quarterly consumption was highest in Q4 (352,881.81 kWh) and Q1 (319,677.67 kWh), and lowest in Q2 (270,277.36 kWh) and Q3 (264,863.12 kWh); Q4 rebounded 33.23% above the Q3 trough.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Direction: not_applicable
  - Ranking: Q4, Q1, Q2, Q3
  - Derived pct_change(kwh_q4, kwh_q3): 33.23
- [q4] Consumption increased by 4.71% in the second half of 2024, rising from 589,955.03 kWh in January–June to 617,744.93 kWh in July–December, a gain of 27,789.90 kWh.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] On hot days (temperature ≥ 25°C), commercial sites produced 19 readings averaging 415.29 kWh — roughly half (0.49×) the overall per-reading mean of 845.73 kWh.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
  - Direction: not_applicable
  - Derived ratio(hot_commercial_mean_kwh, mean_kwh_per_reading): 0.49
- [q6] Consumption is highly variable and right-skewed: median 406.8 kWh versus a mean of 845.73 kWh, with a sample standard deviation of 913.44 kWh. Mean temperature across valid readings was 11.61°C, and 62 readings lack a temperature value. For commercial buildings, temperature and energy show a moderate negative Pearson correlation of -0.64.
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
  - Direction: not_applicable
- [q7] Off-peak tariff consumption (608,075.89 kWh) slightly exceeded peak (599,624.07 kWh), a gap of 8,451.82 kWh; peak share was 49.65% of total usage. Twelve unique meters were recorded, and the highest-use single meter consumed 252,241.26 kWh (20.89% of total).
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Direction: not_applicable
  - Ranking: off-peak, peak
  - Derived difference(kwh_off_peak, kwh_peak): 8451.82
  - Derived share(highest_use_meter_kwh, total_kwh): 20.89

## Limitations
- 62 of 1,428 readings are missing temperature values, so all temperature-based results exclude those records.
- The hot-day commercial average (415.29 kWh) rests on only 19 readings, a small sample.
- Consumption is strongly right-skewed (mean 845.73 vs median 406.8 kWh), so averages are heavily influenced by large industrial readings.
- The -0.64 commercial temperature–energy correlation is associative, not causal, and may reflect seasonal operating schedules rather than cooling demand.
- Data cover a single year with no prior-year baseline, and only 12 meters were monitored; residential use (1.32% of total) may be underrepresented.

## Conclusion
Industrial load dominates and should be the primary focus for efficiency and procurement. The winter-peaking seasonal pattern and near-even peak/off-peak split suggest limited tariff-shifting savings but clear seasonal budgeting needs. Stakeholders should treat hot-day and correlation results cautiously given small samples and missing temperature data.
