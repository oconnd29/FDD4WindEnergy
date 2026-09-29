"""Choice catalog: selectable options with icon family and 'i' panel text."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Choice:
    id: str
    label: str
    family: str
    icon: str
    definition: str
    contrast: str = ""
    when: str = ""
    citations: tuple[str, ...] = ()


def by_id(choice_id: str) -> Choice:
    return CHOICES[choice_id]


def group(*ids: str) -> list[Choice]:
    return [CHOICES[i] for i in ids]


CHOICES: dict[str, Choice] = {}


def _add(choice: Choice) -> Choice:
    CHOICES[choice.id] = choice
    return choice


# --- Data types (Inputs) ---
_add(Choice(
    "data_scada", "Turbine SCADA", "data_type", "data_scada",
    "Routinely collected Supervisory Control and Data Acquisition records from the turbine, typically 10-minute operational features such as temperatures, power and rotational speed.",
    "SCADA is one operational source, not the framework. The same evaluation stages apply if the Monitoring Indicator comes from another measurement family.",
    "Use when the method under evaluation consumes turbine SCADA features or SCADA-derived residuals.",
    ("Tautz-Weinert and Watson, 2017", "Chesterman et al., 2023"),
))
_add(Choice(
    "data_vibration", "Vibration / CMS", "data_type", "data_vibration",
    "Condition-monitoring measurements of vibration or related high-frequency component behaviour, whether from a dedicated CMS or another sensor chain.",
    "Not the same as SCADA temperature or power. A method may use both; record each source separately.",
    "Use when vibration or CMS channels contribute to the Monitoring Indicator or to ground-truth evidence.",
))
_add(Choice(
    "data_alarms", "Alarm / status streams", "data_type", "data_alarms",
    "Turbine alarm, warning or status records that describe OEM or farm-level events over time.",
    "Alarms may be evidence for ground truth, inputs to a method, or neither. Using the same alarm both to label a fault and to score the method risks circular evaluation.",
    "Use when alarm or status streams are available as data, evidence, or both.",
    ("Leahy et al., 2018a",),
))
_add(Choice(
    "data_metmast", "Met-mast / meteorological", "data_type", "data_metmast",
    "Site meteorological measurements such as a met mast, or other environmental series used as context for turbine behaviour.",
    "These are not component-condition measurements. They may still be required as context for an NBM or as an operating-condition filter.",
    "Use when meteorological series are part of the method or of the valid-evaluation rules.",
))
_add(Choice(
    "data_other_ts", "Other time series", "data_type", "data_other",
    "Any other regularly sampled operational series used in the evaluation (for example additional sensors or derived indicators).",
    "Name the series in the notes so the protocol remains interpretable.",
    "Use when the evaluation uses monitoring data that does not fit the named families above.",
))

# --- Evidence / records ---
_add(Choice(
    "rec_operator", "Operator feedback", "record", "tier_b",
    "Direct feedback from the wind-farm operator used to confirm that a period is faulty or healthy.",
    "Operator confirmation is not the same as a published rule for when a pre-fault window starts.",
    "Used in Care to Compare for both anomaly events and normal-behaviour datasets (Gück et al., 2024).",
    ("Gück et al., 2024",),
))
_add(Choice(
    "rec_expert", "Expert analysis", "record", "tier_c",
    "Expert review of operational data, typically to place a pre-fault window relative to a later recorded fault. The exact numerical conditions used to set the window start are often not published.",
    "Expert-defined does not mean the physical onset is known, and it does not mean the labelling rule can be reproduced from the paper alone.",
    "Care to Compare places anomaly-event starts using expert knowledge together with operator feedback, service reports and/or fault logbooks. The end of the event is the start of the turbine fault.",
    ("Gück et al., 2024",),
))
_add(Choice(
    "rec_logbook", "Fault logbook", "record", "tier_a",
    "A fault logbook giving documented fault times. In Care to Compare farm A (EDP), the logbook supplies fault start timestamps only; pre-fault window starts were then inferred by analysing the data before each fault.",
    "A logbook start is a fault (or downtime) time, not automatically the start of abnormal behaviour. The true pre-fault onset can differ from the labelled window start.",
    "Use when documented fault times are the reference event that ends a pre-fault window.",
    ("Gück et al., 2024",),
))
_add(Choice(
    "rec_service", "Service reports", "record", "tier_a",
    "Service-report documents used as fault or maintenance evidence, as in Care to Compare farms B and C.",
    "A service report supports that a fault or intervention occurred. It rarely specifies a unique onset time for earlier abnormal behaviour.",
    "Use when service reports contribute to the case label or reference event.",
    ("Gück et al., 2024",),
))
_add(Choice(
    "rec_inspection", "Technician / inspection logs", "record", "tier_a",
    "Written or structured records of inspection, technician findings or confirmed component condition.",
    "Stronger as ground-truth evidence than a SCADA deviation alone, but timing certainty still depends on when the inspection occurred.",
    "Typical Tier A evidence when it confirms a condition or action.",
    ("Leahy et al., 2018a",),
))
_add(Choice(
    "rec_maintenance", "Maintenance actions", "record", "tier_a",
    "Work orders, repairs, replacements or other maintenance actions used as events or evidence.",
    "A maintenance action is a reference event, not automatically the physical onset of degradation.",
    "Use as a reference event, as evidence of a confirmed action, or both.",
))
_add(Choice(
    "rec_replacement", "Component replacements", "record", "tier_a",
    "Records that a component was replaced. This can confirm that a faulted part was present, but does not by itself locate onset.",
    "Replacement dates are often used as reference events for Early Warning. They are not instance-level abnormal labels.",
    "Use when replacements are the operational event against which detection is judged.",
))

# --- Cost inputs ---
_add(Choice(
    "cost_dispatch", "Maintenance dispatch cost", "cost", "operational",
    "The site-specific cost of sending a maintenance team, used when the evaluation includes operational or cost/impact measures.",
    "This is evaluation input, not a monitoring signal. Values are usually site-specific and should be reported with a sensitivity check.",
    "Needed for Cost / Impact Optimisation and for some Maintenance Planning operational measures.",
    ("Gück et al., 2024", "Kamariotis et al., 2024"),
))
_add(Choice(
    "cost_inspection", "Inspection cost", "cost", "operational",
    "Cost of an inspection triggered by a fault detection or false fault detection.",
    "Distinct from missed-fault and downtime costs.",
    "Include when inspection is the operational response to a detection.",
))
_add(Choice(
    "cost_downtime", "Downtime / lost production", "cost", "operational",
    "Cost or lost production associated with downtime, late detection or a missed faulty case.",
    "Site-specific. The protocol should record the assumption, not treat it as a universal constant.",
    "Include when missed or late detections have a stated production consequence.",
))
_add(Choice(
    "cost_false_positive", "False fault-detection cost", "cost", "operational",
    "Cost of acting on a healthy case that satisfied the fault-detection condition.",
    "This is a case-level cost, not the cost of a single instance-level anomaly alarm.",
    "Include when false fault detections drive inspections or dispatch.",
))
_add(Choice(
    "cost_other", "Other site-specific costs", "cost", "operational",
    "Further cost or utility terms required by the evaluation objective (opportunity cost, component replacement, and similar).",
    "Name each term in the notes. Do not invent values inside this software.",
    "Use when the cost model needs terms beyond dispatch, inspection and downtime.",
))

# --- Method under evaluation ---
_add(Choice(
    "method_ad", "AD Algorithm", "method", "instance",
    "An Anomaly Detection Algorithm that assigns a normal/abnormal decision or an anomaly score to instances of a Monitoring Indicator.",
    "AD performance is instance-level. It is not by itself fault-detection performance.",
    "Use when the evaluated output is detected anomalies at instance level.",
))
_add(Choice(
    "method_nbm", "NBM-based pipeline", "method", "instance",
    "A Normal Behaviour Model estimates expected healthy behaviour; a Monitoring Indicator (often a residual) is then processed by an AD Algorithm.",
    "The NBM is part of the method, not the evaluation protocol. Estimation performance and detection performance are not interchangeable.",
    "The experimental chapters of the thesis follow this route.",
    ("Chesterman et al., 2023",),
))
_add(Choice(
    "method_direct_ad", "Direct AD on operational data", "method", "instance",
    "Anomaly detection applied to operational features without an NBM residual as the Monitoring Indicator.",
    "The evaluation stages remain the same; only the method being evaluated changes.",
    "Use when the method detects anomalies directly from the measured series.",
))
_add(Choice(
    "method_diagnostic", "Diagnostic model", "method", "diagnostic",
    "A method that identifies fault type, component or subsystem after (or instead of) binary fault detection.",
    "Requires diagnostic-level ground truth. Do not claim a finer diagnostic level than the labels support.",
    "Use when Diagnostic Quality is an evaluation objective.",
))
_add(Choice(
    "method_other", "Other fault-detection method", "method", "combined",
    "Any other route through the fault-detection process, including classifiers or hybrid pipelines.",
    "Describe the method output type so Stage 4 can recommend appropriate metrics.",
    "Use when the method does not fit the named families.",
))

# --- Objectives ---
_add(Choice(
    "obj_early_warning", "Early Warning", "objective", "early_warning",
    "Obtain sufficient anomaly evidence to support fault detection before a later reference event, while avoiding equivalent fault-detection behaviour in healthy cases.",
    "Warning lead time from the first detected anomaly is not the same as lead time from the first satisfied fault-detection condition. Both must be defined.",
    "The main objective examined in Chapters 5 and 6. CARE is one way to evaluate it.",
    ("Gück et al., 2024",),
))
_add(Choice(
    "obj_maintenance", "Maintenance Planning", "objective", "maintenance",
    "Support a planning decision: which turbines or components require attention within a useful warning period, at an acceptable rate of false fault detections.",
    "More detected anomalies are not necessarily more useful if they produce excessive false fault detections.",
    "Select when the evaluation should represent workload, prioritisation or a planning horizon.",
))
_add(Choice(
    "obj_diagnostic", "Diagnostic Quality", "objective", "diagnostic",
    "Evaluate whether the correct fault type, component or subsystem is identified after sufficient evidence of a fault has been established.",
    "This is fault identification, not fault detection. The diagnostic level must not exceed the available ground truth.",
    "Select when the method is judged on identification, not only on detecting a faulty case.",
))
_add(Choice(
    "obj_cost", "Cost / Impact Optimisation", "objective", "cost",
    "Evaluate the operational consequences of detections: missed faulty cases, false fault detections, late detection, inspection, maintenance and downtime.",
    "Preferred trade-offs depend on site-specific costs or utilities. Those values must be stated and tested for sensitivity.",
    "Select when methods are compared by expected cost, utility or net benefit.",
    ("Gück et al., 2024", "Kamariotis et al., 2024", "Begun and Schlickewei, 2024"),
))

# --- Detection point ---
_add(Choice(
    "detect_first_anomaly", "First detected anomaly", "detection_point", "instance",
    "Detection time is the first instance classified as abnormal (or the first anomaly score exceeding the operating threshold).",
    "A single detected anomaly is not automatically a detected fault. Do not report this as warning lead time for case-level fault detection.",
    "Use when the question is when anomaly evidence first appears.",
))
_add(Choice(
    "detect_fd_condition", "First satisfied fault-detection condition", "detection_point", "case",
    "Detection time is the first moment the case-level fault-detection condition is met (number, persistence, density or temporal pattern of detected anomalies).",
    "This is later than, or equal to, the first detected anomaly. It is the appropriate point when the objective is fault detection rather than any anomaly evidence.",
    "Use when Early Warning or Maintenance Planning is judged on a declared fault detection.",
))

# --- Evidence tiers ---
_add(Choice(
    "tier_a", "Tier A — condition-based", "evidence_tier", "tier_a",
    "Direct evidence of a confirmed condition or action: inspection, replacement, or another recorded confirmation of the faulted state.",
    "Strongest evidence class in this framework. Timing of physical onset may still be uncertain.",
    "Use when labels rest on confirmed condition or maintenance action.",
    ("Wu and Keogh, 2023",),
))
_add(Choice(
    "tier_b", "Tier B — strong proxy / multi-source", "evidence_tier", "tier_b",
    "Strong proxy evidence, or agreement between independent sources (for example alarms plus maintenance records).",
    "Not a confirmed physical inspection, but stronger than a single behavioural symptom.",
    "Use when several independent records support the label.",
))
_add(Choice(
    "tier_c", "Tier C — symptom / behaviour", "evidence_tier", "tier_c",
    "A fault-related label inferred principally from measured behaviour: a sustained deviation, threshold exceedance or detected change point.",
    "Risk of circular evaluation if the same behaviour both defines the label and is scored by the method.",
    "If selected, the symptom definition (rule, change-point, or multi-indicator) must be documented.",
    ("Frénay and Verleysen, 2014", "Wu and Keogh, 2023"),
))
_add(Choice(
    "tier_combined", "Combined tiers", "evidence_tier", "combined",
    "Different cases, or the same case, draw on more than one evidence tier. Record the mix so cases are not treated as equivalent without explanation.",
    "Combining tiers does not raise every case to Tier A.",
    "Use when the inventory is heterogeneous, as in Chapter 5 (Care to Compare plus constructed farm cases).",
))
_add(Choice(
    "tier_none", "Unlabelled / no direct ground truth", "evidence_tier", "unlabelled",
    "No direct ground-truth label is available. Evaluation may still use stability metrics, synthetic faults or expert review, but standard detection metrics are not valid.",
    "Absence of a recorded fault is not confirmation of healthy operation.",
    "Use when the protocol must proceed without event labels, and document what can still be claimed.",
))

# --- Tier C methods ---
_add(Choice(
    "symptom_rule", "Rule-based symptoms", "symptom", "tier_c",
    "Labels are defined by explicit rules, thresholds and durations on measured signals.",
    "Transparent, but evaluation of a method that implements a similar rule may be circular.",
    "Document signals, thresholds, duration and exceptions.",
))
_add(Choice(
    "symptom_cpd", "Statistical change point", "symptom", "tier_c",
    "Onset or abnormal intervals are inferred from a change score, threshold and duration.",
    "The change-point procedure is part of the ground truth, not part of the evaluated AD Algorithm, unless that is intended.",
    "Document the change score, threshold and minimum duration.",
))
_add(Choice(
    "symptom_multi", "Multiple indicators", "symptom", "tier_c",
    "A fault label is assigned when more than k indicators agree for longer than a stated duration.",
    "Agreement rules can hide disagreement. Record which indicators and the value of k.",
    "Use when several behavioural symptoms are required together.",
))

# --- Label representation ---
_add(Choice(
    "label_binary", "Binary labels (deterministic)", "label", "label_hard",
    "Each instance or case is labelled normal or abnormal / healthy or faulty with no confidence attached.",
    "Hides timing and evidence uncertainty. Common, but not always faithful to the records.",
    "Use when the evaluation treats labels as hard decisions.",
))
_add(Choice(
    "label_soft", "Soft labels (confidence)", "label", "label_soft",
    "Labels carry a numeric, categorical or fuzzy confidence reflecting evidence certainty.",
    "Requires metrics that can use probabilities or weights. Do not compute unweighted hard-label metrics without stating the binarisation rule.",
    "Use when evidence certainty should remain in the evaluation.",
))
_add(Choice(
    "label_interval", "Interval labels (temporal ranges)", "label", "label_interval",
    "Abnormality is represented as a time range rather than a single onset point (onset interval or event window).",
    "An evaluation interval is not a claim of physical onset unless the evidence supports that claim.",
    "Use when timing is an interval, including the constructed event windows in Chapter 5.",
))

# --- Uncertainty ---
_add(Choice(
    "cert_numeric", "Numeric certainty", "evidence_certainty", "label_soft",
    "Evidence certainty is recorded as a number (probability, score or similar).",
))
_add(Choice(
    "cert_categorical", "Categorical certainty", "evidence_certainty", "label_soft",
    "Evidence certainty is recorded as categories (for example high / medium / low).",
))
_add(Choice(
    "cert_fuzzy", "Fuzzy certainty", "evidence_certainty", "label_soft",
    "Evidence certainty is recorded with fuzzy membership rather than a single crisp value.",
))
_add(Choice(
    "time_point", "Point timing", "timing", "instance",
    "A single timestamp is treated as the reference event or onset.",
    "Only appropriate when the records actually support a point event (for example a replacement date used as a reference event, not as physical onset).",
))
_add(Choice(
    "time_interval", "Onset interval", "timing", "label_interval",
    "Onset is known only to lie within an interval. Event windows should not imply greater precision.",
))
_add(Choice(
    "time_unknown", "Unknown timing", "timing", "unlabelled",
    "Physical onset is not known. A consistent evaluation interval may still be defined, as in the Kelmarsh and Penmanshiel cases.",
    "Do not interpret the window start as degradation onset.",
    "Chapter 5 used common event-window durations for comparability, not as physical-onset estimates.",
))
_add(Choice(
    "agree_single", "Single source", "agreement", "tier_c",
    "The label rests on one evidence source.",
))
_add(Choice(
    "agree_consistent", "Consistent sources", "agreement", "tier_b",
    "Independent sources agree on the case label or timing.",
))
_add(Choice(
    "agree_conflict", "Conflicting sources", "agreement", "unlabelled",
    "Sources disagree. Record the conflict; do not silently pick one.",
))
_add(Choice(
    "stab_stable", "Stable labels", "stability", "tier_a",
    "Repeated application of the labelling rule, or expert review, yields stable labels.",
))
_add(Choice(
    "stab_unstable", "Unstable / to be quantified", "stability", "unlabelled",
    "Labels may change with small rule changes or reviewer differences. Quantify if possible; otherwise report the limitation.",
))

# --- Case construction / comparison / tuning ---
_add(Choice(
    "window_prefault", "Pre-fault window", "window_kind", "earliness",
    "The evaluation interval is a pre-fault (anomaly) window: labelled abnormal behaviour that leads up to a later turbine fault. In Care to Compare, the window end is the start of the turbine fault, not the fault period itself.",
    "This is not a fault window. Instance-level labels inside the window describe developing abnormal behaviour before the fault, not the downtime or faulted operating state after detection by other systems.",
    "Use for Early Warning and CARE-style evaluation. Record that the exact onset rule may be expert-defined and not fully published.",
    ("Gück et al., 2024",),
))
_add(Choice(
    "window_fault", "Fault window", "window_kind", "case",
    "The evaluation interval is the faulted period itself (downtime, confirmed faulted operation, or the interval after the fault is already known to other systems).",
    "A fault window answers a different question from Early Warning. Detecting a fault that is already visible in status or alarms is not the same as detecting the pre-fault anomaly.",
    "Use only when the objective is to detect the faulted state rather than the developing period before it.",
))
_add(Choice(
    "window_other", "Other evaluation interval", "window_kind", "label_interval",
    "An evaluation interval that is neither a pre-fault window nor a fault window (for example a fixed-length constructed window when onset is unknown).",
    "State whether the interval is intended as onset, as a conservative evaluation window, or as something else. Chapter 5 Kelmarsh/Penmanshiel windows are evaluation intervals, not physical-onset labels.",
))
_add(Choice(
    "case_predefined", "Pre-defined cases", "case_construction", "case",
    "Cases (including event windows) are supplied by the dataset, such as Care to Compare.",
    "Still record the case label, boundaries and evidence. Pre-defined does not mean uncertainty-free.",
    "Chapter 5 used Care to Compare as pre-defined cases.",
    ("Gück et al., 2024",),
))
_add(Choice(
    "case_constructed", "Constructed cases", "case_construction", "case",
    "Faulty and healthy cases are built from a continuous turbine record using the available evidence.",
    "Construction rules are part of the evaluation result and must be documented.",
    "Chapter 5 constructed Kelmarsh and Penmanshiel cases from SCADA, alarm and maintenance records.",
))
_add(Choice(
    "cmp_pairs", "Faulty–healthy pairs", "comparison", "case",
    "Each faulty case is matched to a healthy case so the same AD Algorithm setting is assessed for fault response and false-detection behaviour.",
    "Faulty cases alone cannot show whether detections are specific.",
    "The comparison used in Chapters 5 and 6.",
))
_add(Choice(
    "cmp_matching", "Matching without strict pairs", "comparison", "case",
    "Healthy and faulty cases are matched on operating context (site, season, load) but not necessarily one-to-one pairs.",
))
_add(Choice(
    "cmp_group", "Case grouping", "comparison", "case",
    "Cases are grouped (for example by fault type or farm) and compared at group level.",
    "State the grouping rule before metrics are calculated.",
))
_add(Choice(
    "tune_oracle", "Oracle tuning", "tuning", "oracle",
    "Hyperparameters may be selected using the evaluated cases. This indicates achievable performance in an ideal tuning scenario, not deployment.",
    "Oracle results should not be reported as if they were held-out deployment performance.",
    "Chapter 5 reports oracle tuning as an upper reference.",
))
_add(Choice(
    "tune_heldout", "Held-out tuning", "tuning", "heldout",
    "The evaluated faulty–healthy pair (or case) is excluded from the tuning inventory before selected hyperparameters are applied.",
    "This is the appropriate analogue of performance in deployment.",
    "Report the composition of the tuning inventory (fault-type, farm-specific, all-case, or other).",
))
_add(Choice(
    "inv_fault_type", "Fault-type inventory", "inventory", "heldout",
    "Tuning uses other cases of the same fault type.",
))
_add(Choice(
    "inv_farm", "Farm-specific inventory", "inventory", "heldout",
    "Tuning uses other cases from the same farm.",
))
_add(Choice(
    "inv_all", "All-case inventory", "inventory", "heldout",
    "Tuning uses the remaining cases in the full inventory.",
))

# --- Fault-detection condition ---
_add(Choice(
    "fd_count", "Count of detected anomalies", "fd_condition", "case",
    "A case is a detected fault when the number of detected anomalies reaches a stated threshold.",
    "A single detected anomaly is not automatically a detected fault unless the threshold is one — and that choice should be explicit.",
))
_add(Choice(
    "fd_persistence", "Persistence / consecutive evidence", "fd_condition", "case",
    "A case is a detected fault when detected anomalies persist for a stated run length or duration (the persistence threshold κ in the thesis notation).",
    "Used conceptually in CARE Reliability. State κ and apply it to faulty and healthy cases alike.",
    ("Gück et al., 2024",),
))
_add(Choice(
    "fd_density", "Density of detected anomalies", "fd_condition", "case",
    "A case is a detected fault when the fraction or rate of detected anomalies in a window exceeds a threshold.",
))
_add(Choice(
    "fd_pattern", "Temporal pattern", "fd_condition", "case",
    "A case is a detected fault when detected anomalies follow a stated temporal pattern (for example clustered bursts).",
    "The pattern definition must be fixed before performance is calculated.",
))

# --- Output types for Stage 4 ---
_add(Choice(
    "out_binary", "Binary class", "output_class", "label_hard",
    "The method distinguishes two classes (normal/abnormal or healthy/faulty).",
))
_add(Choice(
    "out_multiclass", "Multi-class", "output_class", "diagnostic",
    "The method distinguishes more than two mutually exclusive classes (for example fault types).",
    "Requires diagnostic-level ground truth.",
))
_add(Choice(
    "out_multilabel", "Multi-label", "output_class", "diagnostic",
    "Several labels may apply at once.",
))
_add(Choice(
    "out_hard", "Hard label", "output_score", "label_hard",
    "The operating output is a discrete decision (alarm / no alarm, or class id).",
    "Threshold-independent metrics such as ROC-AUC are not the right summary of this operating point, though they may still describe an underlying score.",
))
_add(Choice(
    "out_score", "Score / probability", "output_score", "label_soft",
    "The method produces a continuous anomaly score or class probability. A threshold may still be applied for alarms.",
    "ROC-AUC and PR-AUC describe separation across thresholds, not performance at the selected threshold.",
))
_add(Choice(
    "out_ranked", "Ranked list", "output_score", "maintenance",
    "The method ranks assets or cases for attention (for example for a maintenance review).",
    "Natural for Maintenance Planning. Metrics include precision@k, recall@k and mean reciprocal rank.",
))

# --- Evaluation units (also used as metric icons) ---
_add(Choice(
    "unit_instance", "Instance-level AD performance", "eval_unit", "instance",
    "How well the AD Algorithm distinguishes normal and abnormal instances. This is AD performance, not fault-detection performance.",
    "Good instance-level classification does not establish that detected anomalies provide sufficient evidence of a fault within a case.",
    ("Tatbul et al., 2018",),
))
_add(Choice(
    "unit_case", "Case-level fault-detection performance", "eval_unit", "case",
    "Whether the fault-detection condition distinguishes faulty cases from healthy cases. Each case contributes one outcome.",
    "Requires a stated fault-detection condition and, for false fault detections, healthy cases.",
))
_add(Choice(
    "unit_earliness", "Detection earliness", "eval_unit", "earliness",
    "When the relevant anomaly evidence or fault-detection condition occurs relative to a reference event.",
    "Has no clear meaning unless both the detection point and the reference event are stated.",
))
_add(Choice(
    "unit_combined", "Combined detection performance", "eval_unit", "combined",
    "Two or more of instance-level AD performance, case-level fault detection and earliness, aggregated under a stated rule.",
    "A combined score can hide a weak component. Report components as well. Additive aggregation allows compensation; geometric aggregation reduces it.",
    ("Gück et al., 2024", "OECD et al., 2008"),
))
_add(Choice(
    "unit_operational", "Operational measures", "eval_unit", "operational",
    "Workload, nuisance, ranking or cost quantities that correspond to the Stage 1 decision, rather than to technical detection alone.",
    "Include because the objective requires them, not because they are generally useful.",
))
_add(Choice(
    "yes_stability", "Include stability / nuisance measures", "stability_q", "operational",
    "Also report chatter, false alarms per day, mean time between false alarms, or similar nuisance behaviour.",
    "Instance-level false anomaly detections are not the same as case-level false fault detections.",
))
_add(Choice(
    "no_stability", "No additional stability measure", "stability_q", "operational",
    "Do not add a dedicated nuisance metric beyond what the selected detection metrics already include.",
))
