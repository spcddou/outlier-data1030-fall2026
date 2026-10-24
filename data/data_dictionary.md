# Data dictionary

## Source panel

`data/state_month_unemployment.csv`: 6,732 rows, 3 columns; 50 states and DC, January 2014–December 2024.

| Column | Type | Meaning and unit |
|---|---|---|
| `state_code` | Categorical string | Two-digit area FIPS code; retain leading zeros. Categories are listed below. |
| `month` | Monthly date string | Reference month in YYYY-MM format. |
| `unemployment_rate` | Continuous | Seasonally adjusted unemployment rate, in percent: 4.5 means 4.5%. |

## EDA pairs

`data/eda_pairs.csv`: 5,967 rows, 5 columns; origins January 2015–September 2024. The three source-panel columns retain the definitions above.

| Additional column | Type | Meaning and unit |
|---|---|---|
| `target_unemployment_rate` | Continuous | Actual unemployment rate of the same area three reference months later, in percent. Proposed future regression target, not a prediction. |
| `target_month` | Monthly date string | Reference month plus three months, in YYYY-MM format. |

Rows are aligned to a complete monthly calendar within each area before shifting. No pair crosses an area boundary. The last three months of 2024 have no future labels and are excluded from this paired table. Neither output contains missing values. No train/test split, lag-feature matrix, model fitting, or benchmark evaluation is performed in this midterm notebook.

## Area categories

| Code | Area |
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


## Data versions

The raw JSON files in `data/raw/` preserve BLS API requests, responses, and UTC collection timestamps. Values are revised historical estimates, not reconstructed first-release vintages. Reference month and publication date differ; a month's value is generally released in the following month. EDA does not establish real-time information availability or forecasting performance.
