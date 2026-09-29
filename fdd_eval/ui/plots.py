"""Simple time-series plots for case CSVs (Qt painter, no extra plotting library)."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from fdd_eval.domain.case_io import CaseSeries
from fdd_eval.domain.cost import CostPairResult
from fdd_eval.domain.project import CostModel


class SeriesPlot(QWidget):
    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.title = title
        self.series: CaseSeries | None = None
        self.mode = "train_val"  # train_val | test
        self.y_key = "raw"  # raw | score | power_pair
        self.setMinimumHeight(220)

    def set_data(self, series: CaseSeries | None, mode: str, y_key: str) -> None:
        self.series = series
        self.mode = mode
        self.y_key = y_key
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor("#FFFFFF"))
        if self.series is None:
            p.setPen(QColor("#5C6B73"))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Load a case CSV to plot")
            return
        if self.y_key == "power_pair" and not self.series.has_power():
            p.setPen(QColor("#5C6B73"))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No expected/actual power columns")
            return

        idx = self.series.train_val_idx() if self.mode == "train_val" else self.series.test_idx()
        if len(idx) < 2:
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Not enough points")
            return

        margin_l, margin_r, margin_t, margin_b = 52, 16, 28, 28
        plot = QRectF(margin_l, margin_t, self.width() - margin_l - margin_r, self.height() - margin_t - margin_b)
        xs = [self.series.time_index[i] for i in idx]
        expected: list[float] | None = None
        if self.y_key == "raw":
            ys = [self.series.raw[i] for i in idx]
        elif self.y_key == "power_pair":
            ys = [self.series.power_kw[i] for i in idx]
            expected = [self.series.expected_power_kw[i] for i in idx]
        else:
            ys = [self.series.anomaly_score[i] for i in idx]
        x0, x1 = xs[0], xs[-1]
        y0, y1 = min(ys), max(ys)
        if expected:
            y0 = min(y0, min(expected))
            y1 = max(y1, max(expected))
        if self.y_key == "score":
            ths = [self.series.threshold[i] for i in idx]
            y0 = min(y0, min(ths))
            y1 = max(y1, max(ths))
        if y1 - y0 < 1e-9:
            y1 = y0 + 1.0
        pad = 0.08 * (y1 - y0)
        y0 -= pad
        y1 += pad

        def map_x(x: float) -> float:
            return plot.left() + (x - x0) / (x1 - x0) * plot.width()

        def map_y(y: float) -> float:
            return plot.bottom() - (y - y0) / (y1 - y0) * plot.height()

        # Event band on test plot
        if self.mode == "test":
            event = [i for i in idx if self.series.in_event_window[i]]
            if event:
                xa = map_x(self.series.time_index[event[0]])
                xb = map_x(self.series.time_index[event[-1]])
                p.fillRect(QRectF(xa, plot.top(), max(xb - xa, 1), plot.height()), QColor(233, 196, 106, 70))
                p.setPen(QColor("#8A6D1B"))
                p.setFont(QFont("Segoe UI", 8))
                p.drawText(QPointF(xa + 4, plot.top() + 14), "Pre-fault window")

        # Axes
        p.setPen(QPen(QColor("#D5D0C7"), 1))
        p.drawRect(plot)
        p.setPen(QColor("#5C6B73"))
        p.setFont(QFont("Segoe UI", 8))
        p.drawText(QPointF(4, map_y(y1) + 4), f"{y1:.2f}")
        p.drawText(QPointF(4, map_y(y0)), f"{y0:.2f}")
        p.drawText(QPointF(plot.left(), self.height() - 8), str(x0))
        p.drawText(QRectF(plot.right() - 60, self.height() - 18, 60, 16),
                   Qt.AlignmentFlag.AlignRight, str(x1))
        p.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        p.setPen(QColor("#1B3A4B"))
        p.drawText(QPointF(margin_l, 18), self.title)

        # Train/val divider
        if self.mode == "train_val":
            val_i = [i for i in idx if self.series.period[i] == "val"]
            if val_i:
                xv = map_x(self.series.time_index[val_i[0]])
                p.setPen(QPen(QColor("#8A8F98"), 1, Qt.PenStyle.DotLine))
                p.drawLine(QPointF(xv, plot.top()), QPointF(xv, plot.bottom()))
                p.setPen(QColor("#8A8F98"))
                p.setFont(QFont("Segoe UI", 8))
                p.drawText(QPointF(xv + 4, plot.bottom() - 6), "val")

        # Threshold (score plots)
        if self.y_key == "score":
            th = self.series.threshold[idx[0]]
            yth = map_y(th)
            if self.mode == "train_val":
                pen = QPen(QColor(231, 111, 81, 140), 1.6, Qt.PenStyle.DashLine)
            else:
                pen = QPen(QColor(180, 40, 32), 2.0, Qt.PenStyle.DashLine)
            p.setPen(pen)
            p.drawLine(QPointF(plot.left(), yth), QPointF(plot.right(), yth))

        if expected is not None:
            p.setPen(QPen(QColor("#2A9D8F"), 1.4, Qt.PenStyle.DashLine))
            p.drawPolyline(QPolygonF([QPointF(map_x(x), map_y(y)) for x, y in zip(xs, expected)]))
            p.setFont(QFont("Segoe UI", 8))
            p.setPen(QColor("#2A9D8F"))
            p.drawText(QPointF(plot.left() + 6, plot.top() + 28), "expected")

        colour = QColor("#1B3A4B") if self.y_key in ("raw", "power_pair") else QColor("#2A9D8F")
        p.setPen(QPen(colour, 1.5))
        poly = QPolygonF([QPointF(map_x(x), map_y(y)) for x, y in zip(xs, ys)])
        p.drawPolyline(poly)
        if self.y_key == "power_pair":
            p.setFont(QFont("Segoe UI", 8))
            p.setPen(QColor("#1B3A4B"))
            p.drawText(QPointF(plot.left() + 70, plot.top() + 28), "actual")
        p.end()


GOLD = QColor("#E9C46A")
TEAL = QColor("#2A9D8F")
CORAL = QColor("#E76F51")
NAVY = QColor("#1B3A4B")
CREW = QColor("#3D5A80")


def _eur(value: float) -> str:
    if abs(value) >= 1000:
        return f"€{value:,.0f}"
    return f"€{value:.0f}"


class CostOptionsPlot(QWidget):
    """Timeline of lost production plus two stacked bars for the two responses."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.result: CostPairResult | None = None
        self.faulty: CaseSeries | None = None
        self.model: CostModel | None = None
        self.setMinimumHeight(320)

    def set_result(
        self,
        result: CostPairResult | None,
        faulty: CaseSeries | None,
        model: CostModel | None,
    ) -> None:
        self.result = result
        self.faulty = faulty
        self.model = model
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor("#FFFFFF"))
        p.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        p.setPen(NAVY)
        p.drawText(QPointF(12, 18), "Two responses — send a crew when flagged, or wait until the blade fails")

        if self.result is None or self.faulty is None or not self.faulty.has_power():
            p.setPen(QColor("#5C6B73"))
            p.setFont(QFont("Segoe UI", 10))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Load a pair with power columns to plot cost")
            p.end()
            return

        w, h = self.width(), self.height()
        timeline = QRectF(52, 36, w - 68, max(h * 0.36, 88))
        bars = QRectF(52, timeline.bottom() + 22, w - 68, h - timeline.bottom() - 58)
        self._draw_timeline(p, timeline)
        self._draw_bars(p, bars)
        p.setFont(QFont("Segoe UI", 8))
        legend_y = h - 16
        x = 52
        for colour, label in (
            (GOLD, "Lost production"),
            (TEAL, "Repair"),
            (CORAL, "Stop (turbine off)"),
        ):
            p.fillRect(QRectF(x, legend_y - 8, 10, 10), colour)
            p.setPen(NAVY)
            p.drawText(QPointF(x + 14, legend_y + 1), label)
            x += 8 + p.fontMetrics().horizontalAdvance(label) + 18
        if self.result.healthy.inspection_eur > 0:
            p.fillRect(QRectF(x, legend_y - 8, 10, 10), CREW)
            p.setPen(NAVY)
            p.drawText(QPointF(x + 14, legend_y + 1), "Crew to healthy turbine")
        p.end()

    def _draw_timeline(self, p: QPainter, plot: QRectF) -> None:
        event = self.faulty.event_idx()
        if len(event) < 2:
            p.setPen(QColor("#5C6B73"))
            p.drawText(plot, Qt.AlignmentFlag.AlignCenter, "No damage window")
            return
        xs = [self.faulty.time_index[i] for i in event]
        price = self.model.price_eur_per_mwh if self.model else 100.0
        dt = self.model.sample_hours if self.model else 1.0 / 6.0
        lost = []
        running = 0.0
        for i in event:
            delta = max(self.faulty.expected_power_kw[i] - self.faulty.power_kw[i], 0.0)
            running += delta * dt / 1000.0 * price
            lost.append(running)
        x0, x1 = xs[0], xs[-1]
        y0, y1 = 0.0, max(lost[-1], 1.0) * 1.12

        def map_x(x: float) -> float:
            return plot.left() + (x - x0) / (x1 - x0) * plot.width()

        def map_y(y: float) -> float:
            return plot.bottom() - (y - y0) / (y1 - y0) * plot.height()

        p.fillRect(plot, QColor(233, 196, 106, 40))
        p.setPen(QPen(QColor("#D5D0C7"), 1))
        p.drawRect(plot)
        p.setPen(QColor("#5C6B73"))
        p.setFont(QFont("Segoe UI", 8))
        p.drawText(QPointF(4, map_y(y1) + 4), _eur(y1))
        p.drawText(QPointF(4, plot.bottom()), "€0")
        p.setPen(QPen(NAVY, 1.6))
        p.drawPolyline(QPolygonF([QPointF(map_x(x), map_y(y)) for x, y in zip(xs, lost)]))

        det = self.result.faulty.detection_index
        if det is not None and self.faulty.time_index[event[0]] <= self.faulty.time_index[det] <= x1:
            xv = map_x(self.faulty.time_index[det])
            p.setPen(QPen(TEAL, 1.8, Qt.PenStyle.DashLine))
            p.drawLine(QPointF(xv, plot.top()), QPointF(xv, plot.bottom()))
            p.setPen(TEAL)
            p.drawText(QPointF(min(xv + 4, plot.right() - 70), plot.top() + 28), "Crew sent")

        p.setPen(QPen(QColor("#9B2226"), 1.8, Qt.PenStyle.DashLine))
        p.drawLine(QPointF(plot.right(), plot.top()), QPointF(plot.right(), plot.bottom()))
        p.setPen(QColor("#9B2226"))
        p.drawText(QPointF(plot.right() - 72, plot.bottom() - 6), "Blade fails")
        p.setPen(QColor("#8A6D1B"))
        p.drawText(QPointF(plot.left() + 4, plot.bottom() - 6), "Damage starts")
        p.setPen(NAVY)
        p.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
        p.drawText(QPointF(plot.left() + 4, plot.top() + 14), "Lost production while the blade gets worse (€)")

    def _draw_bars(self, p: QPainter, area: QRectF) -> None:
        send = self.result.faulty
        wait = self.result.wait_faulty
        healthy_crew = self.result.healthy.inspection_eur
        send_parts = [
            (send.lost_revenue_eur, GOLD),
            (send.repair_eur, TEAL),
            (send.downtime_eur, CORAL),
            (healthy_crew, CREW),
        ]
        wait_parts = [
            (wait.lost_revenue_eur, GOLD),
            (wait.repair_eur, TEAL),
            (wait.downtime_eur, CORAL),
        ]
        ymax = max(self.result.c_detect, self.result.c_wait, 1.0) * 1.18
        gap = area.width() * 0.18
        bar_w = (area.width() - gap) / 2.5
        lefts = [area.left() + area.width() * 0.12, area.left() + area.width() * 0.58]
        labels = ["Send a crew when flagged", "Wait until the blade fails"]
        totals = [self.result.c_detect, self.result.c_wait]
        stacks = [send_parts, wait_parts]

        p.setPen(QPen(QColor("#D5D0C7"), 1))
        p.drawLine(QPointF(area.left(), area.bottom()), QPointF(area.right(), area.bottom()))
        p.setPen(QColor("#5C6B73"))
        p.setFont(QFont("Segoe UI", 8))
        p.drawText(QPointF(4, area.top() + 8), _eur(ymax))

        for left, parts, label, total in zip(lefts, stacks, labels, totals):
            y = area.bottom()
            for value, colour in parts:
                if value <= 0:
                    continue
                hh = max(value / ymax * area.height(), 3.0)
                y -= hh
                p.fillRect(QRectF(left, y, bar_w, hh), colour)
                if hh > 16:
                    p.setPen(QColor("#FFFFFF"))
                    p.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
                    p.drawText(QRectF(left, y, bar_w, hh), Qt.AlignmentFlag.AlignCenter, _eur(value))
            p.setPen(NAVY)
            p.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
            p.drawText(
                QRectF(left - 12, area.bottom() + 2, bar_w + 24, 14),
                Qt.AlignmentFlag.AlignHCenter,
                _eur(total),
            )
            p.setFont(QFont("Segoe UI", 8))
            p.setPen(QColor("#5C6B73"))
            p.drawText(
                QRectF(left - 28, area.bottom() + 16, bar_w + 56, 16),
                Qt.AlignmentFlag.AlignHCenter,
                label,
            )

