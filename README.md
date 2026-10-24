# Outlier — DATA1030 Group Project, Fall 2026

We study whether a state's recent unemployment history can predict its unemployment rate **three reference months ahead**.

## What we have done

Start with [the main notebook](src/unemployment_linear_regression.ipynb). It includes code, saved results, and four inline EDA plots.

- English report: [PDF](report/data1030_report_outlier.pdf) · [Word](report/data1030_report_outlier.docx)
- [Data dictionary](data/data_dictionary.md): column definitions, units, all 51 area codes, and encoding rules.
- [Report figures](figures/): the four images embedded in the report.

- **Collection:** six BLS Public Data API requests for seasonally adjusted monthly unemployment rates, covering 50 states + DC, January 2014–December 2024 (6,732 state-month observations).
- **Preparation:** check monthly coverage, duplicates, and valid rates; create lagged features and a three-month-ahead target (5,967 complete labeled rows).
- **Features:** current unemployment rate, rates 1/3/6/12 months earlier, and state identity. One-hot encoding gives 55 input columns. Dates and the future target are excluded from predictors.
- **EDA:** state trends, current versus future rates, target distributions across time periods, and training-period autocorrelation for all 50 states and DC. Figure 4 shows each area separately and the median across areas at each lag.
- **Model and benchmark:** one ordinary `sklearn.linear_model.LinearRegression`, without tuning, compared with a persistence benchmark that uses the current unemployment rate to predict the rate three months later. The model is trained on January 2015–September 2021 origins (4,131 rows) and evaluated on January 2022–September 2024 origins (1,683 rows). October–December 2021 origins are excluded because their targets cross into 2022.
- **Saved test results:** linear regression has an MAE of **0.772 percentage points**, RMSE of **0.854 percentage points**, and R² of **−0.164**. The persistence benchmark has an MAE of **0.141**, RMSE of **0.198**, and R² of **0.938**. The persistence benchmark substantially outperforms the current linear regression specification.

BLS historical values are revised. We have not reconstructed original release vintages, and the test period has already been viewed. Month `t` is generally released in the following month, so this is a retrospective reference-month forecasting exercise, not a verified real-time forecast.

## Run with the data1030 environment

1. Clone the repository (or run `git pull` inside an existing clone):

   ```bash
   git clone https://github.com/spcddou/outlier-data1030-fall2026.git
   cd outlier-data1030-fall2026
   ```

2. Use your existing course environment:

   ```bash
   conda activate data1030
   python -c "import sys; print(sys.executable); print(sys.prefix)"
   ```

   Both paths should point to `data1030`. If you do not have the environment yet, create it from the repository root with `conda env create -f environment.yml`, then activate it.

3. Register the kernel if it is not listed:

   ```bash
   python -m ipykernel install --user --name data1030 --display-name "Python (data1030)"
   ```

4. Launch Jupyter **from `src/`**, because the notebook uses its working directory for input/output:

   ```bash
   cd src
   python -m jupyter notebook unemployment_linear_regression.ipynb
   ```

5. Select **Python (data1030)** and run all cells from top to bottom. In VS Code, open the notebook, select that same kernel, and ensure the working directory is `src/`. The first cell checks the environment and directory.

The recorded run used Python 3.14.6, NumPy 2.4.6, pandas 3.0.3, scikit-learn 1.9.0, and matplotlib 3.11.0. `environment.yml` contains the broader course environment; only ordinary linear regression is used here.

### Data and outputs

- No API key is required. A first run needs internet access and sends six requests to the [BLS API](https://www.bls.gov/developers/api_signature.htm).
- The notebook saves responses to `src/raw/batch_01.json` through `batch_06.json` and reuses them on later runs.
- It writes `state_month_unemployment.csv`, `model_data.csv`, `test_predictions.csv`, and `metrics.json` inside `src/`. Plots display inline with `plt.show()`.
- Raw API responses are included in the repository and reused by the notebook to ensure reproducibility when the BLS API is temporarily unavailable. Generated CSV files may be recreated by running the notebook.
- Earlier planning files under `docs/` and `report/outline.md` are historical scaffolding. Use the notebook and linked English report for the implemented analysis. The teammate handoff remains a separate attachment outside this repository.

## Join the repository

Anyone can read or clone this public repository. To push changes, teammates need collaborator access:

1. Send your GitHub username to the repository owner, **spcddou**.
2. The owner opens [Settings → Collaborators](https://github.com/spcddou/outlier-data1030-fall2026/settings/access), clicks **Add people**, selects your account, and sends an invitation.
3. Accept the invitation through GitHub or the invitation email. Cloning alone does not grant write access.

See [GitHub's collaborator instructions](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/repository-access-and-collaboration/inviting-collaborators-to-a-personal-repository).

For contributions, pull the latest `main`, work on your own branch, and open a pull request so teammates can review changes. Coordinate before editing the same notebook, and stage only the files you intend to share.

## Sources and license

- [BLS Local Area Unemployment Statistics](https://www.bls.gov/lau/)
- [BLS API documentation](https://www.bls.gov/developers/api_signature.htm)
- [BLS methods and revisions](https://www.bls.gov/news.release/laus.tn.htm)

The MIT license applies to original project code and documentation. External data retain their original terms. Code and documentation were prepared with OpenAI Codex assistance; the team is responsible for checking and understanding the work.
