"""Tune on training months, select on validation, evaluate a locked winner on test."""
import argparse
import hashlib
import importlib.metadata
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from bls_pipeline import ROOT, FEATURES, NUMERIC_FEATURES, TARGET, month_cv, write_json


def metrics(actual, predicted):
    return {"mae_percentage_points": float(mean_absolute_error(actual, predicted)),
            "rmse_percentage_points": float(np.sqrt(mean_squared_error(actual, predicted)))}


def model_pipeline(estimator):
    # Every fold fits its own scaling and state encoding; no preprocessing on held-out data.
    preprocessing = ColumnTransformer([
        ("numeric", StandardScaler(), NUMERIC_FEATURES),
        ("state", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["state"])])
    return Pipeline([("preprocess", preprocessing), ("model", estimator)])


def run_models(root=ROOT, rerun=False):
    root = Path(root)
    path = root / "data/processed/model_table.csv"
    fingerprint = hashlib.sha256(path.read_bytes()).hexdigest()
    implementation_hash = hashlib.sha256((root / "src/train_models.py").read_bytes()
                                         + (root / "src/bls_pipeline.py").read_bytes()).hexdigest()
    receipt_path = root / "results/model_run.json"
    evaluation_marker = root / "results/test_evaluation_started.json"
    if receipt_path.exists() and not rerun:
        receipt = json.loads(receipt_path.read_text())
        if receipt["input_sha256"] != fingerprint or receipt.get("implementation_sha256") != implementation_hash:
            raise ValueError("Data or model code changed after test evaluation. Preserve the old results; "
                             "an explicit --rerun is an evaluation on an already observed period.")
        print("Reusing completed exploratory results; test has already been observed.", flush=True)
        print(json.dumps(receipt["test_metrics"], indent=2), flush=True)
        return receipt
    if evaluation_marker.exists() and not receipt_path.exists() and not rerun:
        raise ValueError("An interrupted/incomplete run may already have observed the test period; "
                         "inspect its artifacts and use explicit --rerun to repeat evaluation.")
    if receipt_path.exists() or evaluation_marker.exists():
        print("Explicit rerun: this test period is already observed, not a fresh holdout.", flush=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        if receipt_path.exists():
            write_json(root / f"results/history/model_run_{stamp}.json", json.loads(receipt_path.read_text()))
        elif evaluation_marker.exists():
            write_json(root / f"results/history/interrupted_run_{stamp}.json", json.loads(evaluation_marker.read_text()))
    frame = pd.read_csv(path)
    train = frame[frame.split == "train"].reset_index(drop=True)
    validation = frame[frame.split == "validation"].reset_index(drop=True)
    test = frame[frame.split == "test"].reset_index(drop=True)
    if any(group.empty for group in (train, validation, test)):
        raise ValueError("Train, validation and test must all contain observations")
    if not train.target_month.max() < validation.month.min() or not validation.target_month.max() < test.month.min():
        raise ValueError("An earlier block contains labels unavailable at the next block's start")
    folds = month_cv(train)
    configs = {
        "ridge": (Ridge(), {"model__alpha": [.1, 1, 10, 100]}),
        "random_forest": (RandomForestRegressor(n_estimators=150, random_state=1030, n_jobs=1),
                          {"model__max_depth": [5, None], "model__min_samples_leaf": [5, 20]})}
    rows = [{"model": "persistence", **metrics(validation[TARGET], validation.unemployment_rate)}]
    fitted, tuning = {}, {}
    for name, (estimator, grid) in configs.items():
        print(f"Tuning {name} with {len(folds)} month-grouped, purged folds", flush=True)
        search = GridSearchCV(model_pipeline(estimator), grid, cv=folds,
                              scoring="neg_mean_absolute_error", n_jobs=1, refit=True)
        search.fit(train[FEATURES], train[TARGET])
        fitted[name] = search.best_estimator_
        predicted = search.predict(validation[FEATURES])
        rows.append({"model": name, **metrics(validation[TARGET], predicted)})
        tuning[name] = {"best_parameters": search.best_params_,
                        "training_cv_mae_percentage_points": float(-search.best_score_)}
        pd.DataFrame(search.cv_results_).to_csv(root / f"results/{name}_cv.csv", index=False)
    comparison = pd.DataFrame(rows).sort_values("mae_percentage_points", kind="stable")
    comparison.to_csv(root / "results/validation_metrics.csv", index=False)
    winner = comparison.iloc[0].model
    selection = {"selected_model": winner, "selection_metric": "validation MAE",
                 "input_sha256": fingerprint, "implementation_sha256": implementation_hash,
                 "features": FEATURES, "tuning": tuning,
                 "test_start": "2022-01", "test_used_for_selection": False,
                 "training_cv": [{"train_origin_max": train.iloc[a].month.max(),
                                   "train_target_max": train.iloc[a].target_month.max(),
                                   "validation_origin_min": train.iloc[b].month.min(),
                                   "validation_origin_max": train.iloc[b].month.max()}
                                  for a, b in folds]}
    # Save selection before reading test outcomes for scoring.
    write_json(root / "results/model_selection.json", selection)
    write_json(evaluation_marker, {"started_at_utc": datetime.now(timezone.utc).isoformat(),
                                   "input_sha256": fingerprint, "implementation_sha256": implementation_hash,
                                   "selected_model": winner, "test_has_been_observed": True})
    if winner == "persistence":
        predicted = test.unemployment_rate.to_numpy()
        refit_rows = 0
    else:
        # Include previously purged old-boundary rows once their labels are known.
        development = frame[(frame.month < "2022-01") & (frame.target_month < "2022-01")]
        final_model = clone(fitted[winner]).fit(development[FEATURES], development[TARGET])
        predicted = final_model.predict(test[FEATURES])
        joblib.dump(final_model, root / "results/selected_model.joblib", compress=3)
        refit_rows = len(development)
    predictions = test[["state", "month", "target_month", "unemployment_rate", TARGET]].copy()
    predictions["persistence_prediction"] = test.unemployment_rate.to_numpy()
    predictions["selected_prediction"] = predicted
    predictions.to_csv(root / "results/test_predictions.csv", index=False)
    test_metrics = {"persistence": metrics(test[TARGET], predictions.persistence_prediction)}
    test_metrics[winner] = metrics(test[TARGET], predicted)
    by_state = [{"state": state, "rows": len(group),
                 **{f"selected_{k}": v for k, v in metrics(group[TARGET], group.selected_prediction).items()},
                 **{f"baseline_{k}": v for k, v in metrics(group[TARGET], group.persistence_prediction).items()}}
                for state, group in predictions.groupby("state")]
    pd.DataFrame(by_state).to_csv(root / "results/test_metrics_by_state.csv", index=False)
    baseline_mae = test_metrics["persistence"]["mae_percentage_points"]
    selected_mae = test_metrics[winner]["mae_percentage_points"]
    versions = {name: importlib.metadata.version(name) for name in ["numpy", "pandas", "scikit-learn", "matplotlib", "joblib"]}
    receipt = {**selection, "completed_at_utc": datetime.now(timezone.utc).isoformat(),
               "refit_rows": refit_rows, "test_rows": len(test), "test_metrics": test_metrics,
               "relative_mae_improvement_over_persistence_percent": 100 * (1 - selected_mae / baseline_mae),
               "python": platform.python_version(), "packages": versions,
               "test_has_been_observed": True, "scope": "Exploratory retrospective evaluation on currently revised BLS data; "
               "not real-time vintage evaluation, causal evidence, or deployment validation."}
    write_json(receipt_path, receipt)
    print(json.dumps({"selected_model": winner, "test_metrics": test_metrics,
                      "relative_mae_improvement_percent": receipt["relative_mae_improvement_over_persistence_percent"]}, indent=2), flush=True)
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rerun", action="store_true", help="Explicitly repeat evaluation on an already observed test period")
    run_models(rerun=parser.parse_args().rerun)
