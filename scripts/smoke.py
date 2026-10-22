#!/usr/bin/env python3
"""CPU-only orchestration and synthetic QA demo. Python >=3.6; stdlib only.

No external model, dynamics, force/energy evaluation, or calibrated uncertainty
is implemented. Routes are metadata for later integration, not model adapters.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import uuid


ROOT = Path(__file__).resolve().parents[1]
ROUTES = {"dm2_amorphous", "bgmat_water", "mbpol_water"}


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path, value):
    # Run artifacts are append-only: each named file is created once.
    with Path(path).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_config(path, source_bytes=None):
    if source_bytes is None:
        source_bytes = Path(path).read_bytes()
    config = json.loads(source_bytes.decode("utf-8"))
    if not isinstance(config, dict):
        raise ValueError("config must be an object")
    required = ["schema_version", "route_id", "mode", "source_url", "upstream_entrypoint",
                "prerequisites", "model_status", "fixture", "qa"]
    for key in required:
        if key not in config:
            raise ValueError("missing required config field: " + key)
    if type(config["schema_version"]) is not int or config["schema_version"] != 1:
        raise ValueError("schema_version must be 1")
    if not isinstance(config["route_id"], str) or config["route_id"] not in ROUTES:
        raise ValueError("unknown route: " + str(config["route_id"]))
    if config["mode"] != "synthetic_smoke":
        raise ValueError("only mode=synthetic_smoke is implemented")
    if config["model_status"] != "not_integrated":
        raise ValueError("model_status must be not_integrated")
    for key in ["source_url", "upstream_entrypoint", "fixture"]:
        if not isinstance(config[key], str) or not config[key].strip():
            raise ValueError(key + " must be a nonempty string")
    if not config["source_url"].startswith("https://"):
        raise ValueError("source_url must be an HTTPS source")
    if not isinstance(config["prerequisites"], list) or not config["prerequisites"] or not all(
            isinstance(item, str) and item.strip() for item in config["prerequisites"]):
        raise ValueError("prerequisites must be a nonempty list of strings")
    qa = config["qa"]
    if not isinstance(qa, dict) or not finite_number(qa.get("min_pair_distance_A")) or qa["min_pair_distance_A"] <= 0:
        raise ValueError("qa.min_pair_distance_A must be finite and positive")
    fixture = (Path(path).resolve().parent / config["fixture"]).resolve()
    if not fixture.is_file():
        raise ValueError("fixture file not found: " + str(fixture))
    return config, fixture, source_bytes


def run_path(args):
    run_id = args.run_id or (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:10])
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,100}", run_id):
        raise ValueError("run-id must contain only letters, digits, underscore, dot or hyphen; no path separators")
    output = Path(args.output_root).resolve()
    if output != ROOT and ROOT not in output.parents:
        raise ValueError("output-root must be inside this project workspace")
    destination = output / run_id
    if destination.exists():
        raise ValueError("run directory already exists: " + str(destination))
    return destination


def prepare(args, config, fixture, destination, config_bytes):
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        destination.mkdir()
    except FileExistsError:
        raise ValueError("run directory already exists: " + str(destination))
    with (destination / "config.input.json").open("xb") as handle:
        handle.write(config_bytes)
    with (destination / "fixture.input.json").open("xb") as handle:
        handle.write(fixture.read_bytes())
    snapshot = dict(config)
    snapshot["fixture"] = "fixture.input.json"
    write_json(destination / "config.resolved.json", snapshot)
    launch = {"schema_version": 1, "run_id": destination.name, "created_utc": timestamp(),
              "route_id": config["route_id"], "execution": args.action, "synthetic": True,
              "config_source": str(Path(args.config).resolve()), "fixture_source": str(fixture),
              "config_sha256": digest(destination / "config.input.json"),
              "resolved_config_sha256": digest(destination / "config.resolved.json"),
              "fixture_sha256": digest(destination / "fixture.input.json"),
              "script_sha256": digest(Path(__file__)), "python_submit": sys.version,
              "model_inference": "not_run", "scientific_validation": "not_run"}
    write_json(destination / "launch.json", launch)
    return launch


def terminal_manifest(destination, launch, status, code, **details):
    manifest = dict(launch)
    manifest.update({"status": status, "exit_code": code, "finished_utc": timestamp(),
                     "hostname": socket.gethostname(), "python_worker": sys.version,
                     "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
                     "slurm_cpus_per_task": os.environ.get("SLURM_CPUS_PER_TASK"),
                     "model_inference": "not_run", "scientific_validation": "not_run"})
    manifest.update(details)
    write_json(destination / "manifest.json", manifest)


def qa_records(config, fixture):
    data = read_json(fixture)
    if not isinstance(data, dict) or data.get("synthetic") is not True:
        raise ValueError("fixture must explicitly declare synthetic=true")
    provenance = data.get("provenance")
    if not isinstance(provenance, str) or not provenance.strip():
        raise ValueError("synthetic fixture requires provenance")
    samples = data.get("samples")
    if not isinstance(samples, list) or not samples:
        raise ValueError("fixture requires a nonempty samples list")
    records, seen = [], set()
    for sample in samples:
        if not isinstance(sample, dict) or not isinstance(sample.get("id"), str) or not sample["id"]:
            raise ValueError("each sample requires a string id")
        if sample["id"] in seen:
            raise ValueError("duplicate sample id: " + sample["id"])
        seen.add(sample["id"])
        species, cell, positions = sample.get("species"), sample.get("cell_A"), sample.get("positions_A")
        if not isinstance(cell, list) or len(cell) != 3 or not all(finite_number(v) and v > 0 for v in cell):
            raise ValueError("cell_A requires three finite positive orthorhombic lengths")
        if not isinstance(species, list) or len(species) < 2 or not all(isinstance(v, str) and v for v in species):
            raise ValueError("species requires at least two labels for the pair-distance demo")
        if not isinstance(positions, list) or len(positions) != len(species) or not all(
                isinstance(row, list) and len(row) == 3 and all(finite_number(v) for v in row) for row in positions):
            raise ValueError("positions_A must be a finite N by 3 array matching species")
        distances = []
        for i in range(len(positions)):
            for j in range(i):
                squared = 0.0
                for axis in range(3):
                    delta = positions[i][axis] - positions[j][axis]
                    delta -= cell[axis] * round(delta / cell[axis])
                    squared += delta * delta
                distances.append(math.sqrt(squared))
        minimum = min(distances)
        reasons = []
        if minimum < config["qa"]["min_pair_distance_A"]:
            reasons.append("pair_distance_below_illustrative_threshold")
        if any(not 0 <= row[a] < cell[a] for row in positions for a in range(3)):
            reasons.append("coordinates_outside_primary_cell")
        records.append({"sample_id": sample["id"], "route_id": config["route_id"], "synthetic": True,
                        "provenance": provenance, "physical_validation": "not_run", "qa_pass": not reasons,
                        "minimum_pair_distance_A": minimum, "reasons": reasons,
                        "illustrative_priority": len(reasons), "priority_meaning": "count of QA flags; not calibrated uncertainty",
                        "next_action": "manual_review_only"})
    return records


def worker(destination):
    destination = Path(destination).resolve()
    if destination != ROOT and ROOT not in destination.parents:
        raise ValueError("worker run-dir must be inside this project workspace")
    launch = read_json(destination / "launch.json")
    # Refuse replay before any artifacts could be modified.
    with (destination / "worker.started.json").open("x", encoding="utf-8") as handle:
        json.dump({"started_utc": timestamp(), "pid": os.getpid()}, handle)
    try:
        resolved_path = destination / "config.resolved.json"
        resolved_bytes = resolved_path.read_bytes()
        if hashlib.sha256(resolved_bytes).hexdigest() != launch["resolved_config_sha256"]:
            raise ValueError("resolved config changed since launch snapshot")
        config, fixture, _ = validate_config(resolved_path, resolved_bytes)
        if digest(fixture) != launch["fixture_sha256"]:
            raise ValueError("fixture changed since launch snapshot")
        if digest(Path(__file__)) != launch["script_sha256"]:
            raise ValueError("worker script changed after submission; use a new run")
        records = qa_records(config, fixture)
        candidates = sorted((r for r in records if not r["qa_pass"]), key=lambda r: (-r["illustrative_priority"], r["sample_id"]))
        for name, values in [("qa.jsonl", records), ("candidates.jsonl", candidates)]:
            with (destination / name).open("x", encoding="utf-8") as handle:
                for value in values:
                    handle.write(json.dumps(value, sort_keys=True, allow_nan=False) + "\n")
        summary = {"samples": len(records), "qa_pass": len(records) - len(candidates), "candidates": len(candidates)}
        terminal_manifest(destination, launch, "completed", 0, summary=summary,
                          artifact_sha256={name: digest(destination / name) for name in ["qa.jsonl", "candidates.jsonl"]})
        print(json.dumps({"status": "completed", "run_dir": str(destination), "summary": summary}))
        return 0
    except Exception as error:
        terminal_manifest(destination, launch, "failed", 1, error=str(error))
        print("worker failed: " + str(error), file=sys.stderr)
        return 1


def slurm_command(args, destination):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.partition):
        raise ValueError("partition must be a simple partition name")
    return ["sbatch", "--parsable", "--partition=" + args.partition, "--job-name=genx_cpu_smoke",
            "--nodes=1", "--ntasks=1", "--cpus-per-task=1", "--mem=128M", "--time=00:02:00",
            "--open-mode=append", "--no-requeue",
            "--export=NONE", "--chdir=" + str(ROOT), "--output=" + str(destination / "slurm-%j.out"),
            "--error=" + str(destination / "slurm-%j.err"), str(ROOT / "scripts" / "slurm_smoke.sh"),
            sys.executable, str(Path(__file__).resolve()), str(destination)]


def execute(args):
    config, fixture, config_bytes = validate_config(args.config)
    destination = run_path(args)
    command = (slurm_command(args, destination) if args.action == "submit" else
               [sys.executable, str(Path(__file__).resolve()), "worker", "--run-dir", str(destination)])
    if args.dry_run:
        print(json.dumps({"status": "dry_run", "route_id": config["route_id"], "run_dir": str(destination),
                          "command": command, "synthetic": True, "model_inference": "not_run", "scientific_validation": "not_run"}))
        return 0
    launch = prepare(args, config, fixture, destination, config_bytes)
    write_json(destination / "command.json", {"argv": command, "shell": False})
    # Do not allow inherited SBATCH_* variables to add resources or redirect logs.
    environment = {key: value for key, value in os.environ.items() if not key.startswith("SBATCH_")}
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                universal_newlines=True, env=environment)
        for name, content in [("launcher.stdout.log", result.stdout), ("launcher.stderr.log", result.stderr)]:
            with (destination / name).open("x", encoding="utf-8") as handle:
                handle.write(content)
        code = result.returncode if result.returncode >= 0 else 128 - result.returncode
        if code:
            if not (destination / "manifest.json").exists():
                terminal_manifest(destination, launch, "submission_failed" if args.action == "submit" else "failed", code,
                                  error=result.stderr.strip())
            print(result.stderr, file=sys.stderr, end="")
            return code
        if args.action == "submit":
            job_id = result.stdout.strip().split(";")[0]
            if not job_id.isdigit():
                raise ValueError("sbatch returned no parseable job id; inspect launcher logs before retrying")
            write_json(destination / "submission.json", {"job_id": job_id, "submitted_utc": timestamp(),
                                                       "status": "submitted", "resources": "1 CPU, 128M, 2 minutes, no GPU"})
            print(json.dumps({"status": "submitted", "job_id": job_id, "run_dir": str(destination)}))
        else:
            manifest = read_json(destination / "manifest.json")
            if manifest["status"] != "completed" or manifest["exit_code"] != 0:
                raise ValueError("worker exited zero without a completed manifest")
            print(result.stdout, end="")
        return 0
    except Exception as error:
        if not (destination / "manifest.json").exists():
            terminal_manifest(destination, launch, "submission_failed" if args.action == "submit" else "failed", 1, error=str(error))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action")
    for action in ["local", "submit"]:
        command = commands.add_parser(action)
        command.add_argument("--config", required=True)
        command.add_argument("--output-root", default=str(ROOT / "runs"))
        command.add_argument("--run-id")
        command.add_argument("--dry-run", action="store_true")
        if action == "submit":
            command.add_argument("--partition", default="debug")
    command = commands.add_parser("worker")
    command.add_argument("--run-dir", required=True)
    args = parser.parse_args()
    try:
        if args.action == "worker":
            return worker(args.run_dir)
        if args.action in ["local", "submit"]:
            return execute(args)
        parser.error("an action is required")
    except Exception as error:
        print("error: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
