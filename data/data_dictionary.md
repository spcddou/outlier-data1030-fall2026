# BLS LAUS data dictionary

Snapshot: `20261014T164700258612Z`, collected October 14, 2026. Unit of observation: a U.S. state (or DC) and calendar reference month. All four LAUS measures are seasonally adjusted. Fifty states plus DC; Puerto Rico and territories excluded. BLS definitions concern the civilian noninstitutional population age 16 and over; unemployment has the BLS labor-force definition.

## Tables, keys and missingness

| File | Rows × columns | Key and scope |
|---|---:|---|
| `reference/states.csv` | 51 × 2 | Unique state FIPS |
| `processed/observations_long.csv` | 26,928 × 6 | Unique state/month/measure, 2014–2024 |
| `processed/state_month_panel.csv` | 6,732 × 6 | Unique state/month, 2014–2024 |
| `processed/feature_table.csv` | 6,732 × 24 | Full panel with features/labels/split metadata |
| `processed/model_table.csv` | 5,967 × 24 | Feature-complete labeled origins, January 2015–September 2024; includes 306 rows excluded at split boundaries |

There are no missing source measures in this snapshot. Historical features are missing for early warmup months; targets are missing for October–December 2024 because the snapshot ends in December. No forward filling or imputation is performed. Missing CSV cells mean unavailable; empty `exclusion_reason` means included. All measures/changes below are numeric; no variable is ordinal.

## Every feature-table / model-table column

| Column | Type, unit or categories | Definition and role |
|---|---|---|
| `state` | Nominal string; names in `reference/states.csv` | 50 states and District of Columbia. Model input, one-hot encoded within each fit. |
| `month` | Calendar string YYYY-MM | Feature/origin reference month t; temporal key, not directly a model input. |
| `unemployment_rate` | Continuous, percent of labor force | u(t), BLS measure 03; current model input and persistence prediction. Published to one decimal. |
| `unemployed` | Numeric count, people | U(t), measure 04. Retained for checks, excluded from model input. |
| `employed` | Numeric count, people | E(t), measure 05. Retained as source for historical growth; raw level excluded from model input. |
| `labor_force` | Numeric count, people | L(t), measure 06. Retained as source for historical growth; raw level excluded from model input. |
| `ur_change_1m` | Continuous, percentage points | u(t) − u(t−1); model input. |
| `ur_change_3m` | Continuous, percentage points | u(t) − u(t−3); model input. |
| `ur_change_6m` | Continuous, percentage points | u(t) − u(t−6); model input. |
| `ur_change_12m` | Continuous, percentage points | u(t) − u(t−12); model input. |
| `employed_growth_1m` | Continuous, percent | 100 × [E(t)/E(t−1) − 1]; model input. |
| `employed_growth_3m` | Continuous, percent | 100 × [E(t)/E(t−3) − 1]; model input. |
| `employed_growth_6m` | Continuous, percent | 100 × [E(t)/E(t−6) − 1]; model input. |
| `employed_growth_12m` | Continuous, percent | 100 × [E(t)/E(t−12) − 1]; model input. |
| `labor_force_growth_1m` | Continuous, percent | 100 × [L(t)/L(t−1) − 1]; model input. |
| `labor_force_growth_3m` | Continuous, percent | 100 × [L(t)/L(t−3) − 1]; model input. |
| `labor_force_growth_6m` | Continuous, percent | 100 × [L(t)/L(t−6) − 1]; model input. |
| `labor_force_growth_12m` | Continuous, percent | 100 × [L(t)/L(t−12) − 1]; model input. |
| `month_sin` | Continuous, dimensionless, [−1,1] | sin(2π × calendar month/12); model input. January=1, December=12. |
| `month_cos` | Continuous, dimensionless, [−1,1] | cos(2π × calendar month/12); model input. |
| `target_unemployment_rate` | Continuous, percent of labor force | u(t+3) for the same state; regression target, never a predictor. |
| `target_month` | Calendar string YYYY-MM | Exactly t+3 calendar months; label metadata, never a predictor. |
| `split` | Nominal: train, validation, test, excluded | Time-block assignment; metadata, never a predictor. |
| `exclusion_reason` | Nominal string or empty | Empty=included; `warmup_before_study_start`=2014; `target_unavailable`=future label missing; `label_crosses_next_block`=label enters next block; `feature_history_unavailable`=insufficient/invalid predictor history. Metadata only. |

