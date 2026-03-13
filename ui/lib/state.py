"""Run metadata I/O, parameter loading, CSV loading."""

import functools
import json
import re
import shutil
from dataclasses import fields
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = PROJECT_ROOT / "logs" / "runs"


# ---------------------------------------------------------------------------
# Parameter defaults from dataclasses
# ---------------------------------------------------------------------------

@functools.lru_cache(maxsize=1)
def _param_classes():
    """Deferred import of all parameter dataclasses (cached)."""
    from src.parameters.model_parameters import ModelParameters
    from src.parameters.patient_parameters import PatientParameters
    from src.parameters.weight_parameters import WeightParameters
    return (ModelParameters, PatientParameters, WeightParameters)


def load_all_defaults():
    """Return merged dict of all default parameter values."""
    defaults = {}
    for cls in _param_classes():
        defaults.update({f.name: f.default for f in fields(cls)})
    return defaults


def load_all_labels():
    """Return merged dict of all parameter labels."""
    labels = {}
    for cls in _param_classes():
        cls_labels = getattr(cls, "param_labels", {})
        labels.update(cls_labels)
    return labels


def load_all_steps():
    """Return merged dict of all parameter steps."""
    steps = {}
    for cls in _param_classes():
        cls_steps = getattr(cls, "param_steps", {})
        steps.update(cls_steps)
    return steps


def load_optimized_preset():
    """Return the optimized parameter set from best_parameters.py."""
    from src.learning.best_parameters import best_params
    return dict(best_params)


