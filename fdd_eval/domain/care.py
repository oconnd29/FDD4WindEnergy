"""Compute CARE and related scores from loaded case CSVs (no AD Algorithm)."""

from __future__ import annotations

from dataclasses import dataclass

from fdd_eval.domain.case_io import CaseSeries


def f_beta(tp: int, fp: int, fn: int, beta: float = 0.5) -> float:
    b2 = beta * beta
    den = (1 + b2) * tp + b2 * fn + fp
    if den == 0:
        return 0.0
    return (1 + b2) * tp / den


def confusion(labels: list[int], alarms: list[int]) -> tuple[int, int, int, int]:
    tp = fp = tn = fn = 0
    for y, a in zip(labels, alarms):
        if y == 1 and a == 1:
            tp += 1
        elif y == 0 and a == 1:
            fp += 1
        elif y == 0 and a == 0:
            tn += 1
        else:
            fn += 1
    return tp, fp, tn, fn


def criticality(alarms: list[int]) -> list[int]:
    crit = []
    value = 0
    for a in alarms:
        if a == 1:
            value += 1
        else:
            value = max(value - 1, 0)
        crit.append(value)
    return crit


def coverage_faulty(case: CaseSeries) -> float:
    idx = case.test_idx()
    labels = [case.instance_label[i] for i in idx]
    alarms = [case.alarm[i] for i in idx]
    tp, fp, _tn, fn = confusion(labels, alarms)
    return f_beta(tp, fp, fn, 0.5)


def accuracy_healthy(case: CaseSeries) -> float:
    idx = case.test_idx()
    labels = [case.instance_label[i] for i in idx]
    alarms = [case.alarm[i] for i in idx]
    _tp, fp, tn, _fn = confusion(labels, alarms)
    den = tn + fp
    return tn / den if den else 1.0


def case_detected(case: CaseSeries, kappa: int) -> bool:
    idx = case.test_idx()
    alarms = [case.alarm[i] for i in idx]
    crit = criticality(alarms)
    return bool(crit) and max(crit) >= kappa


def earliness_faulty(case: CaseSeries) -> float:
    event = case.event_idx()
    if not event:
        return 0.0
    n = len(event)
    weights = []
    hits = []
    for k, i in enumerate(event):
        xi = k / max(n - 1, 1)
        w = 1.0 if xi <= 0.5 else 2.0 * (1.0 - xi)
        weights.append(w)
        hits.append(w * case.alarm[i])
    den = sum(weights)
    return sum(hits) / den if den else 0.0


@dataclass
class CareResult:
    coverage: float
    accuracy: float
    reliability: float
    earliness: float
    unified: float
    faulty_detected: bool
    healthy_detected: bool
    kappa: int
    notes: str


def care_pair(faulty: CaseSeries, healthy: CaseSeries, kappa: int = 72) -> CareResult:
    c = coverage_faulty(faulty)
    a = accuracy_healthy(healthy)
    e = earliness_faulty(faulty)
    ell_hat_f = case_detected(faulty, kappa)
    ell_hat_h = case_detected(healthy, kappa)
    # One pair: labels [1, 0], decisions [ell_hat_f, ell_hat_h]
    tp = int(ell_hat_f)
    fp = int(ell_hat_h)
    fn = int(not ell_hat_f)
    r = f_beta(tp, fp, fn, 0.5)
    any_faulty_alarm = any(faulty.alarm[i] for i in faulty.test_idx())
    if not any_faulty_alarm:
        unified = 0.0
        note = "Safeguard: no alarms on the faulty test period, so CARE = 0."
    elif a < 0.5:
        unified = a
        note = "Safeguard: Accuracy < 0.5, so CARE is set equal to Accuracy."
    else:
        unified = (1 * c + 1 * e + 1 * r + 2 * a) / 5.0
        note = "Default C2C weights: ω_C = ω_E = ω_R = 1, ω_A = 2 (Gück et al., 2024)."
    return CareResult(
        coverage=c,
        accuracy=a,
        reliability=r,
        earliness=e,
        unified=unified,
        faulty_detected=ell_hat_f,
        healthy_detected=ell_hat_h,
        kappa=kappa,
        notes=note,
    )
