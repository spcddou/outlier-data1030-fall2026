# Outlier — DATA1030 Group Project, Fall 2026

We study whether a state's recent unemployment history can predict its unemployment rate **three reference months ahead**.

## What we have done

Start with [the main notebook](src/unemployment_linear_regression.ipynb). It includes code, saved results, and four inline EDA plots.

- English report: [PDF](report/data1030_report_outlier.pdf) · [Word](report/data1030_report_outlier.docx)
- [Data dictionary](data/data_dictionary.md): column definitions, units, and all 51 area codes for the source panel and EDA pairs.
- [Report figures](figures/): the four images embedded in the report.

- **Collection:** six BLS Public Data API requests for seasonally adjusted monthly unemployment rates, covering 50 states + DC, January 2014–December 2024 (6,732 state-month observations).
- **Preparation:** check monthly coverage, duplicates, and valid rates; align monthly dates within each state and pair current rates with actual rates three months later (5,967 complete pairs, 5 columns).
- **Scope:** API collection, data checks, and EDA of panel time-series data. No train/test split, model fitting, prediction, or benchmark evaluation is performed in this midterm notebook.
- **EDA:** how rates change over time and across states; how current rates relate to rates three months later; how future-rate distributions differ across calendar periods; and how autocorrelation changes with monthly lag. Figure 4 covers January 2015–December 2024 for all 50 states and DC, showing each area separately and the median across areas at each lag.

BLS historical values are revised. We have not reconstructed original release vintages, and the full 2015–2024 period has already been explored. Month `t` is generally released in the following month. These are descriptive EDA results, not verified real-time forecasts. Future modeling will use time-ordered validation.

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

The recorded run used Python 3.14.6, NumPy 2.4.6, pandas 3.0.3, and matplotlib 3.11.0. `environment.yml` contains the broader course environment; this midterm notebook uses no model-training libraries.

### Data and outputs

- No API key is required. The included cache allows offline reruns. If the cache is absent, the notebook needs internet access and sends six requests to the [BLS API](https://www.bls.gov/developers/api_signature.htm).
- The notebook saves responses to `src/raw/batch_01.json` through `batch_06.json` and reuses them on later runs.
- It writes `state_month_unemployment.csv` and `eda_pairs.csv` inside `src/`. Plots display inline with `plt.show()`.
- Raw API responses are included in the repository and reused by the notebook to ensure reproducibility when the BLS API is temporarily unavailable. Generated CSV files may be recreated by running the notebook.

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

OpenAI ChatGPT was used to review and revise portions of the report, including grammar, wording, reasoning, references, and formatting. It was also used to suggest possible next steps for the analysis and troubleshoot HTTP 503 errors encountered while using GitHub and JupyterLab. The relevant AI interaction records are provided in Appendix B of the report.
