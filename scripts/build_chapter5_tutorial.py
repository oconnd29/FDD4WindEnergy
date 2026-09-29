"""Build the bundled Chapter 5 Care to Compare tutorial project."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fdd_eval.domain.completeness import summarise
from fdd_eval.domain.project import Project
from fdd_eval.io.markdown_export import export_markdown
from fdd_eval.io.project_io import save_project

TUTORIAL_DIR = ROOT / "tutorials"


def chapter5_c2c() -> Project:
    p = Project()
    p.title = "Chapter 5 tutorial — Care to Compare (combined CARE)"
    p.notes = (
        "Worked example of how Chapter 5 maps onto the four-stage evaluation framework. "
        "The data source is the open Care to Compare (C2C) benchmark (Gück et al., 2024), "
        "farms A and B, generator-bearing and rotor-bearing cases. Chapter 5 also constructed "
        "Kelmarsh and Penmanshiel cases; those are omitted here so one open source can be "
        "followed end-to-end.\n\n"
        "The method is an NBM residual Monitoring Indicator (FFNN, LSTM or TCN) and, as a "
        "separate comparator, direct AD on the raw target temperature. Five AD Algorithms "
        "(SCC, EWMA-CC, CUSUM, KSCAD, BCAD) produce instance-level alarms. Combined "
        "detection performance is CARE (Coverage, Accuracy, Reliability, Earliness).\n\n"
        "Open this .fddx in FDD Evaluation and click through Inputs and Stages 1–4. This file "
        "is a protocol example, not a scored result table."
    )

    p.inputs.data_types = ["data_scada", "data_alarms"]
    p.inputs.records = ["rec_operator", "rec_expert", "rec_logbook", "rec_service"]
    p.inputs.method = "method_nbm"
    p.inputs.method_notes = (
        "Decoupled NBM–AD pipeline from Chapter 5. An NBM (FFNN, LSTM or TCN) is trained "
        "on the healthy training period of each case to estimate the target bearing temperature. "
        "The residual is the Monitoring Indicator for residual-based AD. Direct AD on the raw "
        "target temperature is retained as a second Monitoring Indicator so residual monitoring "
        "can be compared with AD on the measured series. AD Algorithms: SCC, EWMA-CC, "
        "CUSUM, KSCAD and BCAD. Each AD Algorithm is fitted on the healthy training period "
        "and applied to the test period, producing a binary alarm sequence a_t."
    )

    p.stage1.primary_objective = "obj_early_warning"
    p.stage1.early_warning.reference_event = (
        "Recorded C2C fault event that ends the expert-defined pre-fault event window "
        "(component fault associated with generator-bearing or rotor-bearing temperature)."
    )
    p.stage1.early_warning.detection_point = "detect_fd_condition"
    p.stage1.early_warning.notes = (
        "Early Warning: obtain sufficient anomaly evidence before the recorded fault while "
        "remaining stable on matched healthy cases. Lead time is taken from the first time "
        "the case-level fault-detection condition is satisfied, not from the first isolated "
        "detected anomaly. CARE Earliness still rewards earlier instance-level evidence inside "
        "the event window."
    )

    p.stage2.fault_definition = (
        "Generator-bearing and rotor-bearing faults on C2C farms A and B. Farm A supplies "
        "generator-bearing cases; farm B supplies rotor-bearing cases. The evaluation represents "
        "component-level bearing faults, not a specific damage mechanism."
    )
    p.stage2.labelled_level = (
        "Component (generator bearing / rotor bearing). Not a finer damage-mechanism label."
    )
    p.stage2.evidence_tier = "tier_combined"
    p.stage2.evidence_sources = ["rec_operator", "rec_expert", "rec_logbook", "rec_service"]
    p.stage2.label_representation = "label_interval"
    p.stage2.uncertainty.evidence_certainty = "cert_categorical"
    p.stage2.uncertainty.timing_certainty = "time_interval"
    p.stage2.uncertainty.source_agreement = "agree_consistent"
    p.stage2.uncertainty.label_stability = "stab_stable"
    p.stage2.healthy_case_evidence = (
        "C2C normal-behaviour datasets are labelled by a combination of wind-farm operator "
        "feedback, manual inspection of the data, and expert knowledge (Gück et al., 2024, §3.3). "
        "Five healthy C2C cases were selected to balance the five faulty cases across farms and "
        "target-signal types. Absence of a recorded fault is not used on its own."
    )
    p.stage2.circular_risk = True
    p.stage2.notes = (
        "Anomaly-event labels come from operator feedback or documented faults (service reports "
        "and fault logbooks). For farm A the EDP logbook gives fault start timestamps only; "
        "pre-fault window starts were then inferred by analysing the data before each fault, "
        "and the authors note that the true starts can differ. For farms B and C, starts were "
        "set from data analysis, operator feedback, service reports and expert knowledge; they "
        "state it is unlikely that events start too early, and that a true start could be earlier "
        "than labelled. The paper does not publish the exact numerical conditions used to place "
        "the pre-fault window start. Because operational data contributed to placing some window "
        "starts, circular evaluation is flagged as a risk if the same series is also scored."
    )

    p.stage3.case_construction = "case_predefined"
    p.stage3.case_notes = (
        "C2C subset used in Chapter 5: 5 faulty and 5 healthy cases (2 generator-bearing "
        "pairs on farm A, 3 rotor-bearing pairs on farm B). Each case has approximately one "
        "year of training data followed by a test period (C2C 'prediction period'). Target "
        "signals: generator-bearing temperature (farm A) and rotor-bearing temperature (farm B). "
        "Access: Gück et al. (2024), CARE to Compare, Data 9(12):138."
    )
    p.stage3.event_windows.defined = True
    p.stage3.event_windows.window_kind = "window_prefault"
    p.stage3.event_windows.boundaries = (
        "C2C requirement 7: every anomaly has an assigned start; the anomaly end is the start "
        "of a turbine fault (Gück et al., 2024). The labelled interval is therefore a pre-fault "
        "window (anomalies that led up to faults), not a fault window of the downtime itself. "
        "Original C2C starts and ends were retained in Chapter 5."
    )
    p.stage3.event_windows.reference_event = (
        "Start of the turbine fault (end of the pre-fault window)."
    )
    p.stage3.event_windows.timing_rules = (
        "Window start: expert / operator / logbook-assisted placement. Exact onset conditions "
        "are not published. Farm A: possible starts inferred from data before the logbook fault "
        "time; true starts can differ. Farms B/C: authors consider it unlikely that labelled "
        "starts are too early; a true start could be earlier. Do not read the window start as "
        "known physical onset. Padding before and after the event is present in C2C so the "
        "label cannot be guessed from test-period length."
    )
    p.stage3.comparison = "cmp_pairs"
    p.stage3.data_periods.training = (
        "Approximately one year of healthy training data at the start of each C2C case. "
        "Used to train the NBM (when residual monitoring is used) and to fit AD Algorithm "
        "limits / reference statistics. Not used as the CARE evaluation interval."
    )
    p.stage3.data_periods.validation = (
        "AD Algorithm hyperparameters are not fit by inspecting the evaluated pair under "
        "held-out tuning. Oracle tuning (reported in Chapter 5 as an upper reference) may "
        "use the evaluated pair; that is a different, explicitly labelled analysis."
    )
    p.stage3.data_periods.test = (
        "C2C test period (called the prediction period in the CARE to Compare release). "
        "Contains the pre-fault event window for faulty cases and a comparable healthy "
        "window for matched healthy cases. CARE is computed on this period."
    )
    p.stage3.valid_data_rules = (
        "Use the C2C-provided case series as released for the selected cases. Instances "
        "without a finite monitoring indicator (missing target or residual) are excluded "
        "from instance-level CARE terms. Shutdown / out-of-scope handling follows the C2C "
        "case construction; additional farm-level maintenance filters are not re-applied "
        "beyond the supplied case boundaries."
    )
    p.stage3.tuning_mode = "tune_heldout"
    p.stage3.tuning_inventory = "inv_all"
    p.stage3.tuning_notes = (
        "Primary protocol for this tutorial is held-out tuning: the evaluated faulty–healthy "
        "pair is excluded from the tuning inventory before selected hyperparameters are applied. "
        "Chapter 5 compared fault-type, farm-specific and all-case inventories; this example "
        "records the all-case inventory. Oracle tuning is reported in the chapter as achievable "
        "performance, not as deployment performance, and is not the protocol claimed here."
    )
    p.stage3.fd_condition = "fd_persistence"
    p.stage3.fd_condition_notes = (
        "Case-level fault detection follows CARE Reliability: detected anomalies must persist "
        "sufficiently, using the persistence threshold κ, before a case is a detected fault. "
        "The same condition is applied to faulty and healthy cases. A single detected anomaly "
        "is not a detected fault. Detection time for warning lead time is the first instance "
        "at which this persistence condition is satisfied."
    )

    p.stage4.output_class = "out_binary"
    p.stage4.output_score = "out_hard"
    p.stage4.include_stability = "no_stability"
    p.stage4.accepted_metrics = [
        "care",
        "care_c",
        "care_a",
        "care_r",
        "care_e",
        "faulty_detection_rate",
        "false_fd_rate",
        "fd_time",
        "warning_lead",
        "precision",
        "recall",
        "f1",
    ]
    p.stage4.rejected_metrics = ["balanced_accuracy", "mcc"]
    p.stage4.override_notes = (
        "Combined detection performance is the unified CARE score, always reported with C, A, "
        "R and E so a high component cannot hide a weak one. Precision, recall and F1 are "
        "kept as instance-level AD summaries at the operating threshold. Balanced accuracy "
        "and MCC were rejected as extra instance scores because CARE Accuracy already "
        "summarises instance-level behaviour including healthy cases. No separate nuisance "
        "rate was added; healthy-case false anomaly detections enter CARE Accuracy and "
        "false fault detections enter Reliability / the false fault-detection rate."
    )

    p.reproducibility.followed = [
        "data_source",
        "preprocessing",
        "split_trace",
        "settings",
        "gt_provenance",
        "report",
    ]
    p.reproducibility.skipped = ["environment"]
    p.reproducibility.notes = (
        "C2C: Gück, Roelofs and Faulstich (2024), CARE to Compare, Data 9(12):138. "
        "NBM training, AD hyperparameters, κ and CARE weights belong with any later score "
        "tables (Chapter 5). Environment pinning is skipped in this protocol-only tutorial "
        "because scores are not computed inside the v1 app."
    )
    return p


def main() -> None:
    TUTORIAL_DIR.mkdir(parents=True, exist_ok=True)
    project = chapter5_c2c()
    fddx = TUTORIAL_DIR / "chapter5_c2c_care.fddx"
    md = TUTORIAL_DIR / "chapter5_c2c_care.md"
    save_project(project, fddx)
    md.write_text(export_markdown(project), encoding="utf-8")
    c = summarise(project)
    print(f"Wrote {fddx}")
    print(f"Wrote {md}")
    print(f"Completeness {c.required_done}/{c.required_total}")
    if c.missing_required:
        for nid, msg in c.missing_required:
            print(" missing:", nid, msg)


if __name__ == "__main__":
    main()
