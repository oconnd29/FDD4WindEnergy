"""Recommend metrics from the dense Stage 4 topology and earlier answers."""

from __future__ import annotations

from dataclasses import dataclass

from fdd_eval.domain.completeness import metric_validity
from fdd_eval.domain.metrics import METRICS, Metric, get
from fdd_eval.domain.project import Project


@dataclass
class Recommendation:
    metric: Metric
    reason: str
    valid: bool
    missing: list[str]
    core: bool = True


def _add(out: list[Recommendation], project: Project, metric_id: str, reason: str, core: bool = True) -> None:
    if any(r.metric.id == metric_id for r in out):
        return
    metric = get(metric_id)
    valid, missing = metric_validity(project, metric)
    out.append(Recommendation(metric, reason, valid, missing, core))


def required_dimensions(project: Project) -> list[str]:
    obj = project.stage1.primary_objective
    dims = []
    if obj == "obj_early_warning":
        dims = ["instance", "case", "earliness", "combined"]
    elif obj == "obj_maintenance":
        dims = ["case", "earliness", "operational"]
    elif obj == "obj_diagnostic":
        dims = ["instance"]
    elif obj == "obj_cost":
        dims = ["case", "operational"]
    else:
        dims = ["instance", "case"]
    if project.stage4.include_stability == "yes_stability" and "operational" not in dims:
        dims.append("operational")
    if "obj_cost" in project.stage1.secondary_objectives and "operational" not in dims:
        dims.append("operational")
    if "obj_maintenance" in project.stage1.secondary_objectives and "operational" not in dims:
        dims.append("operational")
    return dims


