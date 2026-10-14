"""Collect BLS LAUS data and prepare a calendar-aligned forecasting panel.

Run from the repository root:
    python src/bls_pipeline.py collect
    python src/bls_pipeline.py prepare
An existing complete snapshot is reused unless --refresh is requested.
"""
import argparse
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

ROOT = Path(__file__).resolve().parents[1]
API_V1 = "https://api.bls.gov/publicAPI/v1/timeseries/data/"
API_V2 = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
MEASURES = {"03": "unemployment_rate", "04": "unemployed",
            "05": "employed", "06": "labor_force"}
LAGS = (1, 3, 6, 12)
NUMERIC_FEATURES = (["unemployment_rate"] + [f"ur_change_{lag}m" for lag in LAGS]
                    + [f"{name}_growth_{lag}m" for name in ("employed", "labor_force") for lag in LAGS]
                    + ["month_sin", "month_cos"])
FEATURES = ["state"] + NUMERIC_FEATURES
TARGET = "target_unemployment_rate"


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def series_mapping(root=ROOT):
    """BLS: LA + S (seasonally adjusted) + state area code + two-digit measure."""
    states = pd.read_csv(Path(root) / "data/reference/states.csv", dtype=str)
    if len(states) != 51 or states.fips.duplicated().any():
        raise ValueError("Expected 50 distinct state codes plus DC")
    return {f"LASST{row.fips}00000000000{code}": (row.state, measure)
            for row in states.itertuples() for code, measure in MEASURES.items()}


def request_plan(series_ids, start_year, end_year, registered=False):
    if start_year > end_year or not series_ids or len(series_ids) != len(set(series_ids)):
        raise ValueError("Provide distinct series and an ordered year range")
    batch_size, year_limit = (50, 20) if registered else (25, 10)
    return [{"seriesid": series_ids[i:i + batch_size], "startyear": str(start),
             "endyear": str(min(start + year_limit - 1, end_year))}
            for start in range(start_year, end_year + 1, year_limit)
            for i in range(0, len(series_ids), batch_size)]


def parse_response(response, mapping):
    """Keep monthly observations, preserve footnotes, reject incomplete series responses."""
    if response.get("status") != "REQUEST_SUCCEEDED":
        raise ValueError(f"BLS request failed: {response.get('message', [])}")
    result = response.get("Results", {})
    if isinstance(result, list):
        result = result[0] if result else {}
    series = result.get("series", [])
    returned = [item["seriesID"] for item in series]
    if set(returned) != set(mapping) or len(returned) != len(mapping):
        raise ValueError("BLS response contains missing, duplicate or unexpected series")
    rows = []
    for item in series:
        state, measure = mapping[item["seriesID"]]
        if not item.get("data"):
            raise ValueError(f"Empty series: {item['seriesID']}")
        for point in item["data"]:
            period = point["period"]
            if period == "M13":  # Annual average: not a monthly observation.
                continue
            if period not in {f"M{i:02d}" for i in range(1, 13)}:
                raise ValueError(f"Unexpected monthly period: {period}")
            rows.append({"state": state, "month": f"{int(point['year']):04d}-{period[1:]}",
                         "measure": measure, "value": float(point["value"].replace(",", "")),
                         "series_id": item["seriesID"],
                         "footnotes": json.dumps(point.get("footnotes", []), ensure_ascii=False)})
    return rows


def fetch_response(parameters, api_key=None):
    """Actual POST request; credentials are injected only into the in-memory payload."""
    endpoint = API_V2 if api_key else API_V1
    payload = dict(parameters)
    if api_key:
        payload["registrationkey"] = api_key
    request = urllib.request.Request(endpoint, data=json.dumps(payload).encode(),
                                    headers={"Content-Type": "application/json"}, method="POST")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                text = response.read().decode()
            # A registration key must not leak into a saved response or an error message.
            if api_key:
                text = text.replace(api_key, "[REDACTED]")
            return json.loads(text)
        except urllib.error.HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == 2:
                raise
        time.sleep(2 ** (attempt + 1))


