# Copyright (c) 2025 Samuele Stronati
# SPDX-License-Identifier: MIT

"""Subprocess management for running simulations."""

import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from ui.lib.state import PROJECT_ROOT, RUNS_DIR, write_config_yaml, write_meta

# Maximum wall-clock time before killing a stuck subprocess (30 minutes)
SUBPROCESS_TIMEOUT_SECONDS = 30 * 60

PROGRESS_RE = re.compile(
    r"Step\s+(\d+)/(\d+)\s*\|\s*tumor=(\d+)\s+agents=(\d+)\s+glucose=([\d.]+)"
)


def make_run_id(seed: int) -> str:
    """Generate a unique run identifier from the current timestamp and seed."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{ts}_seed{seed}"


def start_simulation(params: dict, snapshot_interval: int = 0) -> dict:
    """Launch simulation subprocess and return run context dict.

    Returns:
        {run_id, run_dir, config_path, process, start_time}
    """
    seed = params.get("random_seed", 1)
    run_id = make_run_id(seed)
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    config_path = run_dir / "config.yaml"
    write_config_yaml(params, config_path)

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    if shutil.which("mpirun"):
        cmd = [
            "mpirun", "-n", "1",
            sys.executable, "run.py",
            "--config", str(config_path),
            "--progress", "10",
        ]
    else:
        cmd = [
            sys.executable, "run.py",
            "--config", str(config_path),
            "--progress", "10",
        ]

    if snapshot_interval > 0:
        cmd.extend(["--snapshot", str(snapshot_interval)])

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=str(PROJECT_ROOT),
        env=env,
        text=True,
        bufsize=1,
    )

    return {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "config_path": str(config_path),
        "process": proc,
        "start_time": time.time(),
    }


def parse_progress_line(line: str) -> dict | None:
    """Parse a progress line, return {step, max_steps, tumor, agents, glucose} or None."""
    m = PROGRESS_RE.search(line)
    if m:
        return {
            "step": int(m.group(1)),
            "max_steps": int(m.group(2)),
            "tumor": int(m.group(3)),
            "agents": int(m.group(4)),
            "glucose": float(m.group(5)),
        }
    return None


def cancel_simulation(proc: subprocess.Popen) -> None:
    """Gracefully terminate a running simulation subprocess."""
    if proc.poll() is not None:
        return  # already finished
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def check_timeout(ctx: dict) -> bool:
    """Return True if the simulation has exceeded the timeout."""
    return (time.time() - ctx["start_time"]) > SUBPROCESS_TIMEOUT_SECONDS


def finalize_run(ctx: dict, params: dict, outcome: str = "UNKNOWN") -> dict:
    """Copy CSV, write meta.json, return metadata."""
    run_dir = Path(ctx["run_dir"])
    elapsed = time.time() - ctx["start_time"]

    # Copy simulation log to run dir
    src_csv = PROJECT_ROOT / "logs" / "simulation_log.csv"
    dst_csv = run_dir / "simulation_log.csv"
    if src_csv.exists():
        shutil.copy2(str(src_csv), str(dst_csv))

    meta = {
        "run_id": ctx["run_id"],
        "timestamp": datetime.now().isoformat(),
        "sex": params.get("sex", "F"),
        "BMI": params.get("BMI", 22.0),
        "treatment": params.get("treatment", "ICI+TKI"),
        "treatment_start": params.get("treatment_start"),
        "seed": params.get("random_seed", 1),
        "max_steps": params.get("max_steps", 500),
        "outcome": outcome,
        "elapsed_seconds": round(elapsed, 1),
        "notes": "",
    }
    write_meta(run_dir, meta)
    return meta
