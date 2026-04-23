"""
Job store — reads and writes jobs.json.

Phase 2 reads jobs from Phase 1's jobs.json.
The file location is configured via the JOBS_FILE_PATH environment variable
(set by the Phase 2 Streamlit app before launching pytest).

If JOBS_FILE_PATH is not set, falls back to this project's own
data-driven-files/jobs/jobs.json (useful for standalone testing).

Record shape:
{
    "run_id":              "a3f9c21b",
    "username":            "user@company.com",
    "password":            "xxxx",
    "pay_period_start":    "2026-04-06",
    "pay_period_end":      "2026-04-12",
    "timesheet_file":      "monday06april2026.xlsx",
    "phase1_completed_at": "2026-04-07T08:32:00",
    "status":              "WAITING"   # WAITING | COMPLETE | FAILED
}
"""

from __future__ import annotations

import json
import os as _os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


# ── Path resolution ────────────────────────────────────────────────────────────
# JOBS_FILE_PATH env var: set by Phase 2 Streamlit app to point at Phase 1's file.
# Fallback: shared/ → timesheets/ → e2e/ → tests/ → root (payroll_phase2/)
_JOBS_FILE_ENV = _os.environ.get("JOBS_FILE_PATH", "").strip()
if _JOBS_FILE_ENV:
    _JOBS_FILE = Path(_JOBS_FILE_ENV)
else:
    _PROJECT_ROOT = Path(__file__).parents[4]
    _JOBS_FILE    = _PROJECT_ROOT / "data-driven-files" / "jobs" / "jobs.json"


# ============================================================================
# INTERNAL HELPERS
# ============================================================================

def _load() -> list[dict]:
    if not _JOBS_FILE.exists():
        return []
    with open(_JOBS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(jobs: list[dict]) -> None:
    _JOBS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(_JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2)


# ============================================================================
# PUBLIC API
# ============================================================================

def write_job(
    username: str,
    password: str,
    pay_period_start: str,
    pay_period_end: str,
    timesheet_file: str,
) -> str:
    """Append a new WAITING job. Returns the generated run_id."""
    run_id = uuid.uuid4().hex[:8]
    jobs = _load()
    jobs.append({
        "run_id":              run_id,
        "username":            username,
        "password":            password,
        "pay_period_start":    pay_period_start,
        "pay_period_end":      pay_period_end,
        "timesheet_file":      timesheet_file,
        "phase1_completed_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "status":              "WAITING",
    })
    _save(jobs)
    print(f"[INFO] Job written  run_id={run_id}  username={username}")
    return run_id


def list_jobs(status: Optional[str] = None) -> list[dict]:
    """Return all jobs, optionally filtered by status."""
    jobs = _load()
    if status:
        return [j for j in jobs if j.get("status") == status]
    return jobs


def get_job(run_id: str) -> Optional[dict]:
    """Return a single job by run_id, or None if not found."""
    return next((j for j in _load() if j["run_id"] == run_id), None)


def mark_complete(run_id: str) -> None:
    jobs = _load()
    for job in jobs:
        if job["run_id"] == run_id:
            job["status"] = "COMPLETE"
            job["phase2_completed_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            break
    _save(jobs)
    print(f"[INFO] Job {run_id} marked COMPLETE")


def mark_failed(run_id: str, reason: str = "") -> None:
    jobs = _load()
    for job in jobs:
        if job["run_id"] == run_id:
            job["status"] = "FAILED"
            job["failure_reason"] = reason
            job["phase2_completed_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            break
    _save(jobs)
    print(f"[INFO] Job {run_id} marked FAILED -- {reason}")


# ============================================================================
# INTERACTIVE SELECTOR  (used by Phase 2 test at startup)
# ============================================================================

def prompt_job_selection() -> dict:
    """
    Show a numbered menu of all jobs and let the user pick one.
    If PAYROLL_RUN_ID is set (CI / Streamlit automation), skip the menu.

    Returns the selected job dict.
    Raises RuntimeError if no jobs exist or the selection is invalid.
    """
    import os

    env_run_id = os.environ.get("PAYROLL_RUN_ID", "").strip()
    if env_run_id:
        job = get_job(env_run_id)
        if not job:
            raise RuntimeError(f"PAYROLL_RUN_ID={env_run_id!r} not found in {_JOBS_FILE}")
        print(f"[INFO] Using PAYROLL_RUN_ID from environment: {env_run_id}")
        return job

    jobs = _load()
    if not jobs:
        raise RuntimeError(f"No jobs found in {_JOBS_FILE}. Run Phase 1 first.")

    print("\n" + "=" * 72)
    print("  Available payroll runs")
    print("=" * 72)
    print(f"  {'#':<4} {'Username':<30} {'Pay Period':<26} {'Status'}")
    print("  " + "-" * 68)

    for i, job in enumerate(jobs, start=1):
        period = f"{job.get('pay_period_start', '?')} to {job.get('pay_period_end', '?')}"
        status = job.get("status", "?")
        status_label = f"[{status}]" if status != "WAITING" else status
        print(f"  {i:<4} {job.get('username', '?'):<30} {period:<26} {status_label}")

    print("=" * 72)

    while True:
        raw = input("\nEnter number to run: ").strip()
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(jobs):
                selected = jobs[idx]
                print(
                    f"\n[INFO] Selected: #{idx + 1}  "
                    f"{selected['username']}  "
                    f"{selected.get('pay_period_start')} to {selected.get('pay_period_end')}\n"
                )
                return selected
        print(f"  Invalid selection -- enter a number between 1 and {len(jobs)}")
