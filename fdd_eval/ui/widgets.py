"""Reusable UI controls: icon+name choices, i-panel, node cards."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from fdd_eval.domain.choices import Choice, group
from fdd_eval.domain.nodes import NodeSpec
from fdd_eval.ui.icons import icon_for_choice, paint_icon, status_icon


class InfoDialog(QDialog):
    def __init__(self, title: str, body_html: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(520, 420)
        layout = QVBoxLayout(self)
        heading = QLabel(title)
        heading.setObjectName("SectionTitle")
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(body_html)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        buttons.clicked.connect(self.accept)
        layout.addWidget(heading)
        layout.addWidget(browser)
        layout.addWidget(buttons)


def choice_html(choice: Choice) -> str:
    parts = [f"<p>{choice.definition}</p>"]
    if choice.contrast:
        parts.append(f"<p><b>What this is not.</b> {choice.contrast}</p>")
    if choice.when:
        parts.append(f"<p><b>When to select it.</b> {choice.when}</p>")
    if choice.citations:
        cites = "<br/>".join(choice.citations)
        parts.append(f"<p><b>References.</b><br/>{cites}</p>")
    return "".join(parts)


class ChoiceChip(QFrame):
    selected = Signal(str)
    info_requested = Signal(str)

    def __init__(self, choice: Choice, parent=None) -> None:
        super().__init__(parent)
        self.choice = choice
        self.setObjectName("ChoiceChip")
        self.setProperty("selected", False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        row = QHBoxLayout(self)
        row.setContentsMargins(8, 6, 6, 6)
        icon = QLabel()
        icon.setPixmap(icon_for_choice(choice.id, 26).pixmap(26, 26))
        name = QLabel(choice.label)
        name.setWordWrap(True)
        name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        info = QPushButton("i")
        info.setObjectName("InfoBtn")
        info.setToolTip("What this option means")
        info.clicked.connect(lambda: self.info_requested.emit(choice.id))
        row.addWidget(icon)
        row.addWidget(name, 1)
        row.addWidget(info)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.selected.emit(self.choice.id)
        super().mousePressEvent(event)

    def set_on(self, on: bool) -> None:
        self.setProperty("selected", on)
        self.style().unpolish(self)
        self.style().polish(self)


class ChoiceGroup(QWidget):
    changed = Signal()

    def __init__(
        self,
        ids: list[str],
        *,
        exclusive: bool = True,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.exclusive = exclusive
        self._ids = ids
        self._values: set[str] = set()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self._chips: dict[str, ChoiceChip] = {}
        for choice in group(*ids):
            chip = ChoiceChip(choice)
            chip.selected.connect(self._on_select)
            chip.info_requested.connect(self._on_info)
            layout.addWidget(chip)
            self._chips[choice.id] = chip

    def _on_info(self, choice_id: str) -> None:
        choice = next(c for c in group(*self._ids) if c.id == choice_id)
        InfoDialog(choice.label, choice_html(choice), self).exec()

    def _on_select(self, choice_id: str) -> None:
        if self.exclusive:
            self._values = {choice_id}
        elif choice_id in self._values:
            self._values.remove(choice_id)
        else:
            self._values.add(choice_id)
        self._refresh()
        self.changed.emit()

    def _refresh(self) -> None:
        for cid, chip in self._chips.items():
            chip.set_on(cid in self._values)

    def set_value(self, value: str | list[str] | None) -> None:
        if value is None or value == "":
            self._values = set()
        elif isinstance(value, list):
            self._values = set(value)
        else:
            self._values = {value}
        self._refresh()

    def value(self) -> str:
        return next(iter(self._values), "")

    def values(self) -> list[str]:
        return [i for i in self._ids if i in self._values]


class NodeCard(QFrame):
    clicked = Signal(str)

    def __init__(self, spec: NodeSpec, parent=None) -> None:
        super().__init__(parent)
        self.spec = spec
        self.setObjectName("NodeCard")
        self.setProperty("selected", False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(88)
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        self._status = QLabel()
        self._title = QLabel(spec.title)
        self._title.setObjectName("SectionTitle")
        self._title.setWordWrap(True)
        top.addWidget(self._status)
        top.addWidget(self._title, 1)
        self._summary = QLabel(spec.summary)
        self._summary.setObjectName("Hint")
        self._summary.setWordWrap(True)
        self._missing = QLabel()
        self._missing.setObjectName("Hint")
        self._missing.setWordWrap(True)
        layout.addLayout(top)
        layout.addWidget(self._summary)
        layout.addWidget(self._missing)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.spec.id)
        super().mousePressEvent(event)

    def set_selected(self, on: bool) -> None:
        self.setProperty("selected", on)
        self.style().unpolish(self)
        self.style().polish(self)

    def set_status(self, state: str, missing: list[str]) -> None:
        self._status.setPixmap(status_icon(state, 20).pixmap(20, 20))
        req = "" if self.spec.required else " (optional)"
        self._title.setText(self.spec.title + req)
        if missing and state != "complete":
            self._missing.setText(missing[0])
        elif state == "complete":
            self._missing.setText("Complete")
        else:
            self._missing.setText("Not started" + (" — optional" if not self.spec.required else ""))


def labelled_group(title: str, widget: QWidget, hint: str = "") -> QWidget:
    box = QWidget()
    layout = QVBoxLayout(box)
    layout.setContentsMargins(0, 0, 0, 8)
    lab = QLabel(title)
    lab.setObjectName("SectionTitle")
    layout.addWidget(lab)
    if hint:
        h = QLabel(hint)
        h.setObjectName("Hint")
        h.setWordWrap(True)
        layout.addWidget(h)
    layout.addWidget(widget)
    return box
