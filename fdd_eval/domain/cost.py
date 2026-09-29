"""Expected cost / net benefit from loaded case CSVs and declared tariffs.

The app does not run an AD Algorithm. Alarms, power and expected power come from the CSV.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from fdd_eval.domain.care import case_detected, criticality
from fdd_eval.domain.case_io import CaseSeries
from fdd_eval.domain.project import CostModel


def first_detection_index(case: CaseSeries, kappa: int) -> int | None:
    idx = case.test_idx()
    alarms = [case.alarm[i] for i in idx]
    crit = criticality(alarms)
    for i, value in zip(idx, crit):
        if value >= kappa:
            return i
    return None


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def lost_mwh(case: CaseSeries, indices: list[int], sample_hours: float) -> float:
    total = 0.0
    for i in indices:
        delta = max(case.expected_power_kw[i] - case.power_kw[i], 0.0)
        total += delta * sample_hours / 1000.0
    return total


def downtime_mwh(case: CaseSeries, hours: float) -> float:
    event = case.event_idx() or case.test_idx()
    mean_kw = _mean([case.expected_power_kw[i] for i in event])
    return mean_kw * hours / 1000.0


def _indices_until(case: CaseSeries, end_i: int | None) -> list[int]:
    event = case.event_idx()
    if end_i is None:
        return event
    return [i for i in event if i <= end_i]


@dataclass
class CostBreakdown:
    lost_revenue_eur: float
    repair_eur: float
    downtime_eur: float
    inspection_eur: float
    total_eur: float
    detected: bool
    detection_index: int | None
    lost_mwh: float
    notes: str


@dataclass
class CostPairResult:
    c_detect: float
    c_wait: float
    net_benefit: float
    faulty: CostBreakdown
    healthy: CostBreakdown
    wait_faulty: CostBreakdown
    sensitivity: dict[str, float]
    notes: str


def score_case(
    case: CaseSeries,
    model: CostModel,
    kappa: int,
    *,
    role: str,
    follow_detection: bool,
) -> CostBreakdown:
    detected = case_detected(case, kappa)
    det_i = first_detection_index(case, kappa) if detected else None
    price = model.price_eur_per_mwh

    if role == "healthy":
        if follow_detection and detected:
            total = model.inspection_eur
            return CostBreakdown(
                lost_revenue_eur=0.0,
                repair_eur=0.0,
                downtime_eur=0.0,
                inspection_eur=model.inspection_eur,
                total_eur=total,
                detected=True,
                detection_index=det_i,
                lost_mwh=0.0,
                notes="Crew sent to a healthy turbine.",
            )
        return CostBreakdown(
            lost_revenue_eur=0.0,
            repair_eur=0.0,
            downtime_eur=0.0,
            inspection_eur=0.0,
            total_eur=0.0,
            detected=detected,
            detection_index=det_i,
            lost_mwh=0.0,
            notes="No crew sent.",
        )

    act_on_detection = follow_detection and detected
    if act_on_detection:
        idxs = _indices_until(case, det_i)
        lost = lost_mwh(case, idxs, model.sample_hours)
        down = downtime_mwh(case, model.planned_downtime_h)
        lost_eur = lost * price
        down_eur = down * price
        repair = model.planned_repair_eur
        note = (
            "The method flagged the damaged turbine: lost production until the crew arrives, "
            "then the early repair and a short stop."
        )
    else:
        idxs = _indices_until(case, None)
        lost = lost_mwh(case, idxs, model.sample_hours)
        down = downtime_mwh(case, model.emergency_downtime_h)
        lost_eur = lost * price
        down_eur = down * price
        repair = model.emergency_repair_eur
        note = (
            "No crew was sent: lost production through the whole damage period, "
            "then the larger repair and a long stop after the blade fails."
        )
    total = lost_eur + repair + down_eur
    return CostBreakdown(
        lost_revenue_eur=lost_eur,
        repair_eur=repair,
        downtime_eur=down_eur,
        inspection_eur=0.0,
        total_eur=total,
        detected=detected,
        detection_index=det_i,
        lost_mwh=lost,
        notes=note,
    )


def _scale(model: CostModel, price_scale: float, crew_scale: float) -> CostModel:
    return replace(
        model,
        price_eur_per_mwh=model.price_eur_per_mwh * price_scale,
        inspection_eur=model.inspection_eur * crew_scale,
        planned_repair_eur=model.planned_repair_eur * crew_scale,
        emergency_repair_eur=model.emergency_repair_eur * crew_scale,
    )


def cost_pair(faulty: CaseSeries, healthy: CaseSeries, model: CostModel, kappa: int) -> CostPairResult:
    if not (faulty.has_power() and healthy.has_power()):
        empty = CostBreakdown(0, 0, 0, 0, 0, False, None, 0, "Power columns missing.")
        return CostPairResult(
            c_detect=0.0,
            c_wait=0.0,
            net_benefit=0.0,
            faulty=empty,
            healthy=empty,
            wait_faulty=empty,
            sensitivity={},
            notes="Load CSVs that include expected_power_kw and power_kw to score cost.",
        )

    f_act = score_case(faulty, model, kappa, role="faulty", follow_detection=True)
    h_act = score_case(healthy, model, kappa, role="healthy", follow_detection=True)
    f_wait = score_case(faulty, model, kappa, role="faulty", follow_detection=False)
    c_detect = f_act.total_eur + h_act.total_eur
    c_wait = f_wait.total_eur
    net = c_wait - c_detect

    sensitivity = {}
    for name, pscale, cscale in (
        ("price_0.5x", 0.5, 1.0),
        ("price_1.5x", 1.5, 1.0),
        ("crew_0.5x", 1.0, 0.5),
        ("crew_1.5x", 1.0, 1.5),
    ):
        alt = _scale(model, pscale, cscale)
        fa = score_case(faulty, alt, kappa, role="faulty", follow_detection=True)
        ha = score_case(healthy, alt, kappa, role="healthy", follow_detection=True)
        fw = score_case(faulty, alt, kappa, role="faulty", follow_detection=False)
        sensitivity[name] = (fw.total_eur) - (fa.total_eur + ha.total_eur)

    note = (
        "Two responses are compared. Send a crew when the method flags the turbine, "
        "or wait until the blade fails and then repair. "
        "Selling price is a constant €/MWh assumption, not a contract. "
        "The extra lines show the same comparison if the selling price or the crew/repair "
        "costs are halved or increased by half."
    )
    return CostPairResult(
        c_detect=c_detect,
        c_wait=c_wait,
        net_benefit=net,
        faulty=f_act,
        healthy=h_act,
        wait_faulty=f_wait,
        sensitivity=sensitivity,
        notes=note,
    )