def verify_recorded_batches(snapshot, manifest):
    for item in manifest["responses"]:
        path = Path(snapshot) / item["file"]
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(f"Raw snapshot checksum mismatch: {path.name}")


def collect(root=ROOT, start_year=2014, end_year=2024, refresh=False, snapshot=None):
    root = Path(root)
    mapping = series_mapping(root)
    key = os.environ.get("BLS_API_KEY") or None
    parameters = request_plan(list(mapping), start_year, end_year, registered=bool(key))
    raw_root = root / "data/raw/bls"
    raw_root.mkdir(parents=True, exist_ok=True)
    if snapshot is None and not refresh:
        manifests = sorted(raw_root.glob("*/manifest.json"), reverse=True)
        for path in manifests:
            manifest = json.loads(path.read_text())
            if manifest.get("complete") and manifest["start_year"] == start_year and manifest["end_year"] == end_year:
                verify_recorded_batches(path.parent, manifest)
                print(f"Reusing frozen snapshot: {path.parent.relative_to(root)}", flush=True)
                return path.parent
    snapshot = Path(snapshot) if snapshot else raw_root / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    snapshot.mkdir(parents=True, exist_ok=True)
    manifest = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "start_year": start_year,
                "end_year": end_year, "seasonal_adjustment": "S", "series_count": len(mapping),
                "source": API_V2 if key else API_V1, "registered": bool(key), "complete": False,
                "vintage_policy": "Currently revised data; not historical real-time vintages.", "responses": []}
    manifest_path = snapshot / "manifest.json"
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text())
        if (previous["start_year"], previous["end_year"], previous["series_count"]) != (start_year, end_year, len(mapping)):
            raise ValueError("Snapshot scope does not match this collection plan")
        # Check the OLD hashes before any overwrite can re-sign a modified frozen batch.
        verify_recorded_batches(snapshot, previous)
        if previous["complete"]:
            print(f"Reusing verified complete snapshot: {snapshot.relative_to(root)}", flush=True)
            return snapshot
        if previous["registered"] != bool(key):
            raise ValueError("Resume with the original API registration mode, or create a new snapshot")
        if any(item["request"] != parameters[i] for i, item in enumerate(previous["responses"])):
            raise ValueError("Saved batch plan does not match this collection plan")
        # Keep every old hash even if this resume is interrupted before revisiting it.
        manifest = {**previous, "complete": False}
    for number, params in enumerate(parameters, 1):
        path = snapshot / f"response_{number:02d}.json"
        if path.exists():
            saved = json.loads(path.read_text())
            if saved["request"] != params:
                raise ValueError("Cached request does not match this collection plan")
            response = saved["response"]
        else:
            print(f"BLS request {number}/{len(parameters)}: {len(params['seriesid'])} series, "
                  f"{params['startyear']}–{params['endyear']}", flush=True)
            response = fetch_response(params, key)
            # Validate before saving a successful batch; API-level errors must stop collection.
            parse_response(response, {sid: mapping[sid] for sid in params["seriesid"]})
            saved = {"retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                     "request": params, "response": response}
            path.write_text(json.dumps(saved, ensure_ascii=False, separators=(",", ":")) + "\n")
        rows = parse_response(response, {sid: mapping[sid] for sid in params["seriesid"]})
        if any(not (f"{params['startyear']}-01" <= row["month"] <= f"{params['endyear']}-12") for row in rows):
            raise ValueError("BLS returned observations outside the requested years")
        if number > len(manifest["responses"]):
            manifest["responses"].append({"file": path.name, "request": params, "monthly_rows": len(rows),
                                          "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
            write_json(snapshot / "manifest.json", manifest)
    manifest["complete"] = True
    write_json(snapshot / "manifest.json", manifest)
    print(f"Saved complete snapshot: {snapshot.relative_to(root)}", flush=True)
    return snapshot


def read_snapshot(snapshot, root=ROOT):
    snapshot = Path(snapshot)
    manifest = json.loads((snapshot / "manifest.json").read_text())
    if not manifest["complete"]:
        raise ValueError("Collection is incomplete; resume it before preparing data")
    mapping, rows = series_mapping(root), []
    for item in manifest["responses"]:
        path = snapshot / item["file"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(f"Raw snapshot checksum mismatch: {path.name}")
        saved = json.loads(path.read_text())
        rows.extend(parse_response(saved["response"], {sid: mapping[sid] for sid in item["request"]["seriesid"]}))
    return pd.DataFrame(rows), manifest


def make_features(panel):
    """Reindex the calendar before shift: gaps stay missing, histories stay within state."""
    if panel.duplicated(["state", "month"]).any():
        raise ValueError("Duplicate state-month rows")
    calendar = pd.period_range(panel.month.min(), panel.month.max(), freq="M")
    pieces = []
    for state, group in panel.groupby("state", sort=True):
        group = group.copy()
        group.index = pd.PeriodIndex(group.month, freq="M")
        group = group.drop(columns=["state", "month"]).reindex(calendar)
        for lag in LAGS:
            group[f"ur_change_{lag}m"] = group.unemployment_rate - group.unemployment_rate.shift(lag)
            for name in ("employed", "labor_force"):
                previous = group[name].shift(lag)
                group[f"{name}_growth_{lag}m"] = 100 * (group[name] / previous.where(previous > 0) - 1)
        group["month_sin"] = np.sin(2 * np.pi * calendar.month / 12)
        group["month_cos"] = np.cos(2 * np.pi * calendar.month / 12)
        group[TARGET] = group.unemployment_rate.shift(-3)
        group["target_month"] = (calendar + 3).astype(str)
        group["state"], group["month"] = state, calendar.astype(str)
        pieces.append(group.reset_index(drop=True))
    return pd.concat(pieces, ignore_index=True)


def assign_splits(features, validation_start="2020-01", test_start="2022-01", study_start="2015-01"):
    if not study_start < validation_start < test_start:
        raise ValueError("Split dates must be ordered")
    out = features.copy()
    out["split"], out["exclusion_reason"] = "excluded", ""
    eligible = ((out.month >= study_start) & out[NUMERIC_FEATURES + [TARGET]].notna().all(axis=1)
                & np.isfinite(out[NUMERIC_FEATURES + [TARGET]].to_numpy(dtype=float)).all(axis=1))
    train = eligible & (out.month < validation_start) & (out.target_month < validation_start)
    val = eligible & (out.month >= validation_start) & (out.month < test_start) & (out.target_month < test_start)
    test = eligible & (out.month >= test_start)
    out.loc[train, "split"], out.loc[val, "split"], out.loc[test, "split"] = "train", "validation", "test"
    out.loc[out.split == "excluded", "exclusion_reason"] = "feature_history_unavailable"
    out.loc[eligible & (out.split == "excluded"), "exclusion_reason"] = "label_crosses_next_block"
    out.loc[out[TARGET].isna(), "exclusion_reason"] = "target_unavailable"
    out.loc[out.month < study_start, "exclusion_reason"] = "warmup_before_study_start"
    return out


def month_cv(frame, n_splits=3, test_size=12):
    """Split unique months, then map to rows; gap=3 is THREE MONTHS, not three rows."""
    months = np.array(sorted(frame.month.unique()))
    folds = []
    for train_m, val_m in TimeSeriesSplit(n_splits=n_splits, test_size=test_size, gap=3).split(months):
        train = frame.month.isin(months[train_m]) & (frame.target_month < months[val_m[0]])
        val = frame.month.isin(months[val_m])
        folds.append((np.flatnonzero(train.to_numpy()), np.flatnonzero(val.to_numpy())))
    return folds


def prepare(root=ROOT, snapshot=None):
    root = Path(root)
    if snapshot is None:
        snapshot = collect(root)  # Reuses a complete snapshot by default.
    long, manifest = read_snapshot(snapshot, root)
    months = pd.period_range(f"{manifest['start_year']}-01", f"{manifest['end_year']}-12", freq="M").astype(str)
    states = sorted({state for state, _ in series_mapping(root).values()})
    duplicates = int(long.duplicated(["state", "month", "measure"]).sum())
    if duplicates:
        raise ValueError(f"Duplicate state-month-measure observations: {duplicates}")
    grid = pd.MultiIndex.from_product([states, months], names=["state", "month"])
    panel = long.pivot(index=["state", "month"], columns="measure", values="value").reindex(grid)
    panel.columns.name = None
    panel = panel.reset_index()
    levels = ["unemployed", "employed", "labor_force"]
    arithmetic = (panel.employed + panel.unemployed - panel.labor_force).abs()
    derived_rate = 100 * panel.unemployed / panel.labor_force
    rate_difference = (derived_rate - panel.unemployment_rate).abs()
    missing = {name: int(panel[name].isna().sum()) for name in MEASURES.values()}
    bad_domain = int((~panel.unemployment_rate.between(0, 100)
                      | (panel[levels] < 0).any(axis=1) | (panel.labor_force <= 0)).sum())
    quality = {"snapshot": str(Path(snapshot).relative_to(root)), "states": len(states),
               "monthly_observations_long": len(long), "state_month_rows": len(panel),
               "period": [months[0], months[-1]], "duplicate_keys": duplicates,
               "missing_by_measure": missing, "domain_violations": bad_domain,
               "labor_force_identity_max_difference_people": float(arithmetic.max()),
               "rate_identity_max_difference_percentage_points": float(rate_difference.max()),
               "rate_identity_tolerance_percentage_points": .11,
               "vintage_policy": manifest["vintage_policy"]}
    quality["passed"] = bool(not any(missing.values()) and bad_domain == 0
                             and arithmetic.max() <= 1 and rate_difference.max() <= .11)
    write_json(root / "results/data_quality.json", quality)
    if not quality["passed"]:
        raise ValueError("Source quality checks failed; inspect results/data_quality.json")
    processed = root / "data/processed"
    processed.mkdir(parents=True, exist_ok=True)
    long.to_csv(processed / "observations_long.csv", index=False)
    panel.to_csv(processed / "state_month_panel.csv", index=False)
    features = assign_splits(make_features(panel))
    features.to_csv(processed / "feature_table.csv", index=False)
    usable = features[(features.month >= "2015-01") & features[NUMERIC_FEATURES + [TARGET]].notna().all(axis=1)].copy()
    usable.to_csv(processed / "model_table.csv", index=False)
    summary = {"snapshot": quality["snapshot"], "target": "unemployment rate at origin reference month + 3",
               "features": FEATURES, "validation_start": "2020-01", "test_start": "2022-01",
               "feature_complete_labeled_rows": len(usable), "split_rows": features.split.value_counts().to_dict(),
               "excluded_reasons": features.loc[features.split == "excluded", "exclusion_reason"].value_counts().to_dict(),
               "boundaries": {name: {"rows": len(group), "origin_min": group.month.min(),
                                      "origin_max": group.month.max(), "target_max": group.target_month.max()}
                              for name, group in usable[usable.split != "excluded"].groupby("split")},
               "release_assumption": "Origin is latest available reference month after its release. "
                                     "Purging uses earlier target months; actual historical release dates/vintages are not reconstructed."}
    write_json(root / "results/split_summary.json", summary)
    print(json.dumps({"quality_passed": True, "panel_rows": len(panel), "labeled_rows": len(usable),
                      "split_rows": summary["split_rows"]}, indent=2), flush=True)
    return features


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["collect", "prepare"])
    parser.add_argument("--refresh", action="store_true", help="Create a new snapshot and consume API quota")
    parser.add_argument("--snapshot", type=Path, help="Use/resume a particular snapshot directory")
    args = parser.parse_args()
    if args.stage == "collect":
        collect(refresh=args.refresh, snapshot=args.snapshot)
    else:
        prepare(snapshot=args.snapshot)


if __name__ == "__main__":
    main()
