"""Main window: stage rail, node cards, inspector, completeness, save/load."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QCloseEvent, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from fdd_eval import APP_NAME, FILE_FILTER, FILE_SUFFIX, __version__
from fdd_eval.domain.completeness import summarise
from fdd_eval.domain.glossary import GLOSSARY
from fdd_eval.domain.nodes import NODES, STAGES, nodes_for
from fdd_eval.domain.project import Project
from fdd_eval.domain.reproducibility import TIPS, mark, tip_state
from fdd_eval.io.markdown_export import export_markdown
from fdd_eval.io.project_io import load_project, save_project
from fdd_eval.paths import app_icon_path, resource_root
from fdd_eval.ui.case_page import CaseDataPage
from fdd_eval.ui.inspectors import Inspector
from fdd_eval.ui.widgets import InfoDialog, NodeCard


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        icon = app_icon_path()
        if icon.exists():
            self.setWindowIcon(QIcon(str(icon)))
        self.resize(1280, 820)
        self.project = Project()
        self.path: Path | None = None
        self.dirty = False
        self.stage_id = "inputs"
        self.node_id = "in_data"
        self._cards: dict[str, NodeCard] = {}
        self._building = False

        self._make_menu()
        self._make_body()
        self.refresh()

    def _make_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        acts = [
            ("&New", QKeySequence.StandardKey.New, self.new_project),
            ("&Open…", QKeySequence.StandardKey.Open, self.open_project),
            ("Open &Tutorial: Chapter 5 (C2C / CARE)…", None, self.open_tutorial_ch5),
            ("Open Tutorial: &Synthetic CUSUM pair…", None, self.open_tutorial_synthetic),
            ("Open Tutorial: &Blade cost pair…", None, self.open_tutorial_cost),
            ("&Save", QKeySequence.StandardKey.Save, self.save_project),
            ("Save &As…", QKeySequence.StandardKey.SaveAs, self.save_project_as),
            None,
            ("Export protocol (&Markdown)…", None, self.export_markdown),
            None,
            ("E&xit", QKeySequence.StandardKey.Quit, self.close),
        ]
        for item in acts:
            if item is None:
                file_menu.addSeparator()
                continue
            name, shortcut, slot = item
            act = QAction(name, self)
            if shortcut:
                act.setShortcut(shortcut)
            act.triggered.connect(slot)
            file_menu.addAction(act)

        help_menu = self.menuBar().addMenu("&Help")
        g = QAction("Glossary", self)
        g.triggered.connect(self.show_glossary)
        help_menu.addAction(g)
        r = QAction("Reproducibility guidelines", self)
        r.triggered.connect(self.show_repro_help)
        help_menu.addAction(r)
        a = QAction("About", self)
        a.triggered.connect(self.show_about)
        help_menu.addAction(a)

    def _make_body(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(12, 10, 12, 10)
        outer.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel(APP_NAME)
        title.setObjectName("AppTitle")
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Project title")
        self.title_edit.textChanged.connect(self._title_changed)
        header.addWidget(title)
        header.addWidget(self.title_edit, 1)
        outer.addLayout(header)

        prog_row = QHBoxLayout()
        self.prog = QProgressBar()
        self.prog.setRange(0, 100)
        self.prog_label = QLabel()
        prog_row.addWidget(self.prog, 1)
        prog_row.addWidget(self.prog_label)
        outer.addLayout(prog_row)

        tabs = QTabWidget()
        protocol = QWidget()
        proto_l = QVBoxLayout(protocol)
        proto_l.setContentsMargins(0, 0, 0, 0)

        split = QSplitter(Qt.Orientation.Horizontal)
        proto_l.addWidget(split, 1)

        self.stage_list = QListWidget()
        self.stage_list.setFixedWidth(210)
        for sid, short, long in STAGES:
            item = QListWidgetItem(f"{short}\n{long}")
            item.setData(Qt.ItemDataRole.UserRole, sid)
            self.stage_list.addItem(item)
        self.stage_list.currentRowChanged.connect(self._stage_changed)
        split.addWidget(self.stage_list)

        mid = QWidget()
        mid_l = QVBoxLayout(mid)
        mid_l.setContentsMargins(8, 0, 8, 0)
        self.stage_hint = QLabel()
        self.stage_hint.setObjectName("Hint")
        self.stage_hint.setWordWrap(True)
        mid_l.addWidget(self.stage_hint)
        self.cards_host = QWidget()
        self.cards_grid = QGridLayout(self.cards_host)
        self.cards_grid.setSpacing(8)
        mid_l.addWidget(self.cards_host, 1)
        split.addWidget(mid)

        right = QWidget()
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(0, 0, 0, 0)
        insp_title = QLabel("Inspector")
        insp_title.setObjectName("SectionTitle")
        right_l.addWidget(insp_title)
        self.inspector_scroll = QScrollArea()
        self.inspector_scroll.setWidgetResizable(True)
        self.inspector_host = QWidget()
        self.inspector_layout = QVBoxLayout(self.inspector_host)
        self.inspector_layout.setContentsMargins(0, 0, 0, 0)
        self.inspector_scroll.setWidget(self.inspector_host)
        right_l.addWidget(self.inspector_scroll, 1)
        split.addWidget(right)
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 3)
        split.setStretchFactor(2, 3)

        bottom = QFrame()
        bottom.setObjectName("Card")
        bot = QHBoxLayout(bottom)
        self.missing_box = QTextBrowser()
        self.missing_box.setMaximumHeight(110)
        self.repro_box = QTextBrowser()
        self.repro_box.setMaximumHeight(110)
        self.repro_box.anchorClicked.connect(self._repro_clicked)
        self.repro_box.setOpenLinks(False)
        bot.addWidget(self._captioned("Next required items", self.missing_box), 1)
        bot.addWidget(self._captioned("Reproducibility (recommended)", self.repro_box), 1)
        proto_l.addWidget(bottom)

        tabs.addTab(protocol, "Evaluation protocol")
        self.case_page = CaseDataPage(self.project, self.path, self._on_project_changed)
        tabs.addTab(self.case_page, "Case data")
        outer.addWidget(tabs, 1)
        self.tabs = tabs

        self.stage_list.setCurrentRow(0)

    def _captioned(self, title: str, widget: QWidget) -> QWidget:
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(8, 8, 8, 8)
        lab = QLabel(title)
        lab.setObjectName("SectionTitle")
        layout.addWidget(lab)
        layout.addWidget(widget)
        return box

    def _title_changed(self, text: str) -> None:
        if self._building:
            return
        self.project.title = text
        self._mark_dirty()

    def _stage_changed(self, row: int) -> None:
        if row < 0:
            return
        self.stage_id = STAGES[row][0]
        stage_nodes = nodes_for(self.stage_id)
        if stage_nodes:
            self.node_id = stage_nodes[0].id
        self._rebuild_cards()
        self._rebuild_inspector()

    def _select_node(self, node_id: str) -> None:
        self.node_id = node_id
        for nid, card in self._cards.items():
            card.set_selected(nid == node_id)
        self._rebuild_inspector()

    def _rebuild_cards(self) -> None:
        while self.cards_grid.count():
            item = self.cards_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()
        spec = next(s for s in STAGES if s[0] == self.stage_id)
        self.stage_hint.setText(f"{spec[1]} — {spec[2]}. Click a card to edit. Jump around as information is available.")
        nodes = nodes_for(self.stage_id)
        status = summarise(self.project).nodes
        for i, node in enumerate(nodes):
            card = NodeCard(node)
            st = status[node.id]
            card.set_status(st.state, st.missing)
            card.set_selected(node.id == self.node_id)
            card.clicked.connect(self._select_node)
            self.cards_grid.addWidget(card, i // 2, i % 2)
            self._cards[node.id] = card

    def _rebuild_inspector(self) -> None:
        while self.inspector_layout.count():
            item = self.inspector_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        inspector = Inspector(self.project, self.node_id, self._on_project_changed)
        self.inspector_layout.addWidget(inspector)

    def _on_project_changed(self) -> None:
        self._mark_dirty()
        self.refresh(rebuild_inspector=False)
        # Rebuild inspector only for metric cards that self-refresh via parent
        if self.node_id == "s4_metrics":
            self._rebuild_inspector()

    def _mark_dirty(self) -> None:
        self.dirty = True
        self._sync_title()

    def _sync_title(self) -> None:
        name = self.path.name if self.path else "unsaved"
        mark = "*" if self.dirty else ""
        self.setWindowTitle(f"{APP_NAME} — {self.project.title} [{name}]{mark}")

    def refresh(self, rebuild_inspector: bool = True) -> None:
        self._building = True
        if self.title_edit.text() != self.project.title:
            self.title_edit.setText(self.project.title)
        self._building = False
        c = summarise(self.project)
        pct = int(100 * c.required_done / max(c.required_total, 1))
        self.prog.setValue(pct)
        self.prog_label.setText(f"{c.required_done} / {c.required_total} required")
        if c.missing_required:
            items = "".join(f"<li>{msg}</li>" for _nid, msg in c.missing_required[:8])
            more = f"<p>…and {len(c.missing_required) - 8} more</p>" if len(c.missing_required) > 8 else ""
            self.missing_box.setHtml(f"<ul>{items}</ul>{more}")
        else:
            self.missing_box.setHtml("<p>Required protocol nodes are complete. You can export the protocol.</p>")
        repro = ["<p>Recommended practice from Chapter 3. Gaps are recorded on export.</p><ul>"]
        for tip in TIPS:
            state = tip_state(self.project, tip.id)
            if state == "open":
                repro.append(
                    f"<li>{tip.title} — "
                    f"<a href='follow:{tip.id}'>mark followed</a> · "
                    f"<a href='skip:{tip.id}'>defer</a> · "
                    f"<a href='info:{tip.id}'>i</a></li>"
                )
            else:
                repro.append(f"<li>{tip.title}: <i>{state}</i></li>")
        repro.append("</ul>")
        self.repro_box.setHtml("".join(repro))
        self._rebuild_cards()
        if rebuild_inspector:
            self._rebuild_inspector()
        self._sync_title()
        # Stage list counts
        for i, (sid, short, long) in enumerate(STAGES):
            done, total = c.stage_complete[sid]
            self.stage_list.item(i).setText(f"{short}  {done}/{total}\n{long}")
        self.case_page.sync_cost_visibility()

    def _repro_clicked(self, url) -> None:
        kind, _, tip_id = url.toString().partition(":")
        if kind == "follow":
            mark(self.project, tip_id, True)
            self._on_project_changed()
        elif kind == "skip":
            mark(self.project, tip_id, False)
            self._on_project_changed()
        elif kind == "info":
            tip = next(t for t in TIPS if t.id == tip_id)
            html = (
                f"<p><b>Ideal.</b> {tip.ideal}</p>"
                f"<p><b>Why.</b> {tip.why}</p>"
            )
            if tip.when:
                html += f"<p><b>When.</b> {tip.when}</p>"
            html += "<p>This is recommended practice for a comparable evaluation.</p>"
            InfoDialog(tip.title, html, self).exec()

    def _confirm_discard(self) -> bool:
        if not self.dirty:
            return True
        r = QMessageBox.question(
            self, APP_NAME,
            "Save the current project first?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
        )
        if r == QMessageBox.StandardButton.Save:
            return self.save_project()
        return r == QMessageBox.StandardButton.Discard

    def new_project(self) -> None:
        if not self._confirm_discard():
            return
        self.project = Project()
        self.path = None
        self.dirty = False
        self.stage_id = "inputs"
        self.node_id = "in_data"
        self.stage_list.setCurrentRow(0)
        self.refresh()
        self.case_page.bind(self.project, self.path)

    def open_project(self) -> None:
        if not self._confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(self, "Open project", "", FILE_FILTER)
        if not path:
            return
        self.project = load_project(path)
        self.path = Path(path)
        self.dirty = False
        self.refresh()
        self.case_page.bind(self.project, self.path)

    def open_tutorial_ch5(self) -> None:
        if not self._confirm_discard():
            return
        path = resource_root() / "tutorials" / "chapter5_c2c_care.fddx"
        if not path.exists():
            QMessageBox.warning(
                self, APP_NAME,
                f"Tutorial file not found:\n{path}",
            )
            return
        self.project = load_project(path)
        self.path = path
        self.dirty = False
        self.refresh()
        self.case_page.bind(self.project, self.path)
        self.tabs.setCurrentIndex(0)
        QMessageBox.information(
            self, APP_NAME,
            "Opened the Chapter 5 Care to Compare tutorial.\n\n"
            "Click through Inputs and Stages 1–4. The event interval is a pre-fault window "
            "(it ends at the start of the turbine fault). Stage 4 shows CARE as the combined "
            "detection-performance metric.",
        )

    def open_tutorial_synthetic(self) -> None:
        if not self._confirm_discard():
            return
        path = resource_root() / "tutorials" / "synthetic_pair" / "synthetic_cusum_pair.fddx"
        if not path.exists():
            QMessageBox.warning(self, APP_NAME, f"Tutorial file not found:\n{path}")
            return
        self.project = load_project(path)
        self.path = path
        self.dirty = False
        self.refresh()
        self.case_page.bind(self.project, self.path)
        self.tabs.setCurrentIndex(1)
        QMessageBox.information(
            self, APP_NAME,
            "Opened the synthetic CUSUM pair.\n\n"
            "The Case data tab plots the precomputed Monitoring Indicator and CUSUM score. "
            "CARE is computed from the CSV alarms; CUSUM is not re-run in the app.",
        )

    def open_tutorial_cost(self) -> None:
        if not self._confirm_discard():
            return
        path = resource_root() / "tutorials" / "cost_blade_pair" / "blade_cost_pair.fddx"
        if not path.exists():
            QMessageBox.warning(self, APP_NAME, f"Tutorial file not found:\n{path}")
            return
        self.project = load_project(path)
        self.path = path
        self.dirty = False
        self.refresh()
        self.case_page.bind(self.project, self.path)
        self.tabs.setCurrentIndex(1)
        QMessageBox.information(
            self, APP_NAME,
            "Opened the blade cost pair.\n\n"
            "The question is: is sending a crew when the method flags the turbine cheaper "
            "than waiting until the blade fails? Change the euro values on the Case data tab. "
            "Power and CUSUM are already in the CSVs; the software only adds up the costs.",
        )

    def save_project(self) -> bool:
        if self.path is None:
            return self.save_project_as()
        save_project(self.project, self.path)
        self.dirty = False
        self._sync_title()
        return True

    def save_project_as(self) -> bool:
        path, _ = QFileDialog.getSaveFileName(self, "Save project", "", FILE_FILTER)
        if not path:
            return False
        if not path.endswith(FILE_SUFFIX) and not path.endswith(".json"):
            path += FILE_SUFFIX
        self.path = Path(path)
        return self.save_project()

    def export_markdown(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export protocol", "", "Markdown (*.md);;Text (*.txt)"
        )
        if not path:
            return
        Path(path).write_text(export_markdown(self.project), encoding="utf-8")
        QMessageBox.information(self, APP_NAME, "Protocol exported.")

    def show_glossary(self) -> None:
        html = "".join(f"<p><b>{k}.</b> {v}</p>" for k, v in GLOSSARY.items())
        InfoDialog("Nomenclature", html, self).exec()

    def show_repro_help(self) -> None:
        html = (
            "<p>Chapter 3 practices are shown as recommended. "
            "They are recorded on export so later readers can see what was followed.</p>"
        )
        html += "".join(f"<p><b>{t.title}.</b> {t.ideal}<br/><i>{t.why}</i></p>" for t in TIPS)
        InfoDialog("Reproducibility guidelines", html, self).exec()

    def show_about(self) -> None:
        InfoDialog(
            "About",
            f"<p><b>{APP_NAME}</b> {__version__}</p>"
            "<p>A protocol builder for consistent wind-turbine fault-detection evaluation "
            "(Chapter 7 of O’Connor, 2026). It does not train models or run AD Algorithms.</p>"
            "<p>Metric suggestions follow the evaluation objective, ground-truth metadata and "
            "evaluation design. Literature pointers sit behind the <b>i</b> control.</p>",
            self,
        ).exec()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._confirm_discard():
            event.accept()
        else:
            event.ignore()
