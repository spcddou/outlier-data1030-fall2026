# Outlier — DATA1030 Group Project, Fall 2026

**Topic:** Forecast seasonally adjusted unemployment rates for 50 U.S. states and DC three reference months ahead. Team: **outlier**.

**Status, October 14, 2026:** API collection, preparation, three EDA figures, and a first exploratory model comparison are implemented and executed. The team must still interpret the evidence, review related work, write the midterm report, and confirm collaborators/TA assignments.

## Start here

- [Runnable notebook walkthrough / 中文代码讲解](src/project_walkthrough.ipynb)
- [Data dictionary: every analytical column, units and availability](data/data_dictionary.md)
- [Fixed first-run design](docs/plans/2026-10-14-bls-pipeline.md)
- [Quality receipt](results/data_quality.json), [split receipt](results/split_summary.json), [model receipt](results/model_run.json)
- [Report question outline](report/outline.md): the team supplies its own prose and captions.

The teammate-agent handoff is shared as a separate attachment outside this repository.

## Reproduce the frozen run

Use Python **3.11.15**. The executed package versions are NumPy **2.4.4**, pandas **3.0.2**, scikit-learn **1.9.0**, matplotlib **3.11.0**, and joblib **1.5.3**. HTTP/JSON collection uses Python's standard library.

```bash
python -m pip install -r requirements.txt
python src/bls_pipeline.py collect
python src/bls_pipeline.py prepare
python src/train_models.py
python src/make_eda.py
python -m unittest discover -s tests -v
```

Run these commands from the repository root. The notebook also runs from the root or from `src/`; install Jupyter separately if your course environment does not already provide it.

The committed raw snapshot is reused and its checksums verified. Completed model results are reused when input and source hashes match; normal reproduction does not call BLS again or repeat test scoring. Notebook code cells were executed in order using Python; opening through a Jupyter kernel was not separately verified.

[environment-pipeline.yml](environment-pipeline.yml) declares the executed core versions; creating a new Conda environment from it was not tested. [environment.yml](environment.yml) preserves the official course specification copied October 9, with its machine-specific prefix removed; that separate course environment was not installed here.

## Actual API collection