def load_scenario_presets():
    """Return dict of named scenario presets for diverse simulation outcomes.

    Each preset is a dict of parameter overrides (applied on top of defaults).
    """
    optimized = load_optimized_preset()

    return {
        # --- Favorable outcomes (survival / regression) ---
        "Strong Immune Response": {
            "description": "Healthy patient with robust innate + adaptive immunity. "
                           "High NK and CD8 concentrations overwhelm the tumor early.",
            "icon": ":material/shield:",
            "outcome_hint": "SURVIVAL",
            "overrides": {
                **optimized,
                "sex": "M",
                "BMI": 23.0,
                "treatment": "ICI+TKI",
                "treatment_start": 50,
                "nkl_concentration": 320000,
                "cd8_concentration": 160000,
                "cd4_concentration": 120000,
                "dc_concentration": 120000,
                "m1_concentration": 80000,
                "w_natural_killer_kill_rate": 5.0,
                "w_cytotoxic_kill": 3.5,
                "w_cytotoxic_proliferation": 2.0,
                "w_tumor_growth_eff": 1.5,
                "w_m1_phagocytosis": 2.0,
            },
        },
        "Early Treatment Success": {
            "description": "Combination therapy starts very early (step 20) before "
                           "tumor establishes. Moderate immune system, treatment does the heavy lifting.",
            "icon": ":material/medication:",
            "outcome_hint": "SURVIVAL",
            "overrides": {
                **optimized,
                "sex": "F",
                "BMI": 24.0,
                "treatment": "ICI+TKI",
                "treatment_start": 20,
                "w_ici_effectiveness": 1.2,
                "w_tki_effectiveness": 1.5,
                "w_tumor_growth_eff": 2.0,
            },
        },

        # --- Unfavorable outcomes (progression) ---
        "Aggressive Tumor": {
            "description": "Fast-growing tumor with high angiogenesis, weak immune "
                           "infiltration, and late treatment start. Tumor likely escapes control.",
            "icon": ":material/emergency:",
            "outcome_hint": "PROGRESSION",
            "overrides": {
                **optimized,
                "sex": "M",
                "BMI": 22.0,
                "treatment": "TKI",
                "treatment_start": 200,
                "ctc_concentration": 160000,
                "nkl_concentration": 80000,
                "cd8_concentration": 40000,
                "w_tumor_growth_eff": 4.5,
                "w_tumor_angiogenesis": 3.0,
                "w_angiogenesis_tumor_growth": 2.0,
                "w_m2_tumour_growth": 2.5,
                "w_cytotoxic_kill": 1.0,
                "w_natural_killer_kill_rate": 1.5,
                "w_gene_pd1_inhibition": 2.0,
            },
        },
        "Obese Immunosuppressed": {
            "description": "High-BMI patient with elevated Treg activity and M2 polarization. "
                           "Immune system is suppressed, allowing steady tumor growth.",
            "icon": ":material/warning:",
            "outcome_hint": "PROGRESSION",
            "overrides": {
                **optimized,
                "sex": "F",
                "BMI": 38.0,
                "treatment": "ICI",
                "treatment_start": 100,
                "treg_concentration": 80000,
                "m2_concentration": 80000,
                "m1_concentration": 20000,
                "nkl_concentration": 80000,
                "cd8_concentration": 40000,
                "w_BMI_on_treg_diff": 2.0,
                "w_BMI_on_m2_mutation": 2.5,
                "w_BMI_nkl_kill_rate": 5.0,
                "w_treg_t_kill_rate": 0.5,
                "w_treg_t_proliferation": 2.5,
                "w_m2_tumour_growth": 2.5,
                "w_tumor_growth_eff": 3.0,
                "w_ici_effectiveness": 0.3,
            },
        },
        "Untreated Baseline": {
            "description": "No therapeutic intervention. Tumor grows against the "
                           "natural immune response only. Useful as a control scenario.",
            "icon": ":material/science:",
            "outcome_hint": "PROGRESSION",
            "overrides": {
                **optimized,
                "sex": "F",
                "BMI": 22.0,
                "treatment": "None",
                "treatment_start": 0,
            },
        },

        # --- Borderline / interesting dynamics ---
        "Immune Equilibrium": {
            "description": "Balanced tumor growth and immune clearance. The tumor "
                           "neither grows nor shrinks — a dynamic stalemate.",
            "icon": ":material/balance:",
            "outcome_hint": "STABLE",
            "overrides": {
                **optimized,
                "sex": "M",
                "BMI": 25.0,
                "treatment": "ICI",
                "treatment_start": 80,
                "w_tumor_growth_eff": 2.8,
                "w_cytotoxic_kill": 2.8,
                "w_natural_killer_kill_rate": 3.0,
                "w_m1_phagocytosis": 1.5,
                "w_treg_t_kill_rate": 0.3,
                "w_progressive_exhaustion": 0.15,
            },
        },
        "ICI Monotherapy": {
            "description": "Checkpoint inhibitor only — relies on unleashing the "
                           "adaptive immune response. Outcome depends on PD-1 dynamics.",
            "icon": ":material/vaccines:",
            "outcome_hint": "VARIABLE",
            "overrides": {
                **optimized,
                "sex": "M",
                "BMI": 26.0,
                "treatment": "ICI",
                "treatment_start": 80,
                "w_ici_effectiveness": 0.8,
                "w_cytotoxic_pd1_inhibition": 2.5,
                "w_gene_pd1_inhibition": 1.5,
                "cd8_concentration": 100000,
                "cd4_concentration": 100000,
            },
        },
        "TKI Monotherapy": {
            "description": "Anti-angiogenic therapy only — starves the tumor of blood "
                           "supply. Less direct immune activation.",
            "icon": ":material/healing:",
            "outcome_hint": "VARIABLE",
            "overrides": {
                **optimized,
                "sex": "F",
                "BMI": 24.0,
                "treatment": "TKI",
                "treatment_start": 60,
                "w_tki_effectiveness": 1.3,
                "w_tumor_angiogenesis": 2.5,
                "w_angiogenesis_tumor_growth": 1.5,
            },
        },
    }


def get_dimension_from_volume(volume: float, block_size: int = 10) -> int:
    """Delegate to canonical implementation in measures_utils."""
    from src.model.measures_utils import get_dimension_from_volume as _gdv
    return _gdv(volume, block_size)


# ---------------------------------------------------------------------------
# YAML config I/O
# ---------------------------------------------------------------------------

def params_to_yaml(params: dict) -> str:
    """Convert flat params dict to sectioned YAML string."""
    model_cls, patient_cls, weight_cls = _param_classes()
    key_to_section = {}
    for section, cls in (("model", model_cls), ("patient", patient_cls), ("weights", weight_cls)):
        for f in fields(cls):
            key_to_section[f.name] = section

    sections = {"model": {}, "patient": {}, "weights": {}}
    for k, v in params.items():
        section = key_to_section.get(k)
        if section:
            sections[section][k] = v
    return yaml.dump(sections, default_flow_style=False, sort_keys=False)


