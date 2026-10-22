# CPU smoke execution record

Executed on 2026-10-22 in `/home/qiuyong/bza/H2O/Gen_X`. Scope: Bash orchestration, configuration checks, synthetic geometry QA and candidate queue, an initial Slurm CPU job and a second CPU job verifying review fixes. No external generator, potential inference, GPU computation, training, model/data download, or dependency installation was performed. Historical runs are preserved; the reviewed-version results are identified separately below.

## Entry points

```bash
# Lightweight software smoke; a unique run ID is generated when omitted.
bash scripts/local_smoke.sh --config configs/dm2_smoke.json
bash scripts/local_smoke.sh --config configs/bgmat_smoke.json
bash scripts/local_smoke.sh --config configs/mbpol_water_smoke.json

# Validate inputs and print the argv array without creating a run or submitting.
bash scripts/submit_smoke.sh --config configs/dm2_smoke.json --partition debug --dry-run

# Submit a new, CPU-only smoke. This creates a real Slurm job.
bash scripts/submit_smoke.sh --config configs/dm2_smoke.json --partition debug

# Tests use only Python's standard library; no scheduler submission occurs.
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest discover -s tests -v
```

The Bash launchers default to `/usr/bin/python3`; `GENX_PYTHON` can select an absolute compatible interpreter. The submitter carries that absolute interpreter path into the batch job. Python 3.6 or newer is required by the implementation; the executed login and compute runtimes were Python 3.12.15 and 3.12.13, respectively. No claim of execution on Python 3.6 is made.

Use `--output-root PATH` inside this repository and optional `--run-id NAME` to choose output names. Existing run directories are rejected, even if empty or previously failed. Paths containing spaces are passed as individual arguments. Configuration fields are not evaluated as shell code. Each run snapshots its input configuration and fixture, records hashes and the exact command array, and creates artifacts with exclusive file creation. The reviewed implementation derives the original and resolved snapshots from the same validated input bytes and verifies the exact resolved-config hash before parsing those bytes for execution. The worker also checks resolved-path containment before reading or writing run files, including when invoked directly. Worker replay is refused. Slurm writes its own scheduler stdout/stderr into the newly reserved run directory.

The Slurm request uses the generic `debug` partition, one node, one task, one CPU, 128 MB and a two-minute time limit. It does not bind to a specific node or request GPU resources. Inherited `SBATCH_*` variables are removed before invoking `sbatch`, and the batch job receives `--export=NONE`; the batch shell also clears `PYTHONHOME`, `PYTHONPATH` and `LD_LIBRARY_PATH`. The reviewed version explicitly requests `--open-mode=append` and `--no-requeue` to preserve scheduler logs and avoid automatic replay of a worker that refuses replay. All output goes directly to the shared project filesystem; node-local scratch is not used.

## Tests and local execution

The initial ten behavior tests cover unknown route, missing required metadata, paths with spaces and periodic overlap detection, output collision, worker subprocess failure, local dry-run, small CPU Slurm dry-run, scheduler rejection, run-ID path traversal, and rejection of a training mode. The scheduler-rejection test uses a deliberately failing local `sbatch` substitute and checks exit status 17 and a failure manifest; it does not contact the cluster.

Initial test run before launcher implementation: 10 tests, 8 failures and 1 error (missing launchers/manifest); one negative-only traversal test already passed. The saved [initial red log](../runs/verification-20261022/initial-red.log) makes that distinction explicit. After initial implementation: all 10 passed in the [green log](../runs/verification-20261022/green.log). Review added four regression tests: editing the original config between validation and staging, modifying the resolved config before execution, Slurm append/no-requeue flags, and direct worker access via a symlink resolving outside the workspace. All four failed before the fixes ([regression red](../runs/review-fix-20261022/regression-red.log)); the full revised suite passes **14/14** ([regression green](../runs/review-fix-20261022/regression-green.log)). Tests create temporary directories inside `tests/` and remove only those task-owned test directories on completion.

Executed local commands:

```bash
bash scripts/local_smoke.sh --config configs/dm2_smoke.json --run-id local_dm2_20261022
bash scripts/local_smoke.sh --config configs/bgmat_smoke.json --run-id local_bgmat_20261022
bash scripts/local_smoke.sh --config configs/mbpol_water_smoke.json --run-id local_mbpol_20261022
bash scripts/submit_smoke.sh --config configs/dm2_smoke.json --run-id dryrun_dm2_20261022 --dry-run
bash -n scripts/local_smoke.sh scripts/submit_smoke.sh scripts/slurm_smoke.sh
```

All three local runs returned zero and produced three synthetic QA records, one illustrative QA pass and two flagged candidates. Evidence:

| Route | Manifest | Meaning |
|---|---|---|
| DM2 | [local DM2 manifest](../runs/local_dm2_20261022/manifest.json) | Hand-authored silicon coordinates; no DM2 invocation |
| bgmat | [local bgmat manifest](../runs/local_bgmat_20261022/manifest.json) | Hand-authored single-bead coordinates; no bgmat invocation |
| DNN@MB-pol water | [local water manifest](../runs/local_mbpol_20261022/manifest.json) | Hand-authored O/H coordinates; no potential or generator invocation |

The [Slurm dry-run record](../runs/verification-20261022/slurm-dry-run.json) stores the planned argument array. It did not create `runs/dryrun_dm2_20261022` or submit a job. Bash syntax checks returned zero.

## Original Slurm execution

The initial implementation submitted one actual smoke job, before independent-review fixes:

```bash
bash scripts/submit_smoke.sh --config configs/dm2_smoke.json --run-id slurm_dm2_20261022 --partition debug
squeue -j 96379 -o '%.18i %.9P %.20j %.8T %.10M %.6D %R'
sacct -j 96379 --format=JobID,JobName,Partition,AllocCPUS,ReqMem,Elapsed,State,ExitCode,NodeList,ReqTRES,AllocTRES -P
scontrol show job 96379
```

| Field | Observed result |
|---|---|
| Job ID | `96379` |
| Partition / allocated node | `debug` / `node04` (scheduler selected) |
| Allocation | 1 CPU, 128 MB; no GPU TRES |
| Requested limit | `00:02:00` |
| Accounted elapsed time | `00:00:05` |
| Job / batch / extern state | `COMPLETED` |
| Job / batch / extern exit code | `0:0` |
| Worker finish time | `2026-10-22T07:50:38.519045+00:00` (15:50:38 Asia/Shanghai) |
| Worker result | 3 synthetic samples; 1 QA pass; 2 flagged candidates |

Evidence: [submission record](../runs/slurm_dm2_20261022/submission.json), [accounting](../runs/slurm_dm2_20261022/sacct.txt), [scheduler details](../runs/slurm_dm2_20261022/scontrol.txt), [stdout](../runs/slurm_dm2_20261022/slurm-96379.out), [stderr](../runs/slurm_dm2_20261022/slurm-96379.err), [terminal manifest](../runs/slurm_dm2_20261022/manifest.json), and [candidate queue](../runs/slurm_dm2_20261022/candidates.jsonl). Scheduler stderr was empty. The manifest records both Python versions and the worker host; accounting independently confirms successful completion. Existing jobs were inspected only and not modified.

This run remains a valid successful smoke of its recorded implementation. Its script hash differs from the reviewed current script. The exact [original script snapshot](../runs/review-fix-20261022/smoke-before-review.py) retains SHA-256 `f4ce17d74d62d8cd9cedde1ba72716615fa9fe95afb4fbdb6fcb8ac63cd5fff1`, matching the original manifests. No earlier results or logs were modified during the review fixes.

## Reviewed-version execution

After the three review fixes and the 14-test passing suite, all three route smokes were run again into new directories:

