"""Inspector forms for each framework node."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import (
    QCheckBox,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from fdd_eval.domain.advisor import recommend, required_dimensions
from fdd_eval.domain.choices import CHOICES
from fdd_eval.domain.glossary import GLOSSARY
from fdd_eval.domain.project import Project
from fdd_eval.ui.widgets import ChoiceGroup, InfoDialog, choice_html, labelled_group


def _text(on_edit: Callable[[str], None], value: str, placeholder: str = "", multi: bool = False) -> QWidget:
    if multi:
        w = QPlainTextEdit()
        w.setPlainText(value)
        w.setPlaceholderText(placeholder)
        w.setMaximumHeight(110)
        w.textChanged.connect(lambda: on_edit(w.toPlainText()))
        return w
    w = QLineEdit()
    w.setText(value)
    w.setPlaceholderText(placeholder)
    w.textChanged.connect(on_edit)
    return w


class Inspector(QWidget):
    def __init__(self, project: Project, node_id: str, on_change: Callable[[], None]) -> None:
        super().__init__()
        self.project = project
        self.node_id = node_id
        self.on_change = on_change
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(4, 4, 4, 4)
        self._build()
        self.layout.addStretch(1)

    def _note(self, text: str) -> None:
        lab = QLabel(text)
        lab.setObjectName("Hint")
        lab.setWordWrap(True)
        self.layout.addWidget(lab)

    def _title(self, text: str) -> None:
        lab = QLabel(text)
        lab.setObjectName("SectionTitle")
        lab.setWordWrap(True)
        self.layout.addWidget(lab)

    def _group(self, title: str, ids: list[str], getter, setter, *, exclusive=True, hint="") -> ChoiceGroup:
        g = ChoiceGroup(ids, exclusive=exclusive)
        if exclusive:
            g.set_value(getter() or "")
            g.changed.connect(lambda: self._set(lambda: setter(g.value())))
        else:
            g.set_value(getter() or [])
            g.changed.connect(lambda: self._set(lambda: setter(g.values())))
        self.layout.addWidget(labelled_group(title, g, hint))
        return g

    def _set(self, fn: Callable[[], None]) -> None:
        fn()
        self.on_change()

    def _build(self) -> None:
        nid = self.node_id
        p = self.project
        if nid == "in_data":
            self._title("Operational data types")
            self._note("Wind-turbine / wind-farm setting. SCADA is one source, not the only one.")
            self._group(
                "Select all that apply",
                ["data_scada", "data_vibration", "data_alarms", "data_metmast", "data_other_ts"],
                lambda: p.inputs.data_types,
                lambda v: setattr(p.inputs, "data_types", v),
                exclusive=False,
            )
        elif nid == "in_records":
            self._title("Evidence records")
            self._note("Optional. These often support ground truth or the reference event.")
            self._group(
                "Available records",
                ["rec_operator", "rec_expert", "rec_logbook", "rec_service",
                 "rec_inspection", "rec_maintenance", "rec_replacement"],
                lambda: p.inputs.records,
                lambda v: setattr(p.inputs, "records", v),
                exclusive=False,
            )
        elif nid == "in_costs":
            self._title("Operational-cost inputs")
            self._note("Needed for Cost / Impact and some Maintenance Planning measures. Do not invent values here.")
            self._group(
                "Cost terms you can supply",
                ["cost_dispatch", "cost_inspection", "cost_downtime", "cost_false_positive", "cost_other"],
                lambda: p.inputs.cost_inputs,
                lambda v: setattr(p.inputs, "cost_inputs", v),
                exclusive=False,
            )
        elif nid == "in_method":
            self._title("Method under evaluation")
            self._group(
                "Method family",
                ["method_nbm", "method_ad", "method_direct_ad", "method_diagnostic", "method_other"],
                lambda: p.inputs.method,
                lambda v: setattr(p.inputs, "method", v),
            )
            self.layout.addWidget(labelled_group(
                "Method notes",
                _text(lambda t: self._set(lambda: setattr(p.inputs, "method_notes", t)),
                      p.inputs.method_notes, "e.g. LSTM NBM residual + CUSUM AD Algorithm", True),
            ))
        elif nid == "s1_objective":
            self._title("Primary evaluation objective")
            self._note("One primary objective is required. Secondary objectives are optional.")
            self._group(
                "Primary objective",
                ["obj_early_warning", "obj_maintenance", "obj_diagnostic", "obj_cost"],
                lambda: p.stage1.primary_objective,
                lambda v: setattr(p.stage1, "primary_objective", v),
            )
            self._group(
                "Secondary objectives (optional)",
                ["obj_early_warning", "obj_maintenance", "obj_diagnostic", "obj_cost"],
                lambda: p.stage1.secondary_objectives,
                lambda v: setattr(p.stage1, "secondary_objectives",
                                  [x for x in v if x != p.stage1.primary_objective]),
                exclusive=False,
            )
        elif nid == "s1_followup":
            self._title("Objective follow-up")
            obj = p.stage1.primary_objective
            if not obj:
                self._note("Choose a primary objective first. You can still fill these fields if you know them.")
            ew = p.stage1.early_warning
            self.layout.addWidget(labelled_group(
                "Reference event",
                _text(lambda t: self._set(lambda: setattr(ew, "reference_event", t)),
                      ew.reference_event, "e.g. generator-bearing replacement; OEM alarm"),
            ))
            self._group(
                "Detection point for lead time",
                ["detect_first_anomaly", "detect_fd_condition"],
                lambda: ew.detection_point,
                lambda v: setattr(ew, "detection_point", v),
                hint="First detected anomaly is not the same as a case-level fault detection.",
            )
            mp = p.stage1.maintenance
            self.layout.addWidget(labelled_group(
                "Useful warning period (Maintenance Planning)",
                _text(lambda t: self._set(lambda: setattr(mp, "useful_lead_time", t)),
                      mp.useful_lead_time, "e.g. 14 days before a planned intervention"),
            ))
            self.layout.addWidget(labelled_group(
                "Acceptable false fault detections",
                _text(lambda t: self._set(lambda: setattr(mp, "acceptable_false_fd", t)),
                      mp.acceptable_false_fd, "e.g. at most one false dispatch per turbine-year"),
            ))
            self.layout.addWidget(labelled_group(
                "Workload unit",
                _text(lambda t: self._set(lambda: setattr(mp, "workload_unit", t)),
                      mp.workload_unit, "e.g. alerts per asset-day; assets per weekly review"),
            ))
            dq = p.stage1.diagnostic
            self.layout.addWidget(labelled_group(
                "Diagnostic level",
                _text(lambda t: self._set(lambda: setattr(dq, "diagnostic_level", t)),
                      dq.diagnostic_level, "e.g. component (generator bearing), not damage mechanism"),
            ))
            self._group(
                "Cost terms in the comparison (Cost / Impact)",
                ["cost_dispatch", "cost_inspection", "cost_downtime", "cost_false_positive", "cost_other"],
                lambda: p.stage1.cost_impact.cost_terms or p.inputs.cost_inputs,
                lambda v: setattr(p.stage1.cost_impact, "cost_terms", v),
                exclusive=False,
            )
            chk = QCheckBox("Sensitivity analysis of cost values is planned")
            chk.setChecked(p.stage1.cost_impact.sensitivity_planned)
            chk.toggled.connect(lambda on: self._set(
                lambda: setattr(p.stage1.cost_impact, "sensitivity_planned", on)))
            self.layout.addWidget(chk)
        elif nid == "s2_ontology":
            self._title("Fault ontology")
            self.layout.addWidget(labelled_group(
                "Fault definition",
                _text(lambda t: self._set(lambda: setattr(p.stage2, "fault_definition", t)),
                      p.stage2.fault_definition,
                      "What confirmed condition or abnormal behaviour is the evaluation about?", True),
            ))
            self.layout.addWidget(labelled_group(
                "Labelled level",
                _text(lambda t: self._set(lambda: setattr(p.stage2, "labelled_level", t)),
                      p.stage2.labelled_level,
                      "e.g. generator-bearing fault; not inner-race spalling unless that is labelled"),
            ))
        elif nid == "s2_tier":
            self._title("Evidence tier and sources")
            self._group(
                "Evidence tier",
                ["tier_a", "tier_b", "tier_c", "tier_combined", "tier_none"],
                lambda: p.stage2.evidence_tier,
                lambda v: setattr(p.stage2, "evidence_tier", v),
            )
            self._group(
                "Evidence sources",
                ["rec_operator", "rec_expert", "rec_logbook", "rec_service",
                 "rec_inspection", "rec_maintenance", "rec_replacement",
                 "data_alarms", "data_scada", "data_vibration"],
                lambda: p.stage2.evidence_sources,
                lambda v: setattr(p.stage2, "evidence_sources", v),
                exclusive=False,
                hint="Care to Compare combines operator feedback, service reports or fault logbooks with expert analysis. The exact rule used to start a pre-fault window is not published.",
            )
            self._group(
                "If Tier C: symptom definition",
                ["symptom_rule", "symptom_cpd", "symptom_multi"],
                lambda: p.stage2.symptom_method,
                lambda v: setattr(p.stage2, "symptom_method", v),
            )
        elif nid == "s2_labels":
            self._title("Label definition and uncertainty")
            self._group(
                "Label representation",
                ["label_binary", "label_soft", "label_interval"],
                lambda: p.stage2.label_representation,
                lambda v: setattr(p.stage2, "label_representation", v),
            )
            u = p.stage2.uncertainty
            self._group(
                "Evidence certainty",
                ["cert_numeric", "cert_categorical", "cert_fuzzy"],
                lambda: u.evidence_certainty,
                lambda v: setattr(u, "evidence_certainty", v),
            )
            self._group(
                "Timing certainty",
                ["time_point", "time_interval", "time_unknown"],
                lambda: u.timing_certainty,
                lambda v: setattr(u, "timing_certainty", v),
            )
            self._group(
                "Source agreement",
                ["agree_single", "agree_consistent", "agree_conflict"],
                lambda: u.source_agreement,
                lambda v: setattr(u, "source_agreement", v),
            )
            self._group(
                "Label stability",
                ["stab_stable", "stab_unstable"],
                lambda: u.label_stability,
                lambda v: setattr(u, "label_stability", v),
            )
            chk = QCheckBox("Circular-evaluation risk: the same monitored behaviour defines labels and is scored")
            chk.setChecked(p.stage2.circular_risk)
            chk.toggled.connect(lambda on: self._set(lambda: setattr(p.stage2, "circular_risk", on)))
            self.layout.addWidget(chk)
            self._note("This is a warning, not a hard stop. Record it so later readers see the limitation.")
        elif nid == "s2_healthy":
            self._title("Healthy-case evidence")
            self._note("The absence of a recorded fault alone does not confirm healthy operation.")
            self.layout.addWidget(labelled_group(
                "How healthy cases are justified",
                _text(lambda t: self._set(lambda: setattr(p.stage2, "healthy_case_evidence", t)),
                      p.stage2.healthy_case_evidence,
                      "e.g. no relevant alarm, maintenance or downtime within ±N days; matched operating region",
                      True),
            ))
        elif nid == "s3_cases":
            self._title("Case construction")
            self._group(
                "How cases enter the evaluation",
                ["case_predefined", "case_constructed"],
                lambda: p.stage3.case_construction,
                lambda v: setattr(p.stage3, "case_construction", v),
            )
            self.layout.addWidget(labelled_group(
                "Case notes",
                _text(lambda t: self._set(lambda: setattr(p.stage3, "case_notes", t)),
                      p.stage3.case_notes, "Boundaries, inventory size, fault groups…", True),
            ))
        elif nid == "s3_windows":
            self._title("Event windows")
            self._note(
                "State whether this is a pre-fault window or a fault window. "
                "Care to Compare labels anomalies that led up to faults: the window ends at the "
                "start of the turbine fault. That is not the faulted operating period itself."
            )
            chk = QCheckBox("Event windows are defined for this evaluation")
            chk.setChecked(p.stage3.event_windows.defined or bool(p.stage3.event_windows.boundaries))
            chk.toggled.connect(lambda on: self._set(
                lambda: setattr(p.stage3.event_windows, "defined", on)))
            self.layout.addWidget(chk)
            self._group(
                "What the interval represents",
                ["window_prefault", "window_fault", "window_other"],
                lambda: p.stage3.event_windows.window_kind,
                lambda v: setattr(p.stage3.event_windows, "window_kind", v),
            )
            ew = p.stage3.event_windows
            self.layout.addWidget(labelled_group(
                "Boundaries",
                _text(lambda t: self._set(lambda: setattr(ew, "boundaries", t)),
                      ew.boundaries, "e.g. 6 weeks ending at the reference event"),
            ))
            self.layout.addWidget(labelled_group(
                "Reference event for the window",
                _text(lambda t: self._set(lambda: setattr(ew, "reference_event", t)),
                      ew.reference_event or p.stage1.early_warning.reference_event,
                      "Often the same as the Stage 1 reference event"),
            ))
            self.layout.addWidget(labelled_group(
                "Timing rules",
                _text(lambda t: self._set(lambda: setattr(ew, "timing_rules", t)),
                      ew.timing_rules,
                      "e.g. common duration because physical onset is unknown", True),
            ))
        elif nid == "s3_compare":
            self._title("Faulty–healthy comparison")
            self._group(
                "Comparison rule",
                ["cmp_pairs", "cmp_matching", "cmp_group"],
                lambda: p.stage3.comparison,
                lambda v: setattr(p.stage3, "comparison", v),
            )
        elif nid == "s3_periods":
            self._title("Data periods and valid evaluation data")
            dp = p.stage3.data_periods
            self.layout.addWidget(labelled_group(
                "Training period",
                _text(lambda t: self._set(lambda: setattr(dp, "training", t)), dp.training,
                      "Used for NBM / method development"),
            ))
            self.layout.addWidget(labelled_group(
                "Validation period",
                _text(lambda t: self._set(lambda: setattr(dp, "validation", t)), dp.validation),
            ))
            self.layout.addWidget(labelled_group(
                "Test / held-out evaluation period",
                _text(lambda t: self._set(lambda: setattr(dp, "test", t)), dp.test,
                      "Must remain separate from development decisions"),
            ))
            self.layout.addWidget(labelled_group(
                "Valid evaluation data rules",
                _text(lambda t: self._set(lambda: setattr(p.stage3, "valid_data_rules", t)),
                      p.stage3.valid_data_rules,
                      "Missing data, shutdown, maintenance, out-of-scope operation", True),
            ))
        elif nid == "s3_tuning":
            self._title("Tuning and held-out evaluation")
            self._group(
                "Tuning mode",
                ["tune_oracle", "tune_heldout"],
                lambda: p.stage3.tuning_mode,
                lambda v: setattr(p.stage3, "tuning_mode", v),
            )
            self._group(
                "Held-out tuning inventory",
                ["inv_fault_type", "inv_farm", "inv_all"],
                lambda: p.stage3.tuning_inventory,
                lambda v: setattr(p.stage3, "tuning_inventory", v),
                hint="Required when held-out tuning is selected.",
            )
            self.layout.addWidget(labelled_group(
                "Tuning notes",
                _text(lambda t: self._set(lambda: setattr(p.stage3, "tuning_notes", t)),
                      p.stage3.tuning_notes, "", True),
            ))
        elif nid == "s3_fd":
            self._title("Fault-detection condition")
            self._note("A single detected anomaly is not automatically a detected fault.")
            self._group(
                "Condition type",
                ["fd_count", "fd_persistence", "fd_density", "fd_pattern"],
                lambda: p.stage3.fd_condition,
                lambda v: setattr(p.stage3, "fd_condition", v),
            )
            self.layout.addWidget(labelled_group(
                "Threshold / rule",
                _text(lambda t: self._set(lambda: setattr(p.stage3, "fd_condition_notes", t)),
                      p.stage3.fd_condition_notes,
                      "e.g. persistence κ = 6 consecutive 10-min alarms", True),
            ))
        elif nid == "s4_output":
            self._title("Method output type")
            self._group(
                "Class scheme",
                ["out_binary", "out_multiclass", "out_multilabel"],
                lambda: p.stage4.output_class,
                lambda v: setattr(p.stage4, "output_class", v),
            )
            self._group(
                "Output type",
                ["out_hard", "out_score", "out_ranked"],
                lambda: p.stage4.output_score,
                lambda v: setattr(p.stage4, "output_score", v),
            )
            self._group(
                "Include stability / nuisance measures?",
                ["yes_stability", "no_stability"],
                lambda: p.stage4.include_stability,
                lambda v: setattr(p.stage4, "include_stability", v),
            )
        elif nid == "s4_dimensions":
            self._title("Required performance dimensions")
            dims = required_dimensions(p)
            if not p.stage1.primary_objective:
                self._note("Choose a primary objective in Stage 1 to see which dimensions are required.")
            else:
                names = {
                    "instance": "Instance-level AD performance",
                    "case": "Case-level fault-detection performance",
                    "earliness": "Detection earliness",
                    "combined": "Combined detection performance",
                    "operational": "Operational measures",
                }
                self._note("These follow from the evaluation objective. Click i on a metric later for definitions.")
                for d in dims:
                    lab = QLabel(f"• {names.get(d, d)}")
                    lab.setWordWrap(True)
                    self.layout.addWidget(lab)
                for key, text in GLOSSARY.items():
                    if any(k in key.lower() for k in ("instance", "case", "earliness", "CARE")):
                        pass
        elif nid == "s4_metrics":
            self._build_metrics()
        else:
            self._note("Select a node.")

    def _build_metrics(self) -> None:
        p = self.project
        self._title("Selected metric set")
        self._note(
            "Recommendations follow Stages 1–3 and the output type. "
            "Accept or reject each metric. Validity is about whether the protocol supports the metric — "
            "it does not block finishing the protocol."
        )
        recs = recommend(p)
        if not recs:
            self._note("No recommendations yet. Set a primary objective and the method output type.")
            return
        accepted = set(p.stage4.accepted_metrics)
        rejected = set(p.stage4.rejected_metrics)
        for rec in recs:
            self.layout.addWidget(self._metric_card(rec, accepted, rejected))
        self.layout.addWidget(labelled_group(
            "Override notes",
            _text(lambda t: self._set(lambda: setattr(p.stage4, "override_notes", t)),
                  p.stage4.override_notes,
                  "If you reject a core metric, say why.", True),
        ))

    def _metric_card(self, rec, accepted: set[str], rejected: set[str]) -> QWidget:
        from fdd_eval.ui.icons import paint_icon
        from PySide6.QtWidgets import QHBoxLayout, QPushButton, QFrame

        metric = rec.metric
        card = QFrame()
        card.setObjectName("Card")
        box = QVBoxLayout(card)
        top = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(paint_icon(metric.unit, 24).pixmap(24, 24))
        title = QLabel(f"{metric.name}")
        title.setObjectName("SectionTitle")
        title.setWordWrap(True)
        info = QPushButton("i")
        info.setObjectName("InfoBtn")
        choice_like = CHOICES.get(f"unit_{metric.unit}")
        def show_info():
            html = (
                f"<p>{metric.summary}</p>"
                f"<p><b>Limitation.</b> {metric.limitation}</p>"
                f"<p><b>Why suggested.</b> {rec.reason}</p>"
            )
            if rec.missing:
                html += "<p><b>Missing for this metric to be valid.</b><ul>" + "".join(
                    f"<li>{m}</li>" for m in rec.missing) + "</ul></p>"
            if metric.citations:
                html += "<p><b>References.</b><br/>" + "<br/>".join(metric.citations) + "</p>"
            if choice_like:
                html += "<hr/>" + choice_html(choice_like)
            InfoDialog(metric.name, html, self).exec()
        info.clicked.connect(show_info)
        top.addWidget(icon)
        top.addWidget(title, 1)
        top.addWidget(info)
        box.addLayout(top)
        why = QLabel(rec.reason)
        why.setObjectName("Hint")
        why.setWordWrap(True)
        box.addWidget(why)
        if rec.valid:
            val = QLabel("Valid on the current protocol.")
        else:
            val = QLabel("Not yet valid: " + "; ".join(rec.missing))
        val.setObjectName("Hint")
        val.setWordWrap(True)
        box.addWidget(val)
        btns = QHBoxLayout()
        acc = QPushButton("Accept")
        acc.setObjectName("Primary" if metric.id in accepted else "")
        rej = QPushButton("Reject")
        if metric.id in accepted:
            acc.setText("Accepted")
        if metric.id in rejected:
            rej.setText("Rejected")

        def accept():
            if metric.id in p.stage4.rejected_metrics:
                p.stage4.rejected_metrics.remove(metric.id)
            if metric.id not in p.stage4.accepted_metrics:
                p.stage4.accepted_metrics.append(metric.id)
            self.on_change()

        def reject():
            if metric.id in p.stage4.accepted_metrics:
                p.stage4.accepted_metrics.remove(metric.id)
            if metric.id not in p.stage4.rejected_metrics:
                p.stage4.rejected_metrics.append(metric.id)
            self.on_change()

        acc.clicked.connect(accept)
        rej.clicked.connect(reject)
        btns.addWidget(acc)
        btns.addWidget(rej)
        btns.addStretch(1)
        box.addLayout(btns)
        return card