def yaml_to_params(yaml_text: str) -> dict:
    """Parse a sectioned YAML config back into a flat params dict."""
    data = yaml.safe_load(yaml_text)
    if not isinstance(data, dict):
        raise ValueError("Invalid YAML: expected a mapping at the top level.")
    flat = {}
    for section_name, section_values in data.items():
        if isinstance(section_values, dict):
            flat.update(section_values)
        else:
            # Top-level key (not sectioned)
            flat[section_name] = section_values
    return flat


def write_config_yaml(params: dict, path: Path):
    """Write params to a YAML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(params_to_yaml(params))


# ---------------------------------------------------------------------------
# Run metadata
# ---------------------------------------------------------------------------

def write_meta(run_dir: Path, meta: dict):
    """Write run metadata JSON."""
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2))


def read_meta(run_dir: Path) -> dict:
    """Read run metadata JSON."""
    return json.loads((run_dir / "meta.json").read_text())


def list_runs() -> list[dict]:
    """Return list of run metadata dicts, newest first."""
    runs = []
    if not RUNS_DIR.exists():
        return runs
    for d in sorted(RUNS_DIR.iterdir(), reverse=True):
        try:
            meta = json.loads((d / "meta.json").read_text())
            meta["run_dir"] = str(d)
            runs.append(meta)
        except (json.JSONDecodeError, OSError, FileNotFoundError):
            continue
    return runs


def load_run_csv(run_dir: str | Path):
    """Load simulation_log.csv from a run directory."""
    import pandas as pd
    try:
        return pd.read_csv(Path(run_dir) / "simulation_log.csv")
    except FileNotFoundError:
        return None


def update_run_notes(run_dir: str | Path, notes: str):
    """Update the notes field in a run's meta.json."""
    meta_path = Path(run_dir) / "meta.json"
    meta = json.loads(meta_path.read_text())
    meta["notes"] = notes
    meta_path.write_text(json.dumps(meta, indent=2))


def delete_run(run_dir: str | Path):
    """Delete a run directory and all its contents."""
    shutil.rmtree(run_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Snapshot utilities
# ---------------------------------------------------------------------------

SNAPSHOT_SUBDIR = "snapshots"
_STEP_RE = re.compile(r"step_(\d+)\.npz$")


def snapshot_dir_for(run_dir: str | Path) -> Path:
    """Return the snapshot directory for a given run."""
    return Path(run_dir) / SNAPSHOT_SUBDIR


def load_snapshot(path: str | Path) -> dict:
    """Load a .npz snapshot → {agents, glucose, step, grid_dims}."""
    import numpy as np
    with np.load(str(path)) as data:
        meta = data["metadata"]
        return {
            "agents": data["agents"].copy(),
            "glucose": data["glucose"].copy(),
            "step": int(meta[0]),
            "grid_dims": (int(meta[1]), int(meta[2]), int(meta[3])),
        }


def latest_snapshot(snapshot_dir: str | Path) -> Path | None:
    """Return path to newest step_*.npz, or None."""
    snap_path = Path(snapshot_dir)
    if not snap_path.is_dir():
        return None
    files = sorted(snap_path.glob("step_*.npz"))
    return files[-1] if files else None


def list_snapshot_steps(snapshot_dir: str | Path) -> list[int]:
    """List available step numbers from snapshot files, sorted."""
    steps = []
    for f in Path(snapshot_dir).glob("step_*.npz"):
        m = _STEP_RE.search(f.name)
        if m:
            steps.append(int(m.group(1)))
    return sorted(steps)


def find_snapshot_runs() -> list[dict]:
    """Return runs that have snapshot directories with .npz files."""
    result = []
    for run in list_runs():
        snap_dir = snapshot_dir_for(run["run_dir"])
        if snap_dir.is_dir() and any(snap_dir.glob("*.npz")):
            result.append({**run, "snapshot_dir": str(snap_dir)})
    return result
