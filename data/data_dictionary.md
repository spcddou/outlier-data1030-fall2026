# Outlier Unemployment Data Dictionary

Updated October 24, 2026. This document describes the saved data used by the project's unemployment forecasting notebook.

## Dataset overview

- Source: U.S. Bureau of Labor Statistics (BLS), Local Area Unemployment Statistics (LAUS), collected through six Public Data API POST requests.
- Coverage: 50 states and the District of Columbia, January 2014–December 2024.
- Observation unit: one area in one calendar reference month. The combination of `state_code` and `month` identifies a row.
- All unemployment rates are seasonally adjusted. A rate of `4.5` means **4.5%**, not `0.045`.
- The prediction target is the same area's unemployment rate three reference months after the origin month.
- The data form a panel with repeated observations within areas and possible common shocks across areas. Rows are not assumed independent.
- No ordinal features are used. State identifiers are nominal categories; their numeric appearance does not imply ordering.

## Saved tables

| File | Rows | Columns | Contents |
|---|---:|---:|---|
| `state_month_unemployment.csv` | 6,732 | 3 | API observations organized into an area-month panel. |
| `model_data.csv` | 5,967 | 9 | Complete labeled rows with current/historical predictors and the future outcome. Origins cover January 2015–September 2024. |
| `test_predictions.csv` | 1,683 | 6 | Test identifiers, current rate, actual future rate, and OLS predictions. Origins cover January 2022–September 2024. |

The table below documents the union of all columns in these files. The raw panel uses `state_code`, `month`, and `unemployment_rate`. The modeling table uses all listed columns except `linear_regression_prediction`. The prediction file uses `state_code`, `month`, `target_month`, `unemployment_rate`, `target_unemployment_rate`, and `linear_regression_prediction`.

## Column definitions

Here, `u_s(t)` denotes area `s`'s unemployment rate for reference month `t`.

| Column | Variable type and storage | Unit or categories | Definition | Role |
|---|---|---|---|---|
| `state_code` | Nominal categorical; two-character string | One of the 51 FIPS codes listed below | State or DC identifier. For example, `44` identifies Rhode Island. Preserve leading zeros, such as `01`. | Row identifier and categorical model input, represented by dummy variables. |
| `month` | Temporal metadata; string in `YYYY-MM` format | Calendar reference month | Origin month `t`, describing the period measured by the current rate. It is not the publication or retrieval date. | Row identifier, ordering, and time-split metadata; excluded from model inputs. |
| `unemployment_rate` | Continuous; floating-point number | Percent of the civilian labor force | Current rate `u_s(t)`: unemployed persons as a percentage of the labor force. It is a rate, not a count of unemployed people or payroll jobs. | Numerical predictor. |
| `lag_1m` | Continuous; floating-point number | Percent | Same area's rate one calendar month earlier, `u_s(t-1)`. | Numerical predictor. |
| `lag_3m` | Continuous; floating-point number | Percent | Same area's rate three calendar months earlier, `u_s(t-3)`. | Numerical predictor. |
| `lag_6m` | Continuous; floating-point number | Percent | Same area's rate six calendar months earlier, `u_s(t-6)`. | Numerical predictor. |
| `lag_12m` | Continuous; floating-point number | Percent | Same area's rate twelve calendar months earlier, `u_s(t-12)`. | Numerical predictor. |
| `target_unemployment_rate` | Continuous; floating-point number | Percent | Same area's actual rate three calendar months later, `u_s(t+3)`. | Supervised-learning target and evaluation outcome; never a predictor. |
| `target_month` | Temporal metadata; string in `YYYY-MM` format | Calendar month | Origin month plus three calendar months. For example, origin `2022-01` has target month `2022-04`. | Label metadata and split eligibility check; excluded from model inputs. |
| `linear_regression_prediction` | Continuous; floating-point number | Percent | Rate predicted by the fitted `sklearn.linear_model.LinearRegression` for a test row. The model does not clip predictions to the 0–100 range. | Model output for comparison with the target; never a predictor. |

Lag columns contain historical **levels**, not differences, percentage changes, or rolling averages. For example, `lag_3m = 7.1` means a rate of 7.1% three months earlier.

MAE, RMSE, and signed prediction errors are measured in **percentage points**. They are evaluation results, not rate columns in the source or modeling tables. For example, a prediction of 4.0% and an actual value of 3.0% differ by 1.0 percentage point.

