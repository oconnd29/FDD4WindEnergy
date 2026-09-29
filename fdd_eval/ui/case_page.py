"""Case-data tab: load precomputed CSVs, plot, compute CARE and optional cost."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from fdd_eval.domain.care import care_pair
from fdd_eval.domain.case_io import load_case_csv, resolve_csv_path
from fdd_eval.domain.cost import cost_pair
from fdd_eval.domain.project import CostModel, Project
from fdd_eval.paths import resource_root
from fdd_eval.ui.plots import CostOptionsPlot, SeriesPlot

REPO_ROOT = resource_root()


def _money(value: float) -> str:
    sign = "−" if value < 0 else ""
    return f"{sign}€{abs(value):,.0f}"


class CaseDataPage(QWidget):
    def __init__(self, project: Project, project_path: Path | None, on_change, parent=None) -> None:
        super().__init__(parent)
        self.project = project
        self.project_path = project_path
        self.on_change = on_change
        self.faulty = None
        self.healthy = None
        self._syncing_cost = False

        outer = QVBoxLayout(self)
        hint = QLabel(
            "Load precomputed case CSVs for a faulty–healthy pair. "
            "The software plots the series and computes metrics only — it does not run an AD Algorithm. "
            "Gold bands mark a pre-fault window (abnormal behaviour leading up to a fault), "
            "not the faulted operating period itself."
        )
        hint.setObjectName("Hint")
        hint.setWordWrap(True)
        outer.addWidget(hint)

        files = QGridLayout()
        self.faulty_edit = QLineEdit(project.case_data.faulty_csv)
        self.healthy_edit = QLineEdit(project.case_data.healthy_csv)
        bf = QPushButton("Browse…")
        bh = QPushButton("Browse…")
        bt = QPushButton("Load tutorial pair")
        bf.clicked.connect(lambda: self._browse("faulty"))
        bh.clicked.connect(lambda: self._browse("healthy"))
        bt.clicked.connect(self._load_tutorial)
        files.addWidget(QLabel("Faulty case CSV"), 0, 0)
        files.addWidget(self.faulty_edit, 0, 1)
        files.addWidget(bf, 0, 2)
        files.addWidget(QLabel("Healthy case CSV"), 1, 0)
        files.addWidget(self.healthy_edit, 1, 1)
        files.addWidget(bh, 1, 2)
        files.addWidget(bt, 1, 3)
        outer.addLayout(files)

        kappa_row = QHBoxLayout()
        kappa_row.addWidget(QLabel("Persistence threshold κ"))
        self.kappa = QSpinBox()
        self.kappa.setRange(1, 500)
        self.kappa.setValue(int(project.case_data.kappa or 72))
        self.kappa.setToolTip("C2C uses κ = 72 (12 hours at 10 min). The short synthetic pair uses 12.")
        self.kappa.valueChanged.connect(self._kappa_changed)
        kappa_row.addWidget(self.kappa)
        load = QPushButton("Load and plot")
        load.setObjectName("Primary")
        load.clicked.connect(self.reload)
        kappa_row.addWidget(load)
        kappa_row.addStretch(1)
        outer.addLayout(kappa_row)

        self.cost_box = self._make_cost_panel()
        outer.addWidget(self.cost_box)

        split = QSplitter(Qt.Orientation.Vertical)
        outer.addWidget(split, 1)

        plots = QWidget()
        grid = QGridLayout(plots)
        grid.setContentsMargins(0, 0, 0, 0)
        self.p_raw_tv = SeriesPlot("Faulty — raw Monitoring Indicator (train + val)")
        self.p_raw_te = SeriesPlot("Faulty — raw Monitoring Indicator (test)")
        self.p_sc_tv = SeriesPlot("Faulty — CUSUM score (train + val)")
        self.p_sc_te = SeriesPlot("Faulty — CUSUM score (test)")
        self.h_raw_tv = SeriesPlot("Healthy — raw Monitoring Indicator (train + val)")
        self.h_raw_te = SeriesPlot("Healthy — raw Monitoring Indicator (test)")
        self.h_sc_tv = SeriesPlot("Healthy — CUSUM score (train + val)")
        self.h_sc_te = SeriesPlot("Healthy — CUSUM score (test)")
        self.p_power = SeriesPlot("Faulty — expected vs actual power (test)")
        self.p_cost = CostOptionsPlot()
        grid.addWidget(self.p_raw_tv, 0, 0)
        grid.addWidget(self.p_raw_te, 0, 1)
        grid.addWidget(self.p_sc_tv, 1, 0)
        grid.addWidget(self.p_sc_te, 1, 1)
        grid.addWidget(self.h_raw_tv, 2, 0)
        grid.addWidget(self.h_raw_te, 2, 1)
        grid.addWidget(self.h_sc_tv, 3, 0)
        grid.addWidget(self.h_sc_te, 3, 1)
        grid.addWidget(self.p_power, 4, 0, 1, 2)
        grid.addWidget(self.p_cost, 5, 0, 1, 2)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(plots)
        split.addWidget(scroll)

        self.metrics = QTextBrowser()
        self.metrics.setMaximumHeight(180)
        split.addWidget(self.metrics)
        split.setStretchFactor(0, 4)
        split.setStretchFactor(1, 1)

        legend = QLabel(
            "Test plots: gold band = pre-fault window (ends at the simulated fault). "
            "Score plots: light red dashed threshold on train/val, darker red dashed threshold on test. "
            "Power plot (when present): dashed teal = expected curve, solid navy = actual. "
            "Cost plot: rising line = lost production as the blade gets worse; teal line = crew sent; "
            "bars = send a crew when flagged versus wait until the blade fails (gold = lost production, "
            "teal = repair, coral = turbine off)."
        )
        legend.setObjectName("Hint")
        legend.setWordWrap(True)
        outer.addWidget(legend)

        self.sync_cost_visibility()
        if project.case_data.faulty_csv or project.case_data.healthy_csv:
            self.reload()

    def _make_cost_panel(self) -> QFrame:
        box = QFrame()
        box.setObjectName("Card")
        layout = QVBoxLayout(box)
        title = QLabel("Cost / impact")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)
        note = QLabel(
            "These euro values are assumptions for the tutorial — change them. "
            "The software does not re-run CUSUM; it only applies these costs to the loaded series."
        )
        note.setObjectName("Hint")
        note.setWordWrap(True)
        layout.addWidget(note)

        grid = QGridLayout()
        self.sp_price = QDoubleSpinBox()
        self.sp_price.setRange(1.0, 500.0)
        self.sp_price.setDecimals(1)
        self.sp_price.setSuffix(" €/MWh")
        self.sp_inspect = QDoubleSpinBox()
        self.sp_inspect.setRange(0.0, 1_000_000.0)
        self.sp_inspect.setDecimals(0)
        self.sp_inspect.setPrefix("€")
        self.sp_planned = QDoubleSpinBox()
        self.sp_planned.setRange(0.0, 1_000_000.0)
        self.sp_planned.setDecimals(0)
        self.sp_planned.setPrefix("€")
        self.sp_planned_h = QDoubleSpinBox()
        self.sp_planned_h.setRange(0.0, 1000.0)
        self.sp_planned_h.setDecimals(0)
        self.sp_planned_h.setSuffix(" h")
        self.sp_emerg = QDoubleSpinBox()
        self.sp_emerg.setRange(0.0, 1_000_000.0)
        self.sp_emerg.setDecimals(0)
        self.sp_emerg.setPrefix("€")
        self.sp_emerg_h = QDoubleSpinBox()
        self.sp_emerg_h.setRange(0.0, 2000.0)
        self.sp_emerg_h.setDecimals(0)
        self.sp_emerg_h.setSuffix(" h")
        labels = [
            (0, "Selling price", self.sp_price),
            (1, "Crew visit if a healthy turbine is flagged", self.sp_inspect),
            (2, "Repair if you catch it early", self.sp_planned),
            (3, "Stop time if you catch it early", self.sp_planned_h),
            (4, "Repair if you wait until the blade fails", self.sp_emerg),
            (5, "Stop time if you wait until the blade fails", self.sp_emerg_h),
        ]
        for col, text, widget in labels:
            grid.addWidget(QLabel(text), 0, col)
            grid.addWidget(widget, 1, col)
            widget.valueChanged.connect(self._cost_tariff_changed)
        layout.addLayout(grid)

        self.cost_results = QTextBrowser()
        self.cost_results.setMaximumHeight(200)
        layout.addWidget(self.cost_results)
        return box

    def _cost_model(self) -> CostModel:
        return self.project.stage1.cost_impact.model

    def _fill_cost_spins(self) -> None:
        m = self._cost_model()
        self._syncing_cost = True
        self.sp_price.setValue(m.price_eur_per_mwh)
        self.sp_inspect.setValue(m.inspection_eur)
        self.sp_planned.setValue(m.planned_repair_eur)
        self.sp_planned_h.setValue(m.planned_downtime_h)
        self.sp_emerg.setValue(m.emergency_repair_eur)
        self.sp_emerg_h.setValue(m.emergency_downtime_h)
        self._syncing_cost = False

    def _cost_tariff_changed(self) -> None:
        if self._syncing_cost:
            return
        m = self._cost_model()
        m.price_eur_per_mwh = float(self.sp_price.value())
        m.inspection_eur = float(self.sp_inspect.value())
        m.planned_repair_eur = float(self.sp_planned.value())
        m.planned_downtime_h = float(self.sp_planned_h.value())
        m.emergency_repair_eur = float(self.sp_emerg.value())
        m.emergency_downtime_h = float(self.sp_emerg_h.value())
        self.on_change()
        self._update_metrics()

    def sync_cost_visibility(self) -> None:
        show = self.project.has_objective("obj_cost")
        self.cost_box.setVisible(show)
        has_power = bool(self.faulty and self.faulty.has_power())
        self.p_power.setVisible(show and has_power)
        self.p_cost.setVisible(show)
        if show:
            self._fill_cost_spins()

    def bind(self, project: Project, project_path: Path | None) -> None:
        self.project = project
        self.project_path = project_path
        self.faulty_edit.setText(project.case_data.faulty_csv)
        self.healthy_edit.setText(project.case_data.healthy_csv)
        self.kappa.setValue(int(project.case_data.kappa or 72))
        self.sync_cost_visibility()
        if project.case_data.faulty_csv:
            self.reload()
        else:
            self._update_metrics()

    def _browse(self, which: str) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open case CSV", "", "CSV (*.csv)")
        if not path:
            return
        if which == "faulty":
            self.faulty_edit.setText(path)
            self.project.case_data.faulty_csv = path
        else:
            self.healthy_edit.setText(path)
            self.project.case_data.healthy_csv = path
        self.on_change()
        self.reload()

    def _load_tutorial(self) -> None:
        if self.project.has_objective("obj_cost"):
            folder = REPO_ROOT / "tutorials" / "cost_blade_pair"
            rel_f = "tutorials/cost_blade_pair/faulty.csv"
            rel_h = "tutorials/cost_blade_pair/healthy.csv"
            kappa = 72
        else:
            folder = REPO_ROOT / "tutorials" / "synthetic_pair"
            rel_f = "tutorials/synthetic_pair/faulty.csv"
            rel_h = "tutorials/synthetic_pair/healthy.csv"
            kappa = 12
        f = folder / "faulty.csv"
        h = folder / "healthy.csv"
        if not f.is_file() or not h.is_file():
            QMessageBox.warning(self, "Case data", f"Tutorial CSVs not found in:\n{folder}")
            return
        self.faulty_edit.setText(rel_f)
        self.healthy_edit.setText(rel_h)
        self.project.case_data.faulty_csv = rel_f
        self.project.case_data.healthy_csv = rel_h
        self.kappa.setValue(kappa)
        self.project.case_data.kappa = kappa
        self.on_change()
        self.reload()

    def _kappa_changed(self, value: int) -> None:
        self.project.case_data.kappa = int(value)
        self.on_change()
        if self.faulty and self.healthy:
            self._update_metrics()

    def reload(self) -> None:
        f_path = resolve_csv_path(self.faulty_edit.text().strip(), self.project_path, REPO_ROOT)
        h_path = resolve_csv_path(self.healthy_edit.text().strip(), self.project_path, REPO_ROOT)
        try:
            self.faulty = load_case_csv(f_path, "faulty") if f_path and f_path.is_file() else None
            self.healthy = load_case_csv(h_path, "healthy") if h_path and h_path.is_file() else None
        except Exception as exc:
            QMessageBox.warning(self, "Case data", str(exc))
            return
        self.project.case_data.faulty_csv = self.faulty_edit.text().strip()
        self.project.case_data.healthy_csv = self.healthy_edit.text().strip()
        self.p_raw_tv.set_data(self.faulty, "train_val", "raw")
        self.p_raw_te.set_data(self.faulty, "test", "raw")
        self.p_sc_tv.set_data(self.faulty, "train_val", "score")
        self.p_sc_te.set_data(self.faulty, "test", "score")
        self.h_raw_tv.set_data(self.healthy, "train_val", "raw")
        self.h_raw_te.set_data(self.healthy, "test", "raw")
        self.h_sc_tv.set_data(self.healthy, "train_val", "score")
        self.h_sc_te.set_data(self.healthy, "test", "score")
        self.p_power.set_data(self.faulty, "test", "power_pair")
        self.sync_cost_visibility()
        self._update_metrics()

    def _update_metrics(self) -> None:
        if not (self.faulty and self.healthy):
            self.metrics.setHtml("<p>Load both CSVs of the pair to compute CARE.</p>")
            self.cost_results.setHtml("<p>Load both CSVs to score cost.</p>")
            self.p_cost.set_result(None, None, None)
            return
        result = care_pair(self.faulty, self.healthy, int(self.kappa.value()))
        self.metrics.setHtml(
            "<p><b>CARE on this pair</b> (computed from the CSV alarms and labels; "
            "CUSUM is not re-run).</p>"
            f"<ul>"
            f"<li>Coverage C = {result.coverage:.3f}</li>"
            f"<li>Accuracy A = {result.accuracy:.3f}</li>"
            f"<li>Reliability R = {result.reliability:.3f} "
            f"(κ = {result.kappa}; faulty detected = {result.faulty_detected}; "
            f"healthy detected = {result.healthy_detected})</li>"
            f"<li>Earliness E = {result.earliness:.3f}</li>"
            f"<li>Unified CARE = <b>{result.unified:.3f}</b></li>"
            f"</ul>"
            f"<p>{result.notes}</p>"
        )
        if not self.project.has_objective("obj_cost"):
            self.p_cost.set_result(None, None, None)
            return
        cost = cost_pair(self.faulty, self.healthy, self._cost_model(), int(self.kappa.value()))
        self.p_cost.set_result(cost, self.faulty, self._cost_model())
        sens = cost.sensitivity
        if cost.net_benefit >= 0:
            diff = f"Sending a crew early is <b>{_money(cost.net_benefit)}</b> cheaper"
        else:
            diff = f"Sending a crew early is <b>{_money(-cost.net_benefit)}</b> more expensive"
        self.cost_results.setHtml(
            f"<p><b>Cost of two responses</b></p>"
            f"<ul>"
            f"<li>Send a crew when the method flags the turbine: "
            f"<b>{_money(cost.c_detect)}</b> "
            f"(damaged turbine {_money(cost.faulty.total_eur)}; "
            f"healthy turbine {_money(cost.healthy.total_eur)})</li>"
            f"<li>Wait until the blade fails, then repair: "
            f"<b>{_money(cost.c_wait)}</b></li>"
            f"<li>{diff}</li>"
            f"<li>Lost production before the crew arrives: "
            f"{cost.faulty.lost_mwh:.2f} MWh ({_money(cost.faulty.lost_revenue_eur)})</li>"
            f"</ul>"
            f"<p>If the selling price is halved, sending a crew early is "
            f"{_money(sens.get('price_0.5x', 0))} cheaper; if it is 50% higher, "
            f"{_money(sens.get('price_1.5x', 0))} cheaper. "
            f"If crew and repair costs are halved, {_money(sens.get('crew_0.5x', 0))} cheaper; "
            f"if they are 50% higher, {_money(sens.get('crew_1.5x', 0))} cheaper.</p>"
            f"<p>{cost.notes}</p>"
        )
