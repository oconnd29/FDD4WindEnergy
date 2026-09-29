"""Framework nodes shown on the stage map."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NodeSpec:
    id: str
    stage: str
    title: str
    summary: str
    required: bool = True


STAGES: list[tuple[str, str, str]] = [
    ("inputs", "Inputs", "Operational data, method and evidence"),
    ("stage1", "Stage 1", "Evaluation Objective"),
    ("stage2", "Stage 2", "Ground-Truth Development"),
    ("stage3", "Stage 3", "Evaluation Design"),
    ("stage4", "Stage 4", "Metric Selection"),
]

NODES: list[NodeSpec] = [
    NodeSpec("in_data", "inputs", "Operational data types",
             "Which monitoring or operational series are in play."),
    NodeSpec("in_records", "inputs", "Evidence records",
             "Inspection, maintenance and replacement records.", required=False),
    NodeSpec("in_costs", "inputs", "Operational-cost inputs",
             "Dispatch, inspection, downtime or other site costs.", required=False),
    NodeSpec("in_method", "inputs", "Method under evaluation",
             "AD Algorithm, NBM pipeline, diagnostic model, or other."),
    NodeSpec("s1_objective", "stage1", "Primary objective",
             "Early Warning, Maintenance Planning, Diagnostic Quality, or Cost / Impact."),
    NodeSpec("s1_followup", "stage1", "Objective follow-up",
             "Reference event, detection point, planning horizon, diagnostic level, or costs."),
    NodeSpec("s2_ontology", "stage2", "Fault ontology",
             "What is labelled, and at what level."),
    NodeSpec("s2_tier", "stage2", "Evidence tier and sources",
             "Tier A / B / C, combined, or unlabelled."),
    NodeSpec("s2_labels", "stage2", "Label definition and uncertainty",
             "Representation, timing certainty, agreement and stability."),
    NodeSpec("s2_healthy", "stage2", "Healthy-case evidence",
             "Absence of a recorded fault is not confirmation of healthy operation."),
    NodeSpec("s3_cases", "stage3", "Case construction",
             "Pre-defined or constructed healthy/faulty cases."),
    NodeSpec("s3_windows", "stage3", "Event windows",
             "Boundaries, reference event and timing rules."),
    NodeSpec("s3_compare", "stage3", "Faulty–healthy comparison",
             "Pairs, matching or grouping."),
    NodeSpec("s3_periods", "stage3", "Data periods and validity",
             "Training, validation, test, and valid-evaluation rules."),
    NodeSpec("s3_tuning", "stage3", "Tuning and held-out evaluation",
             "Oracle vs held-out tuning and inventory composition."),
    NodeSpec("s3_fd", "stage3", "Fault-detection condition",
             "Count, persistence, density or temporal pattern."),
    NodeSpec("s4_output", "stage4", "Method output type",
             "Binary / multi-class / multi-label and hard / score / ranked."),
    NodeSpec("s4_dimensions", "stage4", "Required performance dimensions",
             "Instance, case, earliness, combined, operational."),
    NodeSpec("s4_metrics", "stage4", "Selected metric set",
             "Accepted recommendations, validity and missing information."),
]


def nodes_for(stage: str) -> list[NodeSpec]:
    return [n for n in NODES if n.stage == stage]


def node_by_id(node_id: str) -> NodeSpec:
    return next(n for n in NODES if n.id == node_id)