## State and DC categories

| `state_code` | Area |
|---|---|
| `01` | Alabama |
| `02` | Alaska |
| `04` | Arizona |
| `05` | Arkansas |
| `06` | California |
| `08` | Colorado |
| `09` | Connecticut |
| `10` | Delaware |
| `11` | District of Columbia |
| `12` | Florida |
| `13` | Georgia |
| `15` | Hawaii |
| `16` | Idaho |
| `17` | Illinois |
| `18` | Indiana |
| `19` | Iowa |
| `20` | Kansas |
| `21` | Kentucky |
| `22` | Louisiana |
| `23` | Maine |
| `24` | Maryland |
| `25` | Massachusetts |
| `26` | Michigan |
| `27` | Minnesota |
| `28` | Mississippi |
| `29` | Missouri |
| `30` | Montana |
| `31` | Nebraska |
| `32` | Nevada |
| `33` | New Hampshire |
| `34` | New Jersey |
| `35` | New Mexico |
| `36` | New York |
| `37` | North Carolina |
| `38` | North Dakota |
| `39` | Ohio |
| `40` | Oklahoma |
| `41` | Oregon |
| `42` | Pennsylvania |
| `44` | Rhode Island |
| `45` | South Carolina |
| `46` | South Dakota |
| `47` | Tennessee |
| `48` | Texas |
| `49` | Utah |
| `50` | Vermont |
| `51` | Virginia |
| `53` | Washington |
| `54` | West Virginia |
| `55` | Wisconsin |
| `56` | Wyoming |

## Encoded model inputs

The model uses five numerical columns: `unemployment_rate`, `lag_1m`, `lag_3m`, `lag_6m`, and `lag_12m`.

`pd.get_dummies(..., drop_first=True, dtype=float)` converts state identity to 50 binary columns. Each generated column is named `state_code_XX`, where `XX` is a code from the table above except `01`:

- Value `1.0`: the row belongs to that area.
- Value `0.0`: the row belongs to another area.
- Alabama (`01`) is the reference category and has no separate dummy column. Its 50 state dummy values are all zero.
- For example, `state_code_44 = 1.0` identifies a Rhode Island row.

Thus, each encoded input matrix has **55 columns**: five numerical predictors plus 50 state indicators. The current training matrix has 4,131 rows; the test matrix has 1,683 rows. The target and date metadata are excluded. Test columns are aligned to the training columns.

## Construction and missing values

- API annual-average observations with period `M13` are skipped.
- The saved source panel has 132 observations per area, with no missing rates or duplicate area-month keys. Source rates are checked to be finite and between 0 and 100.
- Within each area, observations are aligned to a complete monthly calendar before shifts are applied. No lag crosses an area boundary.
- The 612 rows in 2014 supply historical context and are excluded from labeled origins. The final three months of 2024 contribute another 153 excluded rows because future targets are unavailable. The resulting complete modeling table has 5,967 rows.
- Rows missing a required numerical predictor or target are dropped, not imputed. All three saved CSV files currently contain no missing values.
- Training requires both origin and target months before January 2022. This yields origins January 2015–September 2021. Test origins are January 2022–September 2024. The 153 labeled October–December 2021 origins are excluded from both sets because their targets enter 2022.

## Release timing and data versions

Reference months, publication dates, and API retrieval timestamps are distinct. A rate for month `t` is generally published in the following month. Current and historical input rates become observable after their respective releases; the future target is unavailable at the prediction origin.

The API snapshot contains revised historical estimates, not reconstructed first-release vintages. Historical values may incorporate later revisions and smoothing. Therefore, the chronological split and lag construction do not by themselves establish real-time information availability. Results should be interpreted as retrospective evaluations using this saved snapshot.

The original JSON cache retains each request, response, and `retrieved_at_utc` timestamp. A fresh API download may produce revised values and different results.

## Source documentation

- [BLS LAUS field definitions](https://www.bls.gov/help/def/la.htm)
- [BLS Public Data API request format](https://www.bls.gov/developers/api_signature.htm)
- [BLS LAUS area codes](https://download.bls.gov/pub/time.series/la/la.area)
- [BLS LAUS release timing and frequently asked questions](https://www.bls.gov/lau/laufaq.htm)
- [BLS LAUS technical note and revisions](https://www.bls.gov/news.release/laus.tn.htm)
