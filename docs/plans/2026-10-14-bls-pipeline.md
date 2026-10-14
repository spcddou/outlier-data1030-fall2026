# BLS state unemployment pipeline implementation plan

Team-selected topic: three-month-ahead U.S. state unemployment rate prediction.

## Scope and fixed first-run choices

- Unit: state × reference month; 50 states plus DC, seasonally adjusted LAUS.
- Collection: four measures (unemployment rate, unemployed, employed, labor force), 2014–2024. Year 2014 supplies historical features; modeling origins start in January 2015. Labels after December 2024 are unavailable and excluded.
- Target: the same state's unemployment rate exactly three calendar months after the feature month.
- Data interpretation: a fixed snapshot of currently revised historical data. No historical release-vintage reconstruction or claim of operational real-time forecasting.
- Splits: validation origins start January 2020; test origins start January 2022. Earlier blocks exclude rows whose target month reaches the next block. All states share month boundaries.
- Models: persistence baseline; Ridge and Random Forest, with month-grouped, label-purged CV on training data. Choose using validation MAE, then evaluate only the locked winner and persistence on test.
- EDA: trends, current-versus-future unemployment, and three-month change distributions. These are exploratory figures; the team writes the submission's captions and prose.
- Deliverables: runnable Python scripts, explanatory notebook, source snapshots/manifests, processed CSVs, quality checks, figures, and exploratory model results. Standalone handoff stays outside GitHub.

## Implementation order and verification

1. Add meaningful tests for calendar alignment, per-state history, missing months, API error/annual-record handling and label-aware month splits; observe failures before implementing.
2. Implement API batching within documented limits, environment-variable key support, frozen raw responses and resumable cached batches. Never serialize the registration key.
3. Parse and validate complete state/month/measure coverage; report duplicates, missing fields, domains and labor-force arithmetic, allowing published rounding.
4. Build calendar-based historical features and target, save usable rows and an explicit exclusion reason for unusable rows. Save split counts and boundaries.
5. Create reproducible static EDA figures and their source tables; inspect exported images.
6. Implement training-only preprocessing/CV, validation selection, locked test evaluation and an explicit completion receipt. Reuse completed results rather than silently repeating test evaluations.
7. Add a small notebook walkthrough, actual dependency versions, updated README/data dictionary and standalone handoff. Run tests and scripts end to end, then commit and push reviewable code.

No model performance claim is made before the run. Test results are exploratory, and the evaluated period becomes observed once results are viewed.