def recommend(project: Project) -> list[Recommendation]:
    recs: list[Recommendation] = []
    obj = project.stage1.primary_objective
    score = project.stage4.output_score
    klass = project.stage4.output_class
    detect = project.stage1.early_warning.detection_point

    if not obj:
        return recs

    if obj == "obj_early_warning":
        if score == "out_hard" or not score:
            _add(recs, project, "precision",
                 "Hard instance decisions for Early Warning need precision so false anomaly detections are visible.")
            _add(recs, project, "recall",
                 "Recall shows how much labelled abnormal behaviour inside the event window is detected.")
            _add(recs, project, "f1",
                 "F1 summarises the precision–recall trade-off at the operating threshold.")
            _add(recs, project, "balanced_accuracy",
                 "Normal instances usually dominate turbine records; balanced accuracy reduces that bias.", core=False)
            _add(recs, project, "mcc",
                 "MCC uses all four confusion-matrix terms and is less dominated by the normal class.", core=False)
        if score == "out_score":
            _add(recs, project, "pr_auc",
                 "A score output should be summarised with PR-AUC under class imbalance.")
            _add(recs, project, "roc_auc",
                 "ROC-AUC describes score separation across thresholds, not the selected operating point.", core=False)
            _add(recs, project, "precision",
                 "Also report precision at the operating threshold; AUC does not replace it.")
            _add(recs, project, "recall",
                 "Also report recall at the operating threshold.")
        _add(recs, project, "faulty_detection_rate",
             "Early Warning still requires a case-level detection rate after the fault-detection condition is applied.")
        _add(recs, project, "false_fd_rate",
             "Healthy cases are required so false fault detections are visible.")
        if detect == "detect_first_anomaly":
            _add(recs, project, "first_anomaly_time",
                 "You selected the first detected anomaly as the detection point.")
            _add(recs, project, "warning_lead",
                 "Warning lead time is measured from that detection point to the reference event.")
        else:
            _add(recs, project, "fd_time",
                 "You selected the first satisfied fault-detection condition as the detection point.")
            _add(recs, project, "warning_lead",
                 "Warning lead time should use that fault-detection time, not the first isolated anomaly.")
        _add(recs, project, "care_c",
             "CARE Coverage is the instance-level view inside faulty event windows.")
        _add(recs, project, "care_a",
             "CARE Accuracy includes healthy-case instance behaviour.")
        _add(recs, project, "care_r",
             "CARE Reliability is the case-level fault-detection component.")
        _add(recs, project, "care_e",
             "CARE Earliness rewards earlier evidence inside the event window.")
        _add(recs, project, "care",
             "Unified CARE is the combined Early Warning metric used in Chapters 5 and 6; report C, A, R and E with it.")

    elif obj == "obj_maintenance":
        if score == "out_ranked":
            _add(recs, project, "prec_at_k",
                 "A ranked maintenance list is judged with precision@k at the review length k.")
            _add(recs, project, "rec_at_k",
                 "Recall@k shows whether the assets that needed attention appeared in the review list.")
            _add(recs, project, "mrr",
                 "Mean reciprocal rank summarises how high relevant assets are placed.", core=False)
        else:
            _add(recs, project, "alerts_asset_day",
                 "Maintenance Planning should represent workload (alerts per asset-day or equivalent).")
            _add(recs, project, "faulty_detection_rate",
                 "Planning still needs to know which faulty cases would have been flagged.")
            _add(recs, project, "false_fd_rate",
                 "Acceptable false fault detections are part of the planning decision.")
        if project.stage1.maintenance.useful_lead_time.strip():
            _add(recs, project, "lead_success",
                 "A useful-lead-time target is stated, so report the lead-time success rate.")
            _add(recs, project, "warning_lead",
                 "Report the lead-time distribution, with the detection point named.")
        else:
            _add(recs, project, "warning_lead",
                 "Planning depends on when the detection occurs relative to a reference event.")

    elif obj == "obj_diagnostic":
        _add(recs, project, "macro_f1",
             "Diagnostic Quality is judged at class level with per-class precision, recall and macro F1.")
        _add(recs, project, "diag_confusion",
             "A confusion matrix keeps identification errors visible.")
        if score in ("out_score", "out_ranked") or klass == "out_multiclass":
            _add(recs, project, "topk_acc",
                 "Top-k accuracy is appropriate when several diagnostic labels are ranked.", core=False)

    elif obj == "obj_cost":
        _add(recs, project, "expected_cost",
             "Cost / Impact Optimisation requires an expected cost or net-benefit model from declared terms.")
        _add(recs, project, "cost_weighted_error",
             "A cost-weighted error makes the same terms visible as a single loss.", core=False)
        _add(recs, project, "false_fd_rate",
             "False fault detections enter the cost model and should also be reported raw.")
        _add(recs, project, "faulty_detection_rate",
             "Missed faulty cases enter the cost model and should also be reported raw.")
        _add(recs, project, "warning_lead",
             "Delay cost needs a defined detection point and reference event.", core=False)

    if project.stage4.include_stability == "yes_stability":
        _add(recs, project, "fa_per_day",
             "You asked to include stability/nuisance measures: false alarms per day.")
        _add(recs, project, "chatter",
             "Chatter/transitions describe alarm instability independently of detection rate.")
        _add(recs, project, "mtbfa",
             "Mean time between false alarms is an alternative nuisance summary.", core=False)

    if "obj_cost" in project.stage1.secondary_objectives and obj != "obj_cost":
        _add(recs, project, "expected_cost",
             "Cost / Impact is a secondary objective, so include an expected-cost measure if terms exist.",
             core=False)

    if "obj_early_warning" in project.stage1.secondary_objectives and obj != "obj_early_warning":
        _add(recs, project, "care",
             "Early Warning is a secondary objective, so report unified CARE with C, A, R and E.",
             core=False)
        _add(recs, project, "care_c",
             "CARE Coverage remains the instance-level detection component on faulty cases.", core=False)
        _add(recs, project, "care_a",
             "CARE Accuracy remains the healthy-case instance summary.", core=False)
        _add(recs, project, "care_r",
             "CARE Reliability remains the case-level fault-detection component.", core=False)
        _add(recs, project, "care_e",
             "CARE Earliness remains the timing component inside the event window.", core=False)

    return recs


def recommendation_map(project: Project) -> dict[str, Recommendation]:
    return {r.metric.id: r for r in recommend(project)}
