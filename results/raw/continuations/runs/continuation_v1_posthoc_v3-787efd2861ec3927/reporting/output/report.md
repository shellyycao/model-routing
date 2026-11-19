# 2024 Smart-Meter Electricity Consumption: Verified Findings for Business Stakeholders

The cleaned 2024 dataset of 1,428 smart-meter readings shows total electricity consumption of 1,207,699.96 kWh. Industrial sites dominate usage at 995,362.16 kWh, about 82.42% of the total. Demand is seasonal: Q4 is the highest-consumption quarter and Q3 the lowest, and second-half consumption rose 4.71% versus the first half. Peak and off-peak tariff usage is nearly balanced, with a peak share of 49.65%. Per-reading consumption is highly skewed, and Commercial usage shows a moderately strong negative correlation (r = -0.64) with temperature.

## Key findings
- [q1] Total 2024 electricity consumption was 1,207,699.96 kWh across 1,428 meter readings, an average of 845.73 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
  - Direction: not_applicable
- [q2] Industrial buildings consumed 995,362.16 kWh — roughly 82.42% of all usage — far ahead of Commercial (196,367.15 kWh) and Residential (15,970.65 kWh).
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Direction: not_applicable
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.42
- [q3] Consumption was highest in Q4 (352,881.81 kWh), followed by Q1 (319,677.67 kWh), Q2 (270,277.36 kWh) and Q3 (264,863.12 kWh); the gap between the highest and lowest quarters was 88,018.69 kWh.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Direction: not_applicable
  - Ranking: Q4, Q1, Q2, Q3
  - Derived difference(kwh_q4, kwh_q3): 88018.69
- [q4] Consumption increased from 589,955.03 kWh in January–June to 617,744.93 kWh in July–December, a rise of 4.71% (27,789.90 kWh) in the second half of the year.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] On hot days (temperature at or above 25 °C), 19 Commercial readings were recorded, averaging 415.29 kWh per reading — below the overall per-reading average of 845.73 kWh.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
  - Direction: not_applicable
- [q6] Consumption is strongly right-skewed: the median reading is 406.80 kWh versus a mean of 845.73 kWh, with a large standard deviation of 913.44 kWh. Average temperature was 11.61 °C, with 62 readings missing temperature data. Among Commercial readings, temperature and consumption correlate at -0.64, a moderately strong negative relationship.
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
  - Direction: not_applicable
- [q7] Off-peak consumption (608,075.89 kWh) slightly exceeded peak consumption (599,624.07 kWh) by 8,451.82 kWh, giving a peak share of 49.65%. Twelve unique meters reported data, and the single highest-use meter consumed 252,241.26 kWh — about 20.89% of the yearly total.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Direction: not_applicable
  - Ranking: off-peak, peak
  - Derived difference(kwh_off_peak, kwh_peak): 8451.82
  - Derived share(highest_use_meter_kwh, total_kwh): 20.89

## Limitations
- 62 readings lack temperature values, so temperature-based metrics (mean temperature, hot-day counts, correlation) exclude them.
- The hot-day Commercial sample is small (19 readings), making its mean sensitive to individual readings.
- Only 12 meters are covered, and one meter alone accounts for about 20.89% of total consumption, so results are concentrated in a few sites.
- The reported temperature–consumption correlation is associational, not causal; occupancy and operating schedules likely confound it.
- Findings cover a single year (2024), limiting conclusions about longer-term trends.

## Conclusion
2024 demand was dominated by Industrial consumption, peaked in Q4, and rose a modest 4.71% in the second half. Near-even peak/off-peak usage suggests little tariff-driven load shifting. Recommended next steps: investigate the single meter driving ~20.89% of consumption, plan capacity around Q4 peaks, and improve temperature data completeness before refining hot-weather Commercial load analysis.
