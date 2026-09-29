"""Load precomputed case CSVs. The app does not run AD Algorithms."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path


PERIODS = ("train", "val", "test")


@dataclass
class CaseSeries:
    path: Path
    role: str
    time_index: list[int]
    timestamp: list[str]
    period: list[str]
    raw: list[float]
    monitoring_indicator: list[float]
    anomaly_score: list[float]
    threshold: list[float]
    alarm: list[int]
    in_event_window: list[int]
    instance_label: list[int]
    wind_speed: list[float] = field(default_factory=list)
    expected_power_kw: list[float] = field(default_factory=list)
    power_kw: list[float] = field(default_factory=list)

    def has_power(self) -> bool:
        n = len(self.time_index)
        return (
            len(self.power_kw) == n
            and len(self.expected_power_kw) == n
            and n > 0
            and any(v != 0.0 for v in self.expected_power_kw)
        )

    def mask(self, period: str) -> list[int]:
        return [i for i, p in enumerate(self.period) if p == period]

    def train_val_idx(self) -> list[int]:
        return [i for i, p in enumerate(self.period) if p in ("train", "val")]

    def test_idx(self) -> list[int]:
        return self.mask("test")

    def event_idx(self) -> list[int]:
        return [i for i, flag in enumerate(self.in_event_window) if int(flag) == 1]


def _f(row: dict, key: str, default: float = 0.0) -> float:
    raw = row.get(key, "")
    if raw is None or raw == "":
        return default
    return float(raw)


def _i(row: dict, key: str, default: int = 0) -> int:
    raw = row.get(key, "")
    if raw is None or raw == "":
        return default
    return int(float(raw))


def load_case_csv(path: str | Path, role: str = "") -> CaseSeries:
    path = Path(path)
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    if not rows:
        raise ValueError(f"No rows in {path}")
    inferred = role or rows[0].get("case_role", path.stem)
    keys = rows[0].keys()
    has_power = "power_kw" in keys and "expected_power_kw" in keys
    return CaseSeries(
        path=path,
        role=inferred,
        time_index=[_i(r, "time_index", i) for i, r in enumerate(rows)],
        timestamp=[r.get("timestamp", str(i)) for i, r in enumerate(rows)],
        period=[r.get("period", "test") for r in rows],
        raw=[_f(r, "raw") for r in rows],
        monitoring_indicator=[_f(r, "monitoring_indicator") for r in rows],
        anomaly_score=[_f(r, "anomaly_score") for r in rows],
        threshold=[_f(r, "threshold") for r in rows],
        alarm=[_i(r, "alarm") for r in rows],
        in_event_window=[_i(r, "in_event_window") for r in rows],
        instance_label=[_i(r, "instance_label") for r in rows],
        wind_speed=[_f(r, "wind_speed") for r in rows] if "wind_speed" in keys else [],
        expected_power_kw=[_f(r, "expected_power_kw") for r in rows] if has_power else [],
        power_kw=[_f(r, "power_kw") for r in rows] if has_power else [],
    )


def resolve_csv_path(stored: str, project_path: Path | None, repo_root: Path) -> Path | None:
    if not stored:
        return None
    path = Path(stored)
    if path.is_file():
        return path
    candidates = []
    if project_path:
        candidates.append(project_path.parent / stored)
    candidates.append(repo_root / stored)
    candidates.append(repo_root / "tutorials" / path.name)
    for cand in candidates:
        if cand.is_file():
            return cand
    return path if path.exists() else None
