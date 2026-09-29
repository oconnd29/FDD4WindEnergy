"""Metric catalog used by the Stage 4 advisor."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Metric:
    id: str
    name: str
    unit: str  # instance | case | earliness | combined | operational
    summary: str
    limitation: str
    needs: tuple[str, ...] = ()
    citations: tuple[str, ...] = ()
    care_component: str = ""


METRICS: dict[str, Metric] = {}


def _m(**kwargs) -> Metric:
    metric = Metric(**kwargs)
    METRICS[metric.id] = metric
    return metric


def get(metric_id: str) -> Metric:
    return METRICS[metric_id]


# Instance-level
_m(id="accuracy", name="Accuracy", unit="instance",
   summary="Overall classification of normal and abnormal instances.",
   limitation="Can be dominated by normal instances when abnormal behaviour is rare.",
   needs=("instance_labels", "hard_or_thresholded"),
   citations=("Leahy, 2018", "Desai et al., 2020"))
_m(id="precision", name="Precision", unit="instance",
   summary="How often detected anomalies correspond to abnormal instances.",
   limitation="Does not measure how much abnormal behaviour is missed.",
   needs=("instance_labels", "hard_or_thresholded"))
_m(id="recall", name="Recall", unit="instance",
   summary="How much labelled abnormal behaviour is detected.",
   limitation="Does not account for false anomaly detections.",
   needs=("instance_labels", "hard_or_thresholded"))
_m(id="f1", name="F1 score", unit="instance",
   summary="Balances precision and recall in one classification score.",
   limitation="Does not include true negatives and can hide the precision–recall trade-off.",
   needs=("instance_labels", "hard_or_thresholded"))
_m(id="specificity", name="Specificity", unit="instance",
   summary="How well normal instances are classified as normal.",
   limitation="Does not describe detection of abnormal instances.",
   needs=("instance_labels", "hard_or_thresholded"))
_m(id="balanced_accuracy", name="Balanced accuracy", unit="instance",
   summary="A more balanced assessment where classes are strongly imbalanced.",
   limitation="Does not describe detection timing or case-level fault detection.",
   needs=("instance_labels", "hard_or_thresholded"),
   citations=("Chatterjee and Byun, 2025",))
_m(id="mcc", name="MCC", unit="instance",
   summary="Matthews correlation coefficient using all four confusion-matrix terms.",
   limitation="Does not describe detection timing or case-level fault detection.",
   needs=("instance_labels", "hard_or_thresholded"))
_m(id="confusion", name="Confusion matrix", unit="instance",
   summary="Counts of true/false normal and abnormal instance decisions.",
   limitation="A table, not a single ranking score. Still instance-level.",
   needs=("instance_labels", "hard_or_thresholded"))
_m(id="roc_auc", name="ROC-AUC", unit="instance",
   summary="Separation produced by a continuous anomaly score across thresholds.",
   limitation="Does not describe AD performance at the final selected threshold.",
   needs=("instance_labels", "scores"))
_m(id="pr_auc", name="PR-AUC", unit="instance",
   summary="Precision–recall area for a continuous anomaly score. Preferable under class imbalance.",
   limitation="Does not describe AD performance at the final selected threshold.",
   needs=("instance_labels", "scores"))
_m(id="brier", name="Brier score", unit="instance",
   summary="Accuracy of predicted probabilities for the abnormal class.",
   limitation="Requires probabilities, not only a ranking score.",
   needs=("instance_labels", "scores"))
_m(id="topk_acc", name="Top-k accuracy", unit="instance",
   summary="Whether the true class appears in the top-k ranked labels.",
   limitation="A ranking diagnostic, not a binary fault-detection result.",
   needs=("diagnostic_labels", "ranked_or_scores"))
_m(id="mrr", name="Mean reciprocal rank", unit="operational",
   summary="Ranking quality for ordered lists of assets or cases.",
   limitation="Requires a ranked list and a definition of a relevant item.",
   needs=("ranked",))
_m(id="prec_at_k", name="Precision @ k", unit="operational",
   summary="Fraction of the top-k ranked items that are relevant.",
   limitation="Depends on the review-list length k.",
   needs=("ranked",))
_m(id="rec_at_k", name="Recall @ k", unit="operational",
   summary="Fraction of relevant items captured in the top-k ranked list.",
   limitation="Depends on the review-list length k.",
   needs=("ranked",))

# Stability / nuisance
_m(id="fa_per_day", name="False alarms per day", unit="operational",
   summary="Rate of instance-level false anomaly detections over calendar or operating time.",
   limitation="Not the same as case-level false fault detections.",
   needs=("healthy_instances", "hard_or_thresholded"))
_m(id="alerts_asset_day", name="Alerts per asset-day", unit="operational",
   summary="Workload of alerts relative to assets and time, for maintenance review.",
   limitation="Needs a defined alert (instance alarm vs case-level fault detection).",
   needs=("hard_or_thresholded",))
_m(id="mtbfa", name="Mean time between false alarms", unit="operational",
   summary="Typical gap between instance-level false anomaly detections.",
   limitation="Sensitive to how consecutive alarms are merged.",
   needs=("healthy_instances", "hard_or_thresholded"))
_m(id="chatter", name="Chatter / transitions", unit="operational",
   summary="How often the alarm state switches, a nuisance/stability measure.",
   limitation="Does not by itself measure fault-detection quality.",
   needs=("hard_or_thresholded",))
_m(id="det_at_far", name="Detection rate at constrained FAR", unit="instance",
   summary="Detection of abnormal instances at a stated false-alarm rate constraint.",
   limitation="The FAR constraint must be declared.",
   needs=("instance_labels", "scores"))

# CARE pieces
_m(id="care_c", name="CARE Coverage (C)", unit="instance",
   summary="Detection of abnormal instances within faulty event windows.",
   limitation="Does not by itself measure healthy-case stability or case-level decisions.",
   needs=("event_windows", "instance_labels", "hard_or_thresholded"),
   citations=("Gück et al., 2024",), care_component="C")
_m(id="care_a", name="CARE Accuracy (A)", unit="instance",
   summary="Instance-level classification, including control of false anomaly detections in healthy cases.",
   limitation="Does not establish that anomalies persist enough to detect a faulty case.",
   needs=("instance_labels", "healthy_cases", "hard_or_thresholded"),
   citations=("Gück et al., 2024",), care_component="A")
_m(id="care_r", name="CARE Reliability (R)", unit="case",
   summary="Whether detected anomalies provide sufficient case-level evidence to distinguish faulty from healthy cases.",
   limitation="Depends on the selected persistence or fault-detection condition.",
   needs=("fd_condition", "healthy_cases", "faulty_cases"),
   citations=("Gück et al., 2024",), care_component="R")
_m(id="care_e", name="CARE Earliness (E)", unit="earliness",
   summary="Greater value to anomalies detected earlier in the faulty event window.",
   limitation="Requires a defined event window; does not by itself establish a fault detection.",
   needs=("event_windows", "hard_or_thresholded"),
   citations=("Gück et al., 2024",), care_component="E")
_m(id="care", name="Unified CARE score", unit="combined",
   summary="Weighted combination of Coverage, Accuracy, Reliability and Earliness for early wind-turbine fault detection.",
   limitation="Additive aggregation allows compensation. Report C, A, R and E alongside the unified score. Weights must be stated.",
   needs=("event_windows", "instance_labels", "healthy_cases", "fd_condition", "hard_or_thresholded"),
   citations=("Gück et al., 2024", "OECD et al., 2008"))

# Case-level / earliness
_m(id="faulty_detection_rate", name="Faulty-case detection rate", unit="case",
   summary="Proportion of faulty cases satisfying the fault-detection condition.",
   limitation="Does not show false fault detections in healthy cases.",
   needs=("fd_condition", "faulty_cases"))
_m(id="false_fd_rate", name="False fault-detection rate", unit="case",
   summary="Proportion of healthy cases satisfying the fault-detection condition.",
   limitation="Does not measure sensitivity to faulty cases.",
   needs=("fd_condition", "healthy_cases"))
_m(id="case_mcc", name="Case-level MCC / balanced accuracy", unit="case",
   summary="Uses faulty and healthy case decisions together.",
   limitation="Requires enough independent cases for stable interpretation.",
   needs=("fd_condition", "faulty_cases", "healthy_cases"))
_m(id="first_anomaly_time", name="First detected-anomaly time", unit="earliness",
   summary="When the first anomaly evidence appears.",
   limitation="A single anomaly does not necessarily represent a detected fault.",
   needs=("detection_point", "reference_event"))
_m(id="fd_time", name="Fault-detection time", unit="earliness",
   summary="Time at which the case-level fault-detection condition is first satisfied.",
   limitation="Depends on the selected persistence or evidence condition.",
   needs=("fd_condition", "detection_point", "reference_event"))
_m(id="warning_lead", name="Warning lead time", unit="earliness",
   summary="Time between a defined detection point and a later reference event.",
   limitation="Has no clear meaning unless both the detection point and reference event are stated.",
   needs=("detection_point", "reference_event"))
_m(id="lead_success", name="Lead-time success rate", unit="earliness",
   summary="Proportion of faulty cases detected before a specified minimum useful lead time.",
   limitation="Depends on an application-specific definition of useful warning.",
   needs=("detection_point", "reference_event", "useful_lead_time"))
_m(id="event_recall", name="Event recall / missed-event rate", unit="case",
   summary="Whether labelled events or faulty cases are detected at all.",
   limitation="Does not describe false detections or timing.",
   needs=("faulty_cases", "fd_condition"))
_m(id="mae_rul", name="MAE / RMSE of RUL or time-to-failure", unit="earliness",
   summary="Error in a remaining-useful-life or time-to-failure target. This is prognosis, not fault detection.",
   limitation="Requires a defined future reference event and a prognostic output.",
   needs=("prognostic_target",))
_m(id="prognostic_horizon", name="Prognostic horizon", unit="earliness",
   summary="How far ahead a prognostic estimate remains useful.",
   limitation="Represents prognosis rather than fault detection itself.",
   needs=("prognostic_target",))

# Cost
_m(id="expected_cost", name="Expected cost / net benefit", unit="operational",
   summary="Operational consequences of missed faulty cases, false fault detections, delay, inspection and downtime.",
   limitation="Requires explicit, usually site-specific, cost terms and a sensitivity check.",
   needs=("cost_terms",),
   citations=("Gück et al., 2024", "Kamariotis et al., 2024"))
_m(id="cost_weighted_error", name="Cost-weighted error", unit="operational",
   summary="Classification or detection error weighted by the declared cost terms.",
   limitation="The weights are the evaluation. Report them.",
   needs=("cost_terms", "hard_or_thresholded"))

# Diagnostic
_m(id="macro_f1", name="Macro F1 / per-class precision–recall", unit="instance",
   summary="Identification quality across fault types or components.",
   limitation="The diagnostic level must not be more specific than the ground truth.",
   needs=("diagnostic_labels",))
_m(id="diag_confusion", name="Diagnostic confusion matrix", unit="instance",
   summary="Per-class identification outcomes at the declared diagnostic level.",
   limitation="Do not interpret component-level labels as damage-mechanism labels.",
   needs=("diagnostic_labels",))
