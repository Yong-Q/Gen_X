"""Behavior tests: real shell/Python execution, synthetic data, no cluster jobs."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


class SmokeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="smoke test ", dir=str(ROOT / "tests"))
        self.work = Path(self.temp.name)
        self.output = self.work / "output with spaces"
        self.fixture = self.work / "synthetic fixture.json"
        self.fixture.write_text(json.dumps({"synthetic": True, "provenance": "hand-authored unit-test fixture; no model", "samples": [
            {"id": "separated", "species": ["O", "O"], "cell_A": [10, 10, 10], "positions_A": [[0, 0, 0], [3, 0, 0]]},
            {"id": "periodic_overlap", "species": ["O", "O"], "cell_A": [10, 10, 10], "positions_A": [[0.1, 0, 0], [9.9, 0, 0]]}
        ]}), encoding="utf-8")
        self.config = self.work / "config with spaces.json"
        self.data = {"schema_version": 1, "route_id": "bgmat_water", "mode": "synthetic_smoke",
                     "source_url": "https://github.com/maxschebek/bgmat", "upstream_entrypoint": "unintegrated: see upstream README",
                     "prerequisites": ["upstream environment and weights; not installed"], "model_status": "not_integrated",
                     "fixture": str(self.fixture), "qa": {"min_pair_distance_A": 0.7}}
        self.save_config()

    def tearDown(self):
        self.temp.cleanup()

    def save_config(self):
        self.config.write_text(json.dumps(self.data), encoding="utf-8")

    def call(self, script="local_smoke.sh", extra=(), env=None):
        return subprocess.run(["bash", str(ROOT / "scripts" / script), "--config", str(self.config),
                               "--output-root", str(self.output), "--run-id", "test_run"] + list(extra),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
                              env=env, cwd=str(ROOT))

    def read_manifest(self):
        return json.loads((self.output / "test_run" / "manifest.json").read_text())

    def test_unknown_route_rejected_before_run_creation(self):
        self.data["route_id"] = "invented_route"
        self.save_config()
        result = self.call()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown route", result.stderr.lower())
        self.assertFalse(self.output.exists())

    def test_missing_required_metadata_rejected(self):
        del self.data["prerequisites"]
        self.save_config()
        result = self.call()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("prerequisites", result.stderr)
        self.assertFalse(self.output.exists())

    def test_paths_with_spaces_and_periodic_qa_are_preserved(self):
        result = self.call()
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = self.read_manifest()
        self.assertEqual(manifest["status"], "completed")
        self.assertEqual(manifest["model_inference"], "not_run")
        self.assertEqual(manifest["scientific_validation"], "not_run")
        self.assertEqual(manifest["summary"], {"samples": 2, "qa_pass": 1, "candidates": 1})
        run_dir = self.output / "test_run"
        candidates = [json.loads(line) for line in (run_dir / "candidates.jsonl").read_text().splitlines()]
        self.assertEqual(candidates[0]["sample_id"], "periodic_overlap")
        self.assertTrue(candidates[0]["synthetic"])
        self.assertEqual(candidates[0]["physical_validation"], "not_run")
        self.assertIn("hand-authored", candidates[0]["provenance"])
        self.assertAlmostEqual(candidates[0]["minimum_pair_distance_A"], 0.2)

    def test_duplicate_run_refused_without_altering_results(self):
        first = self.call()
        self.assertEqual(first.returncode, 0, first.stderr)
        before = (self.output / "test_run" / "manifest.json").read_bytes()
        second = self.call()
        self.assertNotEqual(second.returncode, 0)
        self.assertIn("already exists", second.stderr)
        self.assertEqual((self.output / "test_run" / "manifest.json").read_bytes(), before)

    def test_worker_subprocess_failure_cannot_be_success(self):
        self.fixture.write_text("{malformed JSON", encoding="utf-8")
        result = self.call()
        self.assertNotEqual(result.returncode, 0)
        manifest = self.read_manifest()
        self.assertEqual(manifest["status"], "failed")
        self.assertNotEqual(manifest["exit_code"], 0)
        self.assertFalse((self.output / "test_run" / "candidates.jsonl").exists())

    def test_dry_run_validates_but_creates_no_results(self):
        result = self.call(extra=["--dry-run"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "dry_run")
        self.assertFalse(self.output.exists())

    def test_slurm_dry_run_has_only_small_cpu_request(self):
        result = self.call("submit_smoke.sh", ["--dry-run", "--partition", "debug"])
        self.assertEqual(result.returncode, 0, result.stderr)
        command = json.loads(result.stdout)["command"]
        self.assertIn("--cpus-per-task=1", command)
        self.assertIn("--mem=128M", command)
        self.assertIn("--time=00:02:00", command)
        self.assertFalse(any("gpu" in item or "gres" in item for item in command))
        self.assertFalse(self.output.exists())

    def test_sbatch_failure_propagates_and_records_failure(self):
        bin_dir = self.work / "fake cluster bin"
        bin_dir.mkdir()
        stub = bin_dir / "sbatch"
        stub.write_text("#!/bin/sh\nprintf 'test scheduler rejection\\n' >&2\nexit 17\n")
        stub.chmod(0o755)
        env = dict(os.environ)
        env["PATH"] = str(bin_dir) + os.pathsep + env["PATH"]
        result = self.call("submit_smoke.sh", env=env)
        self.assertEqual(result.returncode, 17, result.stderr)
        self.assertEqual(self.read_manifest()["status"], "submission_failed")

    def test_run_id_traversal_rejected(self):
        result = self.call(extra=["--run-id", "../escaped"])
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.work / "escaped").exists())
        self.assertFalse(self.output.exists())

    def test_scientific_execution_mode_rejected(self):
        self.data["mode"] = "train"
        self.save_config()
        result = self.call()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("synthetic_smoke", result.stderr)

    def test_config_snapshot_uses_the_exact_validated_bytes(self):
        spec = importlib.util.spec_from_file_location("genx_smoke", ROOT / "scripts" / "smoke.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        validated_bytes = self.config.read_bytes()
        original_prepare = module.prepare

        def change_original_after_validation(*args, **kwargs):
            # Simulate an editor saving the input after validation, before staging.
            self.data["qa"]["min_pair_distance_A"] = 9.0
            self.save_config()
            return original_prepare(*args, **kwargs)

        args = SimpleNamespace(config=str(self.config), output_root=str(self.output), run_id="test_run",
                               action="local", dry_run=False)
        with mock.patch.object(module, "prepare", side_effect=change_original_after_validation):
            self.assertEqual(module.execute(args), 0)
        self.assertEqual((self.output / "test_run" / "config.input.json").read_bytes(), validated_bytes)
        self.assertEqual(self.read_manifest()["summary"]["qa_pass"], 1)

    def test_modified_resolved_config_is_refused_before_qa(self):
        bin_dir = self.work / "fake cluster bin"
        bin_dir.mkdir()
        stub = bin_dir / "sbatch"
        stub.write_text("#!/bin/sh\nprintf '99999999\\n'\n")
        stub.chmod(0o755)
        env = dict(os.environ)
        env["PATH"] = str(bin_dir) + os.pathsep + env["PATH"]
        submitted = self.call("submit_smoke.sh", env=env)
        self.assertEqual(submitted.returncode, 0, submitted.stderr)
        directory = self.output / "test_run"
        resolved = directory / "config.resolved.json"
        changed = json.loads(resolved.read_text())
        changed["qa"]["min_pair_distance_A"] = 9.0
        resolved.write_text(json.dumps(changed))
        result = subprocess.run(["/usr/bin/python3", str(ROOT / "scripts" / "smoke.py"), "worker", "--run-dir", str(directory)],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("resolved config changed", result.stderr)
        self.assertFalse((directory / "qa.jsonl").exists())
        self.assertEqual(self.read_manifest()["status"], "failed")

    def test_slurm_preserves_logs_and_disables_requeue(self):
        result = self.call("submit_smoke.sh", ["--dry-run"])
        self.assertEqual(result.returncode, 0, result.stderr)
        command = json.loads(result.stdout)["command"]
        self.assertIn("--open-mode=append", command)
        self.assertIn("--no-requeue", command)

    def test_direct_worker_refuses_resolved_path_outside_workspace(self):
        outside = ROOT.parent / ("nonexistent-" + self.work.name)
        link = self.work / "outside-link"
        link.symlink_to(outside, target_is_directory=True)
        result = subprocess.run(["/usr/bin/python3", str(ROOT / "scripts" / "smoke.py"), "worker", "--run-dir", str(link)],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("inside this project workspace", result.stderr)
        self.assertFalse(outside.exists())


if __name__ == "__main__":
    unittest.main()
