"""Important data-contract checks; no live API requests in these tests."""
import sys
import unittest
import hashlib
import json
import shutil
import tempfile
from unittest.mock import patch
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import bls_pipeline as pipeline
import train_models


def toy_panel():
    rows = []
    for state, offset in [("Alabama", 0), ("Alaska", 10)]:
        for i, month in enumerate(pd.period_range("2017-01", "2024-12", freq="M")):
            rows.append({"state": state, "month": str(month),
                         "unemployment_rate": 3 + offset + i / 100,
                         "unemployed": 300 + i, "employed": 9700 + i,
                         "labor_force": 10000 + 2 * i})
    return pd.DataFrame(rows)


class PipelineTests(unittest.TestCase):
    def test_interrupted_resume_preserves_all_previously_recorded_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data/reference").mkdir(parents=True)
            shutil.copy(pipeline.ROOT / "data/reference/states.csv", root / "data/reference/states.csv")
            mapping = pipeline.series_mapping(root)
            snapshot = root / "data/raw/fixture"
            snapshot.mkdir(parents=True)
            records = []
            for number, request in enumerate(pipeline.request_plan(list(mapping), 2014, 2024)[:2], 1):
                response = {"status": "REQUEST_SUCCEEDED", "Results": {"series": [
                    {"seriesID": sid, "data": [{"year": request["startyear"], "period": "M01", "value": "3"}]}
                    for sid in request["seriesid"]]}}
                path = snapshot / f"response_{number:02d}.json"
                path.write_text(json.dumps({"request": request, "response": response}))
                records.append({"file": path.name, "request": request, "monthly_rows": 25,
                                "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
            manifest = {"created_at_utc": "original", "complete": False, "start_year": 2014,
                        "end_year": 2024, "series_count": 204, "registered": False,
                        "source": pipeline.API_V1, "responses": records}
            pipeline.write_json(snapshot / "manifest.json", manifest)
            original_parse = pipeline.parse_response
            calls = 0

            def interrupt_second_batch(*args):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise RuntimeError("Simulated interruption")
                return original_parse(*args)

            with patch.dict("os.environ", {}, clear=True), \
                    patch.object(pipeline, "parse_response", side_effect=interrupt_second_batch), \
                    patch.object(pipeline, "fetch_response", side_effect=AssertionError("No network in test")):
                with self.assertRaisesRegex(RuntimeError, "Simulated interruption"):
                    pipeline.collect(root, snapshot=snapshot)
            self.assertEqual(json.loads((snapshot / "manifest.json").read_text())["responses"], records)

    def test_resume_cannot_bless_a_modified_frozen_batch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data/reference").mkdir(parents=True)
            shutil.copy(pipeline.ROOT / "data/reference/states.csv", root / "data/reference/states.csv")
            mapping = pipeline.series_mapping(root)
            request = pipeline.request_plan(list(mapping), 2014, 2024)[0]
            response = {"status": "REQUEST_SUCCEEDED", "Results": {"series": [
                {"seriesID": sid, "data": [{"year": "2014", "period": "M01", "value": "3", "footnotes": [{}]}]}
                for sid in request["seriesid"]]}}
            snapshot = root / "data/raw/fixture"
            snapshot.mkdir(parents=True)
            path = snapshot / "response_01.json"
            payload = {"request": request, "response": response}
            path.write_text(json.dumps(payload))
            manifest = {"created_at_utc": "original", "complete": False, "start_year": 2014,
                        "end_year": 2024, "series_count": 204, "registered": False,
                        "source": pipeline.API_V1, "vintage_policy": "Fixture", "responses": [
                            {"file": path.name, "request": request, "monthly_rows": 25,
                             "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}]}
            (snapshot / "manifest.json").write_text(json.dumps(manifest))
            payload["response"]["Results"]["series"][0]["data"][0]["value"] = "9"
            path.write_text(json.dumps(payload))
            with patch.dict("os.environ", {}, clear=True), patch.object(pipeline, "fetch_response", side_effect=AssertionError("No network in test")):
                with self.assertRaisesRegex(ValueError, "checksum"):
                    pipeline.collect(root, snapshot=snapshot)
            self.assertEqual(json.loads((snapshot / "manifest.json").read_text()), manifest)

    def test_interrupted_test_evaluation_requires_explicit_rerun(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            for name in ["bls_pipeline.py", "train_models.py"]:
                shutil.copy(pipeline.ROOT / "src" / name, root / "src" / name)
            (root / "data/processed").mkdir(parents=True)
            pd.DataFrame(columns=["split", "month", "target_month"]).to_csv(root / "data/processed/model_table.csv", index=False)
            (root / "results").mkdir()
            (root / "results/test_evaluation_started.json").write_text('{}')
            with self.assertRaisesRegex(ValueError, "interrupted|incomplete"):
                train_models.run_models(root)

    def test_preparation_writes_readable_quality_receipt_and_calendar_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data/reference").mkdir(parents=True)
            shutil.copy(pipeline.ROOT / "data/reference/states.csv", root / "data/reference/states.csv")
            mapping = pipeline.series_mapping(root)
            values = {"unemployment_rate": "3.0", "unemployed": "300", "employed": "9700", "labor_force": "10000"}
            response = {"status": "REQUEST_SUCCEEDED", "Results": {"series": [
                {"seriesID": sid, "data": [{"year": str(y), "period": f"M{m:02d}",
                                           "value": values[measure], "footnotes": [{}]}
                                          for y in (2014, 2015) for m in range(1, 13)]}
                for sid, (_, measure) in mapping.items()]}}
            snapshot = root / "data/raw/fixture"
            snapshot.mkdir(parents=True)
            payload = {"request": {"seriesid": list(mapping)}, "response": response}
            path = snapshot / "response.json"
            path.write_text(json.dumps(payload))
            manifest = {"complete": True, "start_year": 2014, "end_year": 2015,
                        "vintage_policy": "Synthetic test only", "responses": [
                            {"file": path.name, "request": payload["request"],
                             "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}]}
            (snapshot / "manifest.json").write_text(json.dumps(manifest))
            pipeline.prepare(root, snapshot)
            quality = json.loads((root / "results/data_quality.json").read_text())
            self.assertIs(quality["passed"], True)
            self.assertEqual(quality["state_month_rows"], 51 * 24)
            model = pd.read_csv(root / "data/processed/model_table.csv")
            self.assertEqual(len(model), 51 * 9)
            self.assertEqual(model.target_month.max(), "2015-12")

    def test_request_plan_respects_anonymous_limits_and_covers_years(self):
        ids = [f"series{i}" for i in range(51)]
        requests = pipeline.request_plan(ids, 2014, 2024, registered=False)
        self.assertEqual(len(requests), 6)
        pairs = [(s, year) for r in requests for s in r["seriesid"]
                 for year in range(int(r["startyear"]), int(r["endyear"]) + 1)]
        self.assertEqual(len(pairs), len(set(pairs)))
        self.assertEqual(set(pairs), {(s, y) for s in ids for y in range(2014, 2025)})
        self.assertTrue(all(len(r["seriesid"]) <= 25 for r in requests))
        self.assertTrue(all(int(r["endyear"]) - int(r["startyear"]) < 10 for r in requests))

    def test_api_annual_average_is_not_a_thirteenth_month(self):
        sid = "LASST440000000000003"
        response = {"status": "REQUEST_SUCCEEDED", "Results": {"series": [
            {"seriesID": sid, "data": [
                {"year": "2024", "period": "M01", "value": "4.5", "footnotes": [{}]},
                {"year": "2024", "period": "M13", "value": "4.6", "footnotes": [{}]}]}]}}
        rows = pipeline.parse_response(response, {sid: ("Rhode Island", "unemployment_rate")})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["month"], "2024-01")
        self.assertEqual(rows[0]["value"], 4.5)

    def test_success_status_with_missing_series_is_not_accepted(self):
        response = {"status": "REQUEST_SUCCEEDED", "Results": {"series": []}}
        with self.assertRaisesRegex(ValueError, "series"):
            pipeline.parse_response(response, {"missing": ("Alabama", "unemployment_rate")})

    def test_api_error_is_not_treated_as_an_empty_dataset(self):
        with self.assertRaises(ValueError):
            pipeline.parse_response({"status": "REQUEST_NOT_PROCESSED", "message": ["quota"]}, {})

    def test_missing_month_does_not_turn_three_months_into_three_rows(self):
        panel = toy_panel()
        panel = panel[~((panel.state == "Alabama") & (panel.month == "2020-02"))]
        features = pipeline.make_features(panel)
        jan = features[(features.state == "Alabama") & (features.month == "2020-01")].iloc[0]
        apr = panel[(panel.state == "Alabama") & (panel.month == "2020-04")].iloc[0]
        self.assertAlmostEqual(jan.target_unemployment_rate, apr.unemployment_rate)
        self.assertEqual(jan.target_month, "2020-04")
        missing_target = features[(features.state == "Alabama") & (features.month == "2019-11")].iloc[0]
        self.assertTrue(pd.isna(missing_target.target_unemployment_rate))
        feb = features[(features.state == "Alabama") & (features.month == "2020-02")].iloc[0]
        self.assertTrue(pd.isna(feb.unemployment_rate))

    def test_history_is_per_state_and_does_not_change_with_future_data(self):
        panel = toy_panel()
        before = pipeline.make_features(panel)
        changed = panel.copy()
        changed.loc[changed.month > "2020-01", "unemployment_rate"] += 20
        after = pipeline.make_features(changed)
        cols = ["state", "month"] + pipeline.NUMERIC_FEATURES
        pd.testing.assert_frame_equal(before.loc[before.month <= "2020-01", cols],
                                      after.loc[after.month <= "2020-01", cols])
        row = before[(before.state == "Alaska") & (before.month == "2020-01")].iloc[0]
        self.assertAlmostEqual(row.ur_change_12m, .12)

    def test_block_splits_purge_unavailable_labels(self):
        features = pipeline.make_features(toy_panel())
        split = pipeline.assign_splits(features, "2020-01", "2022-01", "2019-01")
        train = split[split.split == "train"]
        val = split[split.split == "validation"]
        test = split[split.split == "test"]
        self.assertTrue((train.target_month < "2020-01").all())
        self.assertTrue((val.target_month < "2022-01").all())
        self.assertEqual(train.month.max(), "2019-09")
        self.assertEqual(val.month.max(), "2021-09")
        self.assertEqual(test.month.min(), "2022-01")
        self.assertTrue((split.groupby("month").split.nunique() == 1).all())

    def test_cv_groups_whole_months_and_purges_by_target_date(self):
        frame = pipeline.make_features(toy_panel()).dropna(subset=pipeline.NUMERIC_FEATURES)
        frame = frame[frame.month < "2022-01"].reset_index(drop=True)
        folds = pipeline.month_cv(frame, n_splits=3, test_size=12)
        self.assertEqual(len(folds), 3)
        for train_i, val_i in folds:
            train, val = frame.iloc[train_i], frame.iloc[val_i]
            self.assertTrue((train.target_month < val.month.min()).all())
            self.assertFalse(set(train.month) & set(val.month))
            for month in val.month.unique():
                self.assertEqual(set(val[val.month == month].state), {"Alabama", "Alaska"})


if __name__ == "__main__":
    unittest.main()
