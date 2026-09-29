"""Small painted icons for choice families and node status."""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap, QPolygon

from fdd_eval.domain.choices import CHOICES

PALETTE = {
    "instance": "#3D5A80",
    "case": "#2A9D8F",
    "earliness": "#E9C46A",
    "combined": "#7B6C9C",
    "operational": "#E76F51",
    "early_warning": "#E9C46A",
    "maintenance": "#2A9D8F",
    "diagnostic": "#3D5A80",
    "cost": "#E76F51",
    "tier_a": "#2A9D8F",
    "tier_b": "#3D5A80",
    "tier_c": "#E9A825",
    "unlabelled": "#8A8F98",
    "label_hard": "#1B3A4B",
    "label_soft": "#7B6C9C",
    "label_interval": "#3D5A80",
    "oracle": "#E76F51",
    "heldout": "#2A9D8F",
    "data_scada": "#1B3A4B",
    "data_vibration": "#7B6C9C",
    "data_alarms": "#E76F51",
    "data_metmast": "#2A9D8F",
    "data_other": "#8A8F98",
    "complete": "#2A9D8F",
    "partial": "#E9A825",
    "empty": "#C5C8CE",
    "info": "#3D5A80",
}


def _pm(size: int = 28) -> QPixmap:
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    return pix


def _painter(pix: QPixmap) -> QPainter:
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    return p