```bash
bash scripts/local_smoke.sh --config configs/dm2_smoke.json --run-id local_dm2_review_20261022
bash scripts/local_smoke.sh --config configs/bgmat_smoke.json --run-id local_bgmat_review_20261022
bash scripts/local_smoke.sh --config configs/mbpol_water_smoke.json --run-id local_mbpol_review_20261022
bash scripts/submit_smoke.sh --config configs/dm2_smoke.json --run-id dryrun_dm2_review_20261022 --dry-run
bash scripts/submit_smoke.sh --config configs/dm2_smoke.json --run-id slurm_dm2_review_20261022 --partition debug
sacct -j 96390 --format=JobID,JobName,Partition,AllocCPUS,ReqMem,Elapsed,State,ExitCode,NodeList,ReqTRES,AllocTRES -P
scontrol show job 96390
```

The revised [DM2](../runs/local_dm2_review_20261022/manifest.json), [bgmat](../runs/local_bgmat_review_20261022/manifest.json), and [water](../runs/local_mbpol_review_20261022/manifest.json) local manifests all report successful software smoke with three synthetic records, one illustrative QA pass, and two candidates. The revised [dry-run command](../runs/review-fix-20261022/slurm-dry-run.json) includes both `--open-mode=append` and `--no-requeue` and created no dry-run directory.

One additional actual CPU job verified the final script; the task therefore submitted **two actual CPU jobs in total**:

| Field | Reviewed-version result |
|---|---|
| Job ID | `96390` |
| Partition / allocated node | `debug` / `node04` (scheduler selected) |
| Allocation | 1 CPU, 128 MB; no GPU TRES |
| Requested limit | `00:02:00` |
| Accounted elapsed time | `00:00:04` |
| Job / batch / extern state | `COMPLETED` |
| Job / batch / extern exit code | `0:0` |
| Requeue setting | `Requeue=0` |
| Worker finish time | `2026-10-22T08:00:07.479414+00:00` (16:00:07 Asia/Shanghai) |
| Worker result | 3 synthetic samples; 1 QA pass; 2 flagged candidates |

The current script SHA-256 is `7fbcdbb654014889c910bc65f5d2388a7e9076405a66b5bba97a823164a89069`, matching all four revised-version manifests. The Slurm manifest also records resolved-config SHA-256 `31b9c844417a5904bc53cd120617eb0060349cfe22096a6a315e77592e48466c`.

Evidence: [submission record](../runs/slurm_dm2_review_20261022/submission.json), [command array](../runs/slurm_dm2_review_20261022/command.json), [accounting](../runs/slurm_dm2_review_20261022/sacct.txt), [scheduler details](../runs/slurm_dm2_review_20261022/scontrol.txt), [stdout](../runs/slurm_dm2_review_20261022/slurm-96390.out), [stderr](../runs/slurm_dm2_review_20261022/slurm-96390.err), [terminal manifest](../runs/slurm_dm2_review_20261022/manifest.json), and [candidate queue](../runs/slurm_dm2_review_20261022/candidates.jsonl). Scheduler stderr was empty. Automatic restart behavior was not deliberately triggered; the accepted scheduler request, `Requeue=0`, and regression test verify the configured prevention measures.

## Interpretation and limits

`completed` describes the software smoke. Every manifest explicitly retains `model_inference: not_run` and `scientific_validation: not_run`. Route configurations provide upstream sources, model roles, unresolved entrypoints and prerequisites. They do not provide runnable adapters for the cited external models. DNN@MB-pol is registered as a potential teacher for a future all-atom generator; it is not represented as a generator.

The illustrative QA computes minimum pair distance under orthorhombic periodic boundaries and flags coordinates outside the primary cell. The common 0.7 Å threshold is a test parameter, not a validated element-specific or molecular acceptance criterion. Passing these checks does not establish physical validity. Fixtures and every QA/candidate record carry explicit synthetic provenance; bgmat bead data are not called all-atom water. The queue priority is the count of QA flags, not uncertainty, model error, Boltzmann weight, or acquisition value. Candidate actions are `manual_review_only`; no DFT, labeling, retraining, simulation or external submission is triggered by the queue.

Pending scientific milestones: pin and review upstream code/weights/licenses; establish runnable inference environments and unit/species contracts; reproduce published examples; evaluate energy/forces and distribution/ensemble observables; design calibrated candidate selection and separate potential/generator feedback loops. Those stages need their own successful run evidence.
