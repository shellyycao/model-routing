# 2024 Smart-Meter Electricity Consumption Report

Analysis of 1,428 cleaned smart-meter readings for 2024 shows total consumption of 1,207,700 kWh across 12 meters. Industrial buildings dominate usage, accounting for over 82% of all energy consumed. Consumption dipped mid-year before recovering strongly in Q4, and the second half of the year was 4.7% higher than the first. Tariff split is nearly even, and a moderate negative correlation between temperature and commercial energy use suggests cooling-driven demand is not the primary commercial driver.

## Key findings
- [q1] Across all 1,428 readings in the cleaned dataset, total electricity consumption reached 1,207,700 kWh, with a mean of 845.7 kWh per reading.
  - Reported values: total_kwh=1207699.96, reading_count=1428.0, mean_kwh_per_reading=845.7282633053221
- [q2] Industrial buildings consumed the most energy at 995,362 kWh (82.4% of total), followed by Commercial at 196,367 kWh (16.3%) and Residential at 15,971 kWh (1.3%). The gap between Industrial and Commercial is substantial at approximately 799,000 kWh.
  - Reported values: kwh_residential=15970.65, kwh_commercial=196367.15, kwh_industrial=995362.16
  - Ranking: Industrial, Commercial, Residential
  - Derived share(kwh_industrial, total_kwh): 82.4
  - Derived share(kwh_commercial, total_kwh): 16.3
  - Derived share(kwh_residential, total_kwh): 1.3
  - Derived difference(kwh_industrial, kwh_commercial): 798995.01
- [q3] Quarterly consumption shows a U-shaped pattern: Q1 was highest at 319,678 kWh, declining through Q2 (270,277 kWh) and Q3 (264,863 kWh), then rebounding sharply to a year-high of 352,882 kWh in Q4.
  - Reported values: kwh_q1=319677.67, kwh_q2=270277.36, kwh_q3=264863.12, kwh_q4=352881.81
  - Ranking: Q4, Q1, Q2, Q3
- [q4] Second-half consumption (617,745 kWh) exceeded first-half consumption (589,955 kWh) by 4.7%, indicating an increase in demand over the course of the year.
  - Reported values: kwh_h1=589955.03, kwh_h2=617744.93, kwh_h2_vs_h1_change_pct=4.710511579162232
  - Direction: increase
  - Derived difference(kwh_h2, kwh_h1): 27789.9
- [q5] On hot days (temperature ≥ 25 °C), there were 19 commercial readings with a mean consumption of 415.3 kWh per reading, suggesting moderate but not extreme load uplift under high-temperature conditions.
  - Reported values: hot_commercial_reading_count=19.0, hot_commercial_mean_kwh=415.29368421052624
- [q6] The distribution of consumption is right-skewed: the median reading is 406.8 kWh while the standard deviation is 913.4 kWh, indicating a long upper tail driven by high-use meters. The mean temperature across readings with valid data is 11.6 °C; 62 readings have missing temperature values. Among commercial readings, the Pearson correlation between temperature and consumption is -0.64, suggesting that higher temperatures are associated with lower commercial energy use.
  - Reported values: kwh_median=406.8, kwh_std=913.4385157872866, temperature_mean=11.612298682284042, temperature_missing_count=62.0, commercial_temp_kwh_corr=-0.637636239865442
- [q7] Peak-tariff consumption (599,624 kWh, 49.7% of total) and off-peak consumption (608,076 kWh, 50.3%) are nearly equal, indicating no strong tariff-driven load-shifting. Across 12 distinct meters, the highest-consuming single meter recorded 252,241 kWh — roughly 20.9% of total site consumption.
  - Reported values: kwh_peak=599624.07, kwh_off_peak=608075.89, peak_kwh_share_pct=49.65008610251175, unique_meter_count=12.0, highest_use_meter_kwh=252241.26
  - Ranking: off-peak, peak
  - Derived share(kwh_off_peak, total_kwh): 50.3
  - Derived share(highest_use_meter_kwh, total_kwh): 20.9

## Limitations
- 62 readings have missing temperature values, which reduces the reliability of temperature-based analyses and may introduce bias if missingness is non-random.
- Only 19 commercial readings qualify as hot-day observations (temperature ≥ 25 °C), making the hot-day commercial load estimate statistically fragile.
- The dataset covers only 12 distinct meters; findings may not generalise to a broader meter population.
- The negative commercial temperature–consumption correlation is observational; confounding factors (e.g., seasonal occupancy patterns) are not controlled for.
- Residential consumption is very low relative to other building types, which may reflect under-representation of residential meters rather than true low usage.

## Conclusion
Industrial sites are the dominant energy consumers and should be the primary focus of any demand-management or efficiency programme. The Q4 surge and the H2 increase of 4.7% warrant investigation into seasonal or operational drivers. The near-even peak/off-peak split suggests limited tariff optimisation is currently occurring, presenting a potential cost-saving opportunity. Temperature data gaps and the small commercial hot-day sample should be addressed in future data collection to strengthen load-forecasting models.