def _pen(color: str, width: float = 1.8) -> QPen:
    pen = QPen(QColor(color))
    pen.setWidthF(width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pen


def paint_icon(key: str, size: int = 28) -> QIcon:
    color = PALETTE.get(key, "#1B3A4B")
    pix = _pm(size)
    p = _painter(pix)
    s = size
    m = s * 0.18
    p.setPen(_pen(color, s * 0.07))
    p.setBrush(Qt.BrushStyle.NoBrush)

    if key == "instance":
        p.setBrush(QColor(color))
        p.drawEllipse(QRectF(s * 0.32, s * 0.32, s * 0.36, s * 0.36))
    elif key == "case":
        p.drawRoundedRect(QRectF(m, m * 1.2, s - 2 * m, s - 2.4 * m), 3, 3)
        p.setBrush(QColor(color))
        p.drawEllipse(QRectF(s * 0.28, s * 0.42, s * 0.14, s * 0.14))
        p.drawEllipse(QRectF(s * 0.56, s * 0.42, s * 0.14, s * 0.14))
    elif key == "earliness":
        p.drawEllipse(QRectF(m, m, s - 2 * m, s - 2 * m))
        p.drawLine(s * 0.5, s * 0.5, s * 0.5, s * 0.28)
        p.drawLine(s * 0.5, s * 0.5, s * 0.72, s * 0.5)
    elif key == "combined":
        p.drawEllipse(QRectF(m, s * 0.28, s * 0.48, s * 0.48))
        p.drawEllipse(QRectF(s * 0.38, s * 0.28, s * 0.48, s * 0.48))
    elif key in ("operational", "cost", "maintenance"):
        # wrench-ish / coin stack
        p.drawEllipse(QRectF(s * 0.22, s * 0.38, s * 0.56, s * 0.42))
        p.drawArc(QRect(int(s * 0.22), int(s * 0.22), int(s * 0.56), int(s * 0.42)), 0, 180 * 16)
        p.drawArc(QRect(int(s * 0.22), int(s * 0.12), int(s * 0.56), int(s * 0.42)), 0, 180 * 16)
    elif key == "early_warning":
        path = QPainterPath()
        path.moveTo(s * 0.5, m)
        path.lineTo(s - m, s * 0.78)
        path.lineTo(m, s * 0.78)
        path.closeSubpath()
        p.drawPath(path)
        p.setBrush(QColor(color))
        p.drawEllipse(QRectF(s * 0.46, s * 0.42, s * 0.08, s * 0.08))
        p.drawLine(int(s * 0.5), int(s * 0.52), int(s * 0.5), int(s * 0.66))
    elif key == "diagnostic":
        p.drawEllipse(QRectF(m, m, s * 0.52, s * 0.52))
        p.drawLine(s * 0.58, s * 0.58, s * 0.82, s * 0.82)
    elif key == "tier_a":
        path = QPainterPath()
        path.moveTo(s * 0.5, m)
        path.lineTo(s - m, s * 0.38)
        path.lineTo(s - m, s * 0.62)
        path.lineTo(s * 0.5, s - m)
        path.lineTo(m, s * 0.62)
        path.lineTo(m, s * 0.38)
        path.closeSubpath()
        p.setBrush(QColor(color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(path)
    elif key == "tier_b":
        p.drawEllipse(QRectF(m * 0.7, s * 0.28, s * 0.46, s * 0.46))
        p.drawEllipse(QRectF(s * 0.38, s * 0.28, s * 0.46, s * 0.46))
    elif key == "tier_c":
        p.drawPolyline(QPolygon([
            QPoint(int(m), int(s * 0.62)),
            QPoint(int(s * 0.32), int(s * 0.38)),
            QPoint(int(s * 0.5), int(s * 0.7)),
            QPoint(int(s * 0.7), int(s * 0.32)),
            QPoint(int(s - m), int(s * 0.55)),
        ]))
    elif key == "unlabelled":
        p.drawEllipse(QRectF(m, m, s - 2 * m, s - 2 * m))
        p.drawLine(s * 0.5, s * 0.32, s * 0.5, s * 0.52)
        p.drawEllipse(QRectF(s * 0.46, s * 0.62, s * 0.08, s * 0.08))
    elif key == "label_hard":
        p.drawRoundedRect(QRectF(m, s * 0.32, s - 2 * m, s * 0.36), 3, 3)
    elif key == "label_soft":
        p.setBrush(QColor(color))
        p.setOpacity(0.35)
        p.drawEllipse(QRectF(m, m, s - 2 * m, s - 2 * m))
        p.setOpacity(1)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(m, m, s - 2 * m, s - 2 * m))
    elif key == "label_interval":
        p.drawLine(m, s * 0.5, s - m, s * 0.5)
        p.drawLine(m, s * 0.35, m, s * 0.65)
        p.drawLine(s - m, s * 0.35, s - m, s * 0.65)
    elif key == "oracle":
        p.drawEllipse(QRectF(m, m, s - 2 * m, s - 2 * m))
        p.drawText(QRect(0, 0, s, s), Qt.AlignmentFlag.AlignCenter, "*")
    elif key == "heldout":
        p.drawRect(QRectF(m, m, s * 0.42, s - 2 * m))
        p.drawRect(QRectF(s * 0.52, m, s * 0.32, s - 2 * m))
    elif key == "data_scada":
        p.drawRect(QRectF(m, m * 1.4, s - 2 * m, s * 0.22))
        p.drawRect(QRectF(m, s * 0.52, s - 2 * m, s * 0.22))
    elif key == "data_vibration":
        p.drawPolyline(QPolygon([
            QPoint(int(m), int(s * 0.5)),
            QPoint(int(s * 0.3), int(s * 0.22)),
            QPoint(int(s * 0.45), int(s * 0.78)),
            QPoint(int(s * 0.65), int(s * 0.3)),
            QPoint(int(s - m), int(s * 0.5)),
        ]))
    elif key == "data_alarms":
        p.drawEllipse(QRectF(s * 0.28, m, s * 0.44, s * 0.44))
        p.drawRect(QRectF(s * 0.42, s * 0.55, s * 0.16, s * 0.22))
    elif key == "data_metmast":
        p.drawLine(s * 0.5, m, s * 0.5, s - m)
        p.drawLine(s * 0.5, s * 0.32, s * 0.78, s * 0.22)
        p.drawLine(s * 0.5, s * 0.48, s * 0.78, s * 0.38)
    elif key == "complete":
        p.setPen(_pen(color, s * 0.1))
        p.drawPolyline(QPolygon([
            QPoint(int(s * 0.22), int(s * 0.52)),
            QPoint(int(s * 0.42), int(s * 0.72)),
            QPoint(int(s * 0.78), int(s * 0.28)),
        ]))
    elif key == "partial":
        p.drawEllipse(QRectF(m, m, s - 2 * m, s - 2 * m))
        p.drawLine(s * 0.5, s * 0.28, s * 0.5, s * 0.5)
        p.drawLine(s * 0.5, s * 0.5, s * 0.68, s * 0.62)
    elif key == "empty":
        p.drawEllipse(QRectF(m, m, s - 2 * m, s - 2 * m))
    elif key == "info":
        p.drawEllipse(QRectF(m, m, s - 2 * m, s - 2 * m))
        p.drawText(QRect(0, 1, s, s), Qt.AlignmentFlag.AlignCenter, "i")
    else:
        p.drawRoundedRect(QRectF(m, m, s - 2 * m, s - 2 * m), 4, 4)

    p.end()
    return QIcon(pix)


def icon_for_choice(choice_id: str, size: int = 28) -> QIcon:
    choice = CHOICES.get(choice_id)
    key = choice.icon if choice else "empty"
    return paint_icon(key, size)


def status_icon(state: str, size: int = 18) -> QIcon:
    return paint_icon(state if state in ("complete", "partial", "empty") else "empty", size)
