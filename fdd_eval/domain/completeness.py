"""Completeness, metric validity, and missing-information lists."""

from __future__ import annotations

from dataclasses import dataclass

from fdd_eval.domain.metrics import METRICS, Metric
from fdd_eval.domain.nodes import NODES
from fdd_eval.domain.project import Project

NEED_LABELS = {
    "instance_labels": "Instance-level normal–abnormal labels (or a documented rule to obtain them)",
    "hard_or_thresholded": "A hard instance decision, or a score plus an operating threshold",
    "scores": "A continuous anomaly score or probability",
    "event_windows": "Defined event windows with boundaries and a reference event",
    "healthy_cases": "Healthy cases (or paired healthy references) assessed with the same fault-detection condition",
    "faulty_cases": "Faulty cases with case-level labels",
    "fd_condition": "An explicit case-level fault-detection condition",
    "detection_point": "Whether detection is the first detected anomaly or the first satisfied fault-detection condition",
    "reference_event": "The later reference event used for lead time",
    "useful_lead_time": "A stated minimum useful lead time",
    "healthy_instances": "Healthy-period instances for false-alarm rates",
    "ranked": "A ranked list of assets or cases",
    "ranked_or_scores": "Scores or a ranked diagnostic output",
    "diagnostic_labels": "Ground truth at the declared diagnostic level",
    "prognostic_target": "A remaining-useful-life or time-to-failure target with a defined future event",
    "cost_terms": "Site-specific cost terms (for example dispatch, inspection, downtime)",
}


@dataclass
class NodeStatus:
    node_id: str
    state: str  # empty | partial | complete
    missing: list[str]


@dataclass
class Completeness:
    nodes: dict[str, NodeStatus]
    stage_complete: dict[str, tuple[int, int]]
    required_done: int
    required_total: int
    missing_required: list[tuple[str, str]]  # (node_id, action)
    protocol_complete: bool


def _filled(value) -> bool:
    if isinstance(value, bool):
        return True
    if isinstance(value, list):
        return len(value) > 0
    if isinstance(value, str):
        return bool(value.strip())
    return bool(value)


def _status(node_id: str, parts: list[tuple[bool, str]], required: bool) -> NodeStatus:
    missing = [msg for ok, msg in parts if not ok]
    filled_n = sum(1 for ok, _ in parts if ok)
    if filled_n == 0:
        state = "empty"
    elif missing:
        state = "partial"
    else:
        state = "complete"
    if not required and filled_n == 0:
        state = "empty"
    return NodeStatus(node_id, state, missing)


def evaluate_nodes(project: Project) -> dict[str, NodeStatus]:
    p = project
    s1, s2, s3, s4, inp = p.stage1, p.stage2, p.stage3, p.stage4, p.inputs
    obj = s1.primary_objective

    out: dict[str, NodeStatus] = {}
    out["in_data"] = _status("in_data", [
        (_filled(inp.data_types), "Select at least one operational data type"),
    ], True)
    out["in_records"] = _status("in_records", [
        (True, ""),  # optional
    ] if not inp.records else [(_filled(inp.records), "")], False)
    if inp.records:
        out["in_records"] = NodeStatus("in_records", "complete", [])
    else:
        out["in_records"] = NodeStatus("in_records", "empty", [])
    if inp.cost_inputs:
        out["in_costs"] = NodeStatus("in_costs", "complete", [])
    else:
        out["in_costs"] = NodeStatus("in_costs", "empty", [])
    out["in_method"] = _status("in_method", [
        (_filled(inp.method), "Select the method family under evaluation"),
    ], True)

    out["s1_objective"] = _status("s1_objective", [
        (_filled(obj), "Choose a primary evaluation objective"),
    ], True)

    follow = []
    if obj == "obj_early_warning" or not obj:
        follow.append((_filled(s1.early_warning.reference_event),
                       "State the reference event for Early Warning"))
        follow.append((_filled(s1.early_warning.detection_point),
                       "State the detection point (first anomaly vs fault-detection condition)"))
    if obj == "obj_maintenance":
        follow.append((_filled(s1.maintenance.useful_lead_time),
                       "State the useful warning period for planning"))
        follow.append((_filled(s1.maintenance.workload_unit) or _filled(s1.maintenance.acceptable_false_fd),
                       "State acceptable false fault detections or the workload unit"))
    if obj == "obj_diagnostic":
        follow.append((_filled(s1.diagnostic.diagnostic_level),
                       "State the diagnostic level (component / fault type / mechanism)"))
    if obj == "obj_cost":
        follow.append((_filled(s1.cost_impact.cost_terms) or _filled(inp.cost_inputs),
                       "Declare the cost terms used for Cost / Impact Optimisation"))
    if obj in s1.secondary_objectives or True:
        # Secondary objectives add optional follow-ups without blocking if empty
        pass
    if not follow:
        follow = [(False, "Complete the follow-up questions for the primary objective")]
    out["s1_followup"] = _status("s1_followup", follow, True)

    out["s2_ontology"] = _status("s2_ontology", [
        (_filled(s2.fault_definition), "Define the fault the evaluation represents"),
        (_filled(s2.labelled_level), "State the labelled level (component, fault type, …)"),
    ], True)
    tier_parts = [(_filled(s2.evidence_tier), "Select an evidence tier")]
    if s2.evidence_tier == "tier_c":
        tier_parts.append((_filled(s2.symptom_method),
                           "If Tier C, define the symptom method"))
    out["s2_tier"] = _status("s2_tier", tier_parts, True)
    out["s2_labels"] = _status("s2_labels", [
        (_filled(s2.label_representation), "Select how labels are represented"),
        (_filled(s2.uncertainty.timing_certainty), "Record timing certainty"),
    ], True)
    out["s2_healthy"] = _status("s2_healthy", [
        (_filled(s2.healthy_case_evidence),
         "Document healthy-case evidence (absence of a recorded fault is not enough)"),
    ], True)

    out["s3_cases"] = _status("s3_cases", [
        (_filled(s3.case_construction), "State whether cases are pre-defined or constructed"),
    ], True)
    out["s3_windows"] = _status("s3_windows", [
        (s3.event_windows.defined or _filled(s3.event_windows.boundaries),
         "Define event-window boundaries, or state that windows are not used"),
        (_filled(s3.event_windows.window_kind),
         "State whether the interval is a pre-fault window or a fault window"),
        (_filled(s3.event_windows.reference_event) or _filled(s1.early_warning.reference_event),
         "State the event-window reference event"),
    ], True)
    out["s3_compare"] = _status("s3_compare", [
        (_filled(s3.comparison), "Define the faulty–healthy comparison rule"),
    ], True)
    out["s3_periods"] = _status("s3_periods", [
        (_filled(s3.data_periods.test), "Define the test / held-out evaluation period"),
        (_filled(s3.valid_data_rules), "State valid-evaluation data rules"),
    ], True)
    out["s3_tuning"] = _status("s3_tuning", [
        (_filled(s3.tuning_mode), "Choose oracle or held-out tuning"),
        (s3.tuning_mode != "tune_heldout" or _filled(s3.tuning_inventory),
         "For held-out tuning, state the tuning inventory"),
    ], True)
    out["s3_fd"] = _status("s3_fd", [
        (_filled(s3.fd_condition), "Define the case-level fault-detection condition"),
    ], True)

    out["s4_output"] = _status("s4_output", [
        (_filled(s4.output_class), "Select the class scheme of the method output"),
        (_filled(s4.output_score), "Select whether the output is a hard label, score or ranked list"),
    ], True)
    out["s4_dimensions"] = _status("s4_dimensions", [
        (_filled(obj), "Objective required before performance dimensions can be confirmed"),
    ], True)
    out["s4_metrics"] = _status("s4_metrics", [
        (_filled(s4.accepted_metrics), "Accept at least one metric (or record an override)"),
        (_filled(s4.accepted_metrics) or _filled(s4.override_notes),
         "Accept recommended metrics, or explain an override"),
    ], True)
    return out