The model uses **state + 15 numeric predictors = 16 input columns**, not all 24 columns. Percent and percentage points differ: a change from 4% to 5% is +1 percentage point and +25% relative growth. All differences/growth are state-specific; reindexing prevents gaps from changing lag length.

## Raw / long-table columns and reference mapping

The panel's six columns are `state`, `month`, `employed`, `labor_force`, `unemployed`, `unemployment_rate`, defined above. The long table has `state`, `month`, plus:

| Column | Type / meaning |
|---|---|
| `measure` | Nominal: unemployment_rate (03), unemployed (04), employed (05), labor_force (06). |
| `value` | Numeric; percent for measure 03, people for measures 04–06. |
| `series_id` | Nominal BLS identifier: `LA` + seasonal flag `S` + area `ST{two-digit FIPS}00000000000` + measure. Example `LASST440000000000003` is Rhode Island rate. |
| `footnotes` | JSON string preserving BLS footnotes, often an empty object/list; inspect original notes before interpreting flagged values. Not a model input. |

`reference/states.csv` has `fips` (two-digit nominal code, preserve leading zero) and `state` (nominal full name). It follows official BLS state-area codes; DC=11 and Rhode Island=44. There is no category ordering.

Raw JSON wrappers record `retrieved_at_utc`, `request` (seriesid/startyear/endyear), and `response` (original status/messages/series). Manifests record scope, registration mode, source endpoint, completeness, vintage policy and each response's file/hash/monthly row count. Registration keys are omitted; model features never include collection metadata.

## Generated result / figure fields

`results/test_predictions.csv` contains state, month, target_month, unemployment_rate, target_unemployment_rate (defined above), `persistence_prediction`=u(t) and `selected_prediction`=validation-selected model output, both in percent.

`results/validation_metrics.csv` uses nominal `model` and numeric `mae_percentage_points` / `rmse_percentage_points`. Per-state metrics add nominal `state`, integer `rows`, and `selected_` / `baseline_` prefixes to these same error units. CV files are sklearn GridSearchCV exports: parameter values, per-fold negative MAE scores, ranks, and fit/score times in seconds; they contain no model input features.

Figure 01's CSV has reference month and one percentage-rate column per state. Figure 02 uses the documented current/target fields. Figure 03 adds `change_percentage_points`=u(t+3)−u(t) and boolean `origin_in_2020_2021` identifying origin months January 2020–December 2021; the flag describes period grouping, not a causal effect.

## Availability, revisions and validity checks

At prediction time, input values must have been released for reference month t and all lagged months. State LAUS estimates generally appear the following month. The target is a future reference-month value; it is not a feature.

This snapshot uses currently revised historical data. Historical seasonal adjustment uses two-sided smoothing and revisions may use information unavailable at an original forecast date. We have **not** reconstructed historical releases/vintages. Results therefore describe retrospective forecasting with revised data, not a deployable real-time system.

Quality checks enforce complete 51-state × 132-month × four-measure coverage; unique keys; rate 0–100%; nonnegative population counts and positive labor force; |E+U−L| ≤1 person; |100U/L−u| ≤0.11 percentage points to allow published rounding. Actual source arithmetic maximum is zero people and rate difference approximately 0.05 percentage points. Source quality does not establish predictive value.

Official sources:
- [LAUS field/series definitions](https://www.bls.gov/help/def/la.htm)
- [BLS state area mapping](https://download.bls.gov/pub/time.series/la/la.area)
- [API request signature](https://www.bls.gov/developers/api_signature.htm), [API limits](https://www.bls.gov/developers/api_FAQs.htm)
- [LAUS definitions/technical notes](https://www.bls.gov/news.release/laus.tn.htm)
- [Seasonal adjustment](https://www.bls.gov/lau/lauseas.htm), [LAUS FAQ/release timing](https://www.bls.gov/lau/laufaq.htm)
