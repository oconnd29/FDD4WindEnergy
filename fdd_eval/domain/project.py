"""Versioned evaluation-project schema."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields, is_dataclass
from datetime import datetime, timezone
from typing import Any, get_type_hints


SCHEMA_VERSION = 1


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _from_dict(cls, data: dict | None):
    if not data:
        return cls()
    hints = get_type_hints(cls)
    kwargs = {}
    for field_obj in fields(cls):
        if field_obj.name not in data:
            continue
        value = data[field_obj.name]
        typ = hints.get(field_obj.name)
        if isinstance(typ, type) and is_dataclass(typ) and isinstance(value, dict):
            kwargs[field_obj.name] = _from_dict(typ, value)
        else:
            kwargs[field_obj.name] = value
    return cls(**kwargs)


@dataclass
class EarlyWarning:
    reference_event: str = ""
    detection_point: str = ""
    notes: str = ""


@dataclass
class MaintenancePlanning:
    useful_lead_time: str = ""
    acceptable_false_fd: str = ""
    workload_unit: str = ""
    notes: str = ""


@dataclass
class DiagnosticQuality:
    diagnostic_level: str = ""
    notes: str = ""


@dataclass
class CostModel:
    """Site tariffs used to score Cost / Impact. Defaults are tutorial assumptions, not a farm quote."""

    price_eur_per_mwh: float = 100.0
    inspection_eur: float = 4000.0
    planned_repair_eur: float = 12000.0
    planned_downtime_h: float = 24.0
    emergency_repair_eur: float = 50000.0
    emergency_downtime_h: float = 240.0
    rated_power_kw: float = 2000.0
    sample_hours: float = 1.0 / 6.0  # 10-minute samples
    notes: str = ""


@dataclass
class CostImpact:
    cost_terms: list[str] = field(default_factory=list)
    sensitivity_planned: bool = False
    notes: str = ""
    model: CostModel = field(default_factory=CostModel)


@dataclass
class Stage1:
    primary_objective: str = ""
    secondary_objectives: list[str] = field(default_factory=list)
    early_warning: EarlyWarning = field(default_factory=EarlyWarning)
    maintenance: MaintenancePlanning = field(default_factory=MaintenancePlanning)
    diagnostic: DiagnosticQuality = field(default_factory=DiagnosticQuality)
    cost_impact: CostImpact = field(default_factory=CostImpact)


@dataclass
class Uncertainty:
    evidence_certainty: str = ""
    timing_certainty: str = ""
    source_agreement: str = ""
    label_stability: str = ""


@dataclass
class Stage2:
    fault_definition: str = ""
    labelled_level: str = ""
    evidence_tier: str = ""
    evidence_sources: list[str] = field(default_factory=list)
    symptom_method: str = ""
    label_representation: str = ""
    uncertainty: Uncertainty = field(default_factory=Uncertainty)
    healthy_case_evidence: str = ""
    circular_risk: bool = False
    notes: str = ""


@dataclass
class EventWindows:
    defined: bool = False
    window_kind: str = ""
    boundaries: str = ""
    reference_event: str = ""
    timing_rules: str = ""


@dataclass
class DataPeriods:
    training: str = ""
    validation: str = ""
    test: str = ""


@dataclass
class Stage3:
    case_construction: str = ""
    case_notes: str = ""
    event_windows: EventWindows = field(default_factory=EventWindows)
    comparison: str = ""
    data_periods: DataPeriods = field(default_factory=DataPeriods)
    valid_data_rules: str = ""
    tuning_mode: str = ""
    tuning_inventory: str = ""
    tuning_notes: str = ""
    fd_condition: str = ""
    fd_condition_notes: str = ""


@dataclass
class Stage4:
    output_class: str = ""
    output_score: str = ""
    include_stability: str = ""
    accepted_metrics: list[str] = field(default_factory=list)
    rejected_metrics: list[str] = field(default_factory=list)
    override_notes: str = ""


@dataclass
class Inputs:
    data_types: list[str] = field(default_factory=list)
    records: list[str] = field(default_factory=list)
    cost_inputs: list[str] = field(default_factory=list)
    method: str = ""
    method_notes: str = ""


@dataclass
class CaseData:
    """Paths to precomputed case CSVs. The app plots and scores; it does not run the AD Algorithm."""
    faulty_csv: str = ""
    healthy_csv: str = ""
    kappa: int = 72
    notes: str = ""


@dataclass
class ReproducibilityLog:
    followed: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class Project:
    schema_version: int = SCHEMA_VERSION
    title: str = "Untitled evaluation"
    created: str = field(default_factory=_now)
    modified: str = field(default_factory=_now)
    notes: str = ""
    inputs: Inputs = field(default_factory=Inputs)
    stage1: Stage1 = field(default_factory=Stage1)
    stage2: Stage2 = field(default_factory=Stage2)
    stage3: Stage3 = field(default_factory=Stage3)
    stage4: Stage4 = field(default_factory=Stage4)
    case_data: CaseData = field(default_factory=CaseData)
    reproducibility: ReproducibilityLog = field(default_factory=ReproducibilityLog)

    def touch(self) -> None:
        self.modified = _now()

    def to_dict(self) -> dict[str, Any]:
        self.touch()
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Project:
        data = dict(data or {})
        data.pop("schema_version", None)
        obj = _from_dict(cls, data)
        obj.schema_version = SCHEMA_VERSION
        return obj

    def has_objective(self, objective_id: str) -> bool:
        return (
            self.stage1.primary_objective == objective_id
            or objective_id in self.stage1.secondary_objectives
        )
