"""Paint and save the application icon (PNG + ICO)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QApplication


def paint_logo(size: int) -> QPixmap:
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    s = float(size)
    bg = QPainterPath()
    bg.addRoundedRect(QRectF(0, 0, s, s), s * 0.18, s * 0.18)
    grad = QLinearGradient(0, 0, s, s)
    grad.setColorAt(0.0, QColor("#1B3A4B"))
    grad.setColorAt(1.0, QColor("#163038"))
    p.fillPath(bg, grad)

    teal = QColor("#2A9D8F")
    cream = QColor("#F4F1EA")
    gold = QColor("#E9C46A")

    # Tower
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(cream)
    tower = QPainterPath()
    cx = s * 0.42
    tower.moveTo(cx - s * 0.035, s * 0.86)
    tower.lineTo(cx - s * 0.018, s * 0.34)
    tower.lineTo(cx + s * 0.018, s * 0.34)
    tower.lineTo(cx + s * 0.055, s * 0.86)
    tower.closeSubpath()
    p.drawPath(tower)

    # Nacelle
    p.setBrush(teal)
    p.drawRoundedRect(QRectF(cx - s * 0.06, s * 0.30, s * 0.14, s * 0.07), 2, 2)

    # Blades
    p.setBrush(cream)
    hub = QPointF(cx + s * 0.02, s * 0.33)
    p.setPen(QPen(cream, max(2.0, s * 0.035), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    for ang in (90, 210, 330):
        import math
        rad = math.radians(ang)
        p.drawLine(hub, QPointF(hub.x() + math.cos(rad) * s * 0.22, hub.y() - math.sin(rad) * s * 0.22))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(gold)
    p.drawEllipse(hub, s * 0.028, s * 0.028)

    # Evaluation check (protocol / metric)
    p.setPen(QPen(teal, max(2.5, s * 0.06), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPolyline([
        QPointF(s * 0.58, s * 0.70),
        QPointF(s * 0.70, s * 0.82),
        QPointF(s * 0.90, s * 0.54),
    ])
    p.end()
    return pix


def write_ico(path: Path, pixmaps: list[QPixmap]) -> None:
    images: list[bytes] = []
    for pm in pixmaps:
        buf = __import__("io").BytesIO()
        # QPixmap.save to buffer via QByteArray
        from PySide6.QtCore import QByteArray, QBuffer, QIODevice
        ba = QByteArray()
        qbuf = QBuffer(ba)
        qbuf.open(QIODevice.OpenModeFlag.WriteOnly)
        pm.save(qbuf, "PNG")
        images.append(bytes(ba.data()))

    count = len(images)
    offset = 6 + 16 * count
    entries = []
    data = bytearray()
    data += (0).to_bytes(2, "little")
    data += (1).to_bytes(2, "little")
    data += count.to_bytes(2, "little")
    blob = bytearray()
    for pm, png in zip(pixmaps, images):
        w = pm.width() if pm.width() < 256 else 0
        h = pm.height() if pm.height() < 256 else 0
        entries.append((w, h, len(png), offset + len(blob)))
        blob += png
    for w, h, nbytes, off in entries:
        data += bytes([w, h, 0, 0])
        data += (1).to_bytes(2, "little")
        data += (32).to_bytes(2, "little")
        data += nbytes.to_bytes(4, "little")
        data += off.to_bytes(4, "little")
    data += blob
    path.write_bytes(bytes(data))


def main() -> None:
    import sys
    app = QApplication(sys.argv)
    root = Path(__file__).resolve().parents[1] / "fdd_eval" / "assets"
    root.mkdir(parents=True, exist_ok=True)
    sizes = [16, 24, 32, 48, 64, 128, 256]
    pixmaps = [paint_logo(sz) for sz in sizes]
    pixmaps[-1].save(str(root / "app.png"), "PNG")
    write_ico(root / "app.ico", pixmaps)
    print("Wrote", root / "app.ico")
    print("Wrote", root / "app.png")
    app.quit()


if __name__ == "__main__":
    main()