def summarise(project: Project) -> Completeness:
    nodes = evaluate_nodes(project)
    required = [n for n in NODES if n.required]
    required_done = sum(1 for n in required if nodes[n.id].state == "complete")
    missing_required: list[tuple[str, str]] = []
    for n in required:
        st = nodes[n.id]
        if st.state != "complete":
            if st.missing:
                for msg in st.missing:
                    missing_required.append((n.id, msg))
            else:
                missing_required.append((n.id, f"Complete: {n.title}"))
    stage_complete: dict[str, tuple[int, int]] = {}
    for stage in ("inputs", "stage1", "stage2", "stage3", "stage4"):
        stage_nodes = [n for n in NODES if n.stage == stage and n.required]
        done = sum(1 for n in stage_nodes if nodes[n.id].state == "complete")
        stage_complete[stage] = (done, len(stage_nodes))
    return Completeness(
        nodes=nodes,
        stage_complete=stage_complete,
        required_done=required_done,
        required_total=len(required),
        missing_required=missing_required,
        protocol_complete=required_done == len(required),
    )


def project_capabilities(project: Project) -> set[str]:
    """Facts available for metric validity (protocol-level, not CSV)."""
    caps: set[str] = set()
    s1, s2, s3, s4, inp = project.stage1, project.stage2, project.stage3, project.stage4, project.inputs
    if s2.label_representation in ("label_binary", "label_soft", "label_interval"):
        caps.add("instance_labels")
    if s4.output_score == "out_hard":
        caps.add("hard_or_thresholded")
    if s4.output_score == "out_score":
        caps.add("scores")
        caps.add("hard_or_thresholded")  # a threshold can still be applied
    if s4.output_score == "out_ranked":
        caps.add("ranked")
        caps.add("ranked_or_scores")
    if s4.output_score == "out_score":
        caps.add("ranked_or_scores")
    if s3.event_windows.defined or s3.event_windows.boundaries.strip():
        caps.add("event_windows")
    if s3.comparison in ("cmp_pairs", "cmp_matching", "cmp_group") or s2.healthy_case_evidence.strip():
        caps.add("healthy_cases")
        caps.add("healthy_instances")
    if s3.case_construction:
        caps.add("faulty_cases")
    if s3.fd_condition:
        caps.add("fd_condition")
    if s1.early_warning.detection_point:
        caps.add("detection_point")
    if s1.early_warning.reference_event or s3.event_windows.reference_event:
        caps.add("reference_event")
    if s1.maintenance.useful_lead_time.strip():
        caps.add("useful_lead_time")
    if s1.primary_objective == "obj_diagnostic" or s4.output_class in ("out_multiclass", "out_multilabel"):
        if s2.labelled_level.strip():
            caps.add("diagnostic_labels")
    if s1.cost_impact.cost_terms or inp.cost_inputs:
        caps.add("cost_terms")
    return caps


def metric_validity(project: Project, metric: Metric) -> tuple[bool, list[str]]:
    caps = project_capabilities(project)
    missing = [NEED_LABELS[n] for n in metric.needs if n not in caps]
    return (len(missing) == 0, missing)


def node_state(project: Project, node_id: str) -> str:
    return evaluate_nodes(project)[node_id].state