[src/bls_pipeline.py](src/bls_pipeline.py) sends JSON POST requests to the [BLS Public Data API](https://www.bls.gov/developers/api_signature.htm):

```text
POST https://api.bls.gov/publicAPI/v1/timeseries/data/
{"seriesid":["LASST440000000000003"],"startyear":"2014","endyear":"2023"}
```

This example is Rhode Island's seasonally adjusted unemployment rate. The actual collection requests all **204 series**: 51 areas × four LAUS measures, `03` unemployment rate, `04` unemployed, `05` employed, `06` labor force. The state FIPS mapping is [data/reference/states.csv](data/reference/states.csv); definitions and source links are in the dictionary. Annual `M13` records are excluded.

The full 2014–2024 anonymous run used **18 successful requests**, batched by series and years. Anonymous access permits 25 series/query, 10 years/query and 25 queries/day; registration permits 50 series, 20 years and 500 queries/day ([BLS limits](https://www.bls.gov/developers/api_FAQs.htm)). Optional registration is read from environment variable `BLS_API_KEY`; it is never saved in request manifests.

To deliberately collect a new currently revised snapshot:

```bash
python src/bls_pipeline.py collect --refresh
```

To resume an interrupted collection, pass its incomplete directory under data/raw/bls as `--snapshot data/raw/bls/<snapshot-id>`. Resume verifies saved hashes and requires the original registration mode. Save and export your key locally through your preferred secret manager; do not put it in code or Git. Complete raw responses, retrieval timestamps, query parameters and SHA-256 hashes are saved under [data/raw/bls/](data/raw/bls/).

## Dataset and prediction contract

| Item | Frozen run |
|---|---|
| Snapshot | `20261014T164700258612Z`, retrieved October 14, 2026 |
| Source period | January 2014–December 2024; 2014 supplies historical features |
| Raw monthly measure records | 26,928 |
| Complete state-month panel | 6,732 rows × 6 columns |
| Feature table | 6,732 rows × 24 columns, including metadata/labels |
| Feature-complete labeled table | 5,967 rows × 24 columns, origins January 2015–September 2024 |
| Predictors actually used | 16: state + 15 numeric features; see dictionary |
| Target | Same state's unemployment rate at reference month t+3, in percent |
| Baseline | Predict u(t+3) = u(t) |

History is computed within each state after reindexing the calendar. Missing months remain missing; three months never means three arbitrary rows. Predictors use the current rate, historical rate changes and employment/labor-force growth over 1/3/6/12 months, cyclic month encodings, and one-hot state. Raw employed, unemployed and labor-force counts are retained for quality checks; redundant level counts are excluded from model input.

All states share chronological boundaries. Train: origins **2015-01–2019-09**, **2,907** rows; validation: **2020-01–2021-09**, **1,071** rows; test: **2022-01–2024-09**, **1,683** rows. Earlier blocks purge origins whose three-month labels reach the next block. Within training, three expanding CV folds split whole months with a three-month gap; preprocessing is fitted inside each fold. The split receipt records exclusions and target-date boundaries. The 306 boundary rows remain in the labeled table with `split=excluded`; they are not scored as train/validation/test.

After validation selection, the winning estimator is refitted on all **4,131** pre-test origins whose labels precede January 2022, including old boundary rows once their labels are known. This evaluation pools states already represented in training; it does not test transfer to unseen states.

## First exploratory result

Ridge and Random Forest hyperparameters were tuned using training CV. Validation MAE selected Random Forest over Ridge and persistence before test scoring.

| Model | Validation MAE (percentage points) | Test MAE (percentage points) | Test RMSE (percentage points) |
|---|---:|---:|---:|
| Persistence | 2.293 | **0.141** | **0.198** |
| Random Forest, validation-selected | **1.811** | 0.302 | 0.580 |
| Ridge | 5.962 | Not evaluated | Not evaluated |

**The selected model did not beat persistence on the test period.** Preserve this negative result. A validation/test period difference is a possible explanation to investigate, not an established causal finding.

The test period has now been observed. Do not tune on these results and describe it as a fresh holdout. Changes to data/model code require explicit `python src/train_models.py --rerun`; previous completion receipts are archived under `results/history/`. Operational fixes were rerun with unchanged features, splits, estimator grid and selection rule, reproducing the same errors. An interruption marker also blocks silent test rescoring.

## Interpretation limits and next team tasks

- This is a retrospective study using a currently revised historical snapshot. [BLS historical seasonal adjustment](https://www.bls.gov/lau/lauseas.htm) can use later information; [LAUS technical notes](https://www.bls.gov/news.release/laus.tn.htm) explain revisions. Chronological feature construction does not remove this source-vintage limitation.
- Origin t means the latest reference month after its release. [State estimates are generally released the following month](https://www.bls.gov/lau/laufaq.htm). This does not establish a forecast exactly three calendar months after today's date.
- Three EDA figures use all available labeled periods, including test. The period is also observed through EDA; later adaptive analysis needs a separately justified future evaluation design.
- State-month observations share national shocks and serial dependence. Row count is not a count of independent experiments. MAE weights each state-month equally.
- Review the topic and collection scope with the mentor TA, read related unemployment-forecasting work, interpret figures and errors, write captions/report in your own words, and assign teammate roles. Full vintage-aware backtesting is an optional later extension, beyond this first cut.

## Midterm requirements

Course sources were checked October 9, 2026. Teams have **3–4 students**. The project is **35%** of the course grade: midterm report 10 percentage points, final presentation 25. The report is due **October 25, 2026 at 5 pm on Gradescope**, with no grace period.

Use code-based data collection; ready-made Kaggle/UCI/repository datasets do not satisfy the stated collection requirement. Document every column. The report must follow Introduction, Data, EDA, Problem description/potential impact, References, with at least **three explanatory figures**, labeled axes/captions, and at most **1,500 words including captions**; references/appendix are excluded. No code in the report. The team writes its own report prose; the rubric permits LLM grammar/typo help. Include required AI attribution and a permitted chat-history link when preparing the submission.

Keep the repository public and add every teammate as a collaborator. Final presentations are scheduled for the week of December 7; check the forthcoming final rubric for exact details.

- [Canvas syllabus](https://canvas.brown.edu/courses/1103554)
- [Official midterm rubric](https://docs.google.com/document/d/1kC3cgE-CPUVmveWHdKAqlbnaq2XMNKjzY9ifF6M97ps/edit)
- [EdStem rubric announcement](https://edstem.org/us/courses/104806/discussion/8310956)
- [Finalized teams](https://edstem.org/us/courses/104806/discussion/8358533)

## Repository and attribution

`data/`: frozen API responses, state mapping, processed tables and dictionary. `src/`: collector/preparation, modeling, EDA and notebook. `figures/`: three PNGs with source CSVs. `results/`: quality/split/model receipts, CV results, predictions and saved estimator. `tests/`: offline data-contract and interruption checks. `report/`: team report outline. `docs/`: design and archived topic comparisons.

The MIT license applies to original project code/documentation; external data retain their source attribution/terms. Data source: U.S. Bureau of Labor Statistics, Local Area Unemployment Statistics. Planning and implementation were assisted by OpenAI Codex and reviewed with offline tests. Team members remain responsible for understanding the code, interpreting results, and authoring submitted work.
