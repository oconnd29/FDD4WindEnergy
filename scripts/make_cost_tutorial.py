"""Generate a synthetic onshore blade-damage pair for the Cost / Impact tutorial.

Wind, power curve, residual and CUSUM are computed here only. The desktop app plots
those columns and scores CARE plus expected cost.
"""

from __future__ import annotations

import csv
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "tutorials" / "cost_blade_pair"

N_TRAIN = 288          # 2 days at 10 min
N_VAL = 72             # 12 hours
N_TEST = 35 * 144      # 35 days
EVENT_LEN = 28 * 144   # 28-day pre-fault window
RATED_KW = 2000.0
CUT_IN = 3.0
RATED_V = 12.0
CUT_OUT = 25.0
MAX_DAMAGE = 0.05      # 5% region-2 loss at the end of the window
K_ALLOW = 0.5
Q_TAU = 0.99
KAPPA = 72
SEED = 4
NOISE_FAULTY = 8.0     # kW
NOISE_HEALTHY = 18.0   # kW, throughout, so |z|-CUSUM does not persist


def median(xs: list[float]) -> float:
    ys = sorted(xs)
    n = len(ys)
    if n % 2:
        return ys[n // 2]
    return 0.5 * (ys[n // 2 - 1] + ys[n // 2])


def mad_scale(xs: list[float]) -> float:
    med = median(xs)
    return median([abs(x - med) for x in xs]) * 1.4826 or 1.0


def quantile(xs: list[float], q: float) -> float:
    ys = sorted(xs)
    pos = q * (len(ys) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return ys[lo]
    w = pos - lo
    return ys[lo] * (1 - w) + ys[hi] * w


def power_curve(v: float, rated: float = RATED_KW) -> float:
    if v < CUT_IN or v >= CUT_OUT:
        return 0.0
    if v >= RATED_V:
        return rated
    frac = (v ** 3 - CUT_IN ** 3) / (RATED_V ** 3 - CUT_IN ** 3)
    return max(rated * frac, 0.0)


def weibull_ms(rng: random.Random) -> float:
    u = max(rng.random(), 1e-12)
    return 9.0 * math.sqrt(-math.log(u))


def wind_series(n: int, rng: random.Random) -> list[float]:
    v = 8.0
    out = []
    for _ in range(n):
        v = 0.92 * v + 0.08 * weibull_ms(rng)
        v = min(max(v, 0.4), 22.0)
        out.append(v)
    return out


def damage_at(t: int, event_start: int, event_end: int) -> float:
    if t < event_start or t >= event_end:
        return 0.0
    span = max(event_end - event_start - 1, 1)
    return MAX_DAMAGE * (t - event_start) / span


def cusum_high(x: list[float], train: list[float], k: float) -> list[float]:
    """One-sided CUSUM for a positive residual (under-production)."""
    med = median(train)
    scale = mad_scale(train)
    s = 0.0
    scores = []
    for xi in x:
        z = (xi - med) / scale
        s = max(0.0, s + z - k)
        scores.append(s)
    return scores


def detection_stats(rows: list[dict], kappa: int) -> dict:
    test = [r for r in rows if r["period"] == "test"]
    event = [r for r in test if r["in_event_window"]]
    alarms_test = sum(r["alarm"] for r in test)
    alarms_event = sum(r["alarm"] for r in event)
    crit = mx = 0
    for r in test:
        crit = crit + 1 if r["alarm"] else max(crit - 1, 0)
        mx = max(mx, crit)
    return {
        "role": rows[0]["case_role"],
        "tau": rows[0]["threshold"],
        "alarms_test": alarms_test,
        "n_test": len(test),
        "alarms_event": alarms_event,
        "n_event": len(event),
        "max_crit": mx,
        "detected": mx >= kappa,
    }


def build_rows(
    role: str,
    wind: list[float],
    rng: random.Random,
    noise_kw: float,
    *,
    apply_damage: bool,
) -> list[dict]:
    n = len(wind)
    event_start = N_TRAIN + N_VAL + (N_TEST - EVENT_LEN)
    event_end = n
    expected = [power_curve(v) for v in wind]
    actual = []
    residual = []
    for t, (v, p_exp) in enumerate(zip(wind, expected)):
        d = damage_at(t, event_start, event_end) if apply_damage else 0.0
        loss = d if v < RATED_V else 0.0
        p = max(p_exp * (1.0 - loss) + rng.gauss(0.0, noise_kw), 0.0)
        actual.append(p)
        residual.append(p_exp - p)
    train_r = residual[:N_TRAIN]
    scores = cusum_high(residual, train_r, K_ALLOW)
    tau = quantile(scores[:N_TRAIN], Q_TAU)
    rows = []
    for t in range(n):
        if t < N_TRAIN:
            period = "train"
        elif t < N_TRAIN + N_VAL:
            period = "val"
        else:
            period = "test"
        in_event = 1 if event_start <= t < event_end else 0
        label = 1 if (role == "faulty" and in_event) else 0
        rows.append({
            "time_index": t,
            "timestamp": t,
            "period": period,
            "case_role": role,
            "wind_speed": round(wind[t], 4),
            "expected_power_kw": round(expected[t], 4),
            "power_kw": round(actual[t], 4),
            "raw": round(actual[t], 4),
            "monitoring_indicator": round(residual[t], 4),
            "anomaly_score": round(scores[t], 4),
            "threshold": round(tau, 4),
            "alarm": int(scores[t] > tau),
            "in_event_window": in_event,
            "instance_label": label,
        })
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _try_pair(seed: int) -> tuple[list[dict], list[dict]]:
    rng_w = random.Random(seed)
    rng_f = random.Random(seed + 17)
    rng_h = random.Random(seed + 31)
    n = N_TRAIN + N_VAL + N_TEST
    wind = wind_series(n, rng_w)
    faulty = build_rows("faulty", wind, rng_f, NOISE_FAULTY, apply_damage=True)
    healthy = build_rows("healthy", wind, rng_h, NOISE_HEALTHY, apply_damage=False)
    return faulty, healthy


def write_readme(seed: int) -> None:
    (OUT / "README.txt").write_text(
        "Synthetic onshore blade-damage pair for the Cost / Impact tutorial.\n"
        "Setting: 2 MW onshore turbine, 10-minute samples, Ireland-style selling price.\n"
        "\n"
        "Monitoring Indicator: power residual (expected curve minus measured power).\n"
        "AD Algorithm: one-sided CUSUM on the residual, k=0.5, threshold = 0.99 quantile of\n"
        "training CUSUM. Same HPs for both cases. Not recomputed in the software.\n"
        "\n"
        "Faulty event: 28-day pre-fault window. Region-2 power loss ramps from 0 to 5%\n"
        "(Sandia/NREL heavy leading-edge erosion is typically up to ~5% AEP). The window\n"
        "ends at a simulated blade-fault stop — it is a pre-fault window, not a fault window.\n"
        "Healthy case: identical wind, no damage, higher measurement noise throughout.\n"
        "\n"
        "Default euro values (change them in the Case data cost panel):\n"
        "  selling price   100 €/MWh  (between RESS 4/5 onshore-wind strikes and 2024–25 SEM DAM)\n"
        "  crew if healthy €4,000     (onshore rope-access call-out order of magnitude)\n"
        "  early repair    €12,000 + 24 h stop\n"
        "  repair if wait  €50,000 + 10 days stop (structural repair, no crane)\n"
        "Selling price is a constant €/MWh assumption, not a contract. RESS is a two-way CfD; "
        "wind capture is often below the DAM average.\n"
        f"Persistence threshold kappa={KAPPA} (12 h at 10 min). Random seed: {seed}.\n",
        encoding="utf-8",
    )


def write_project(kappa: int) -> None:
    from fdd_eval.domain.completeness import summarise
    from fdd_eval.domain.project import Project
    from fdd_eval.io.markdown_export import export_markdown
    from fdd_eval.io.project_io import save_project

    p = Project()
    p.title = "Tutorial — blade damage, Cost / Impact Optimisation"
    p.notes = (
        "Synthetic onshore Irish 2 MW turbine. Primary objective is Cost / Impact: "
        "is sending a crew when the method flags the turbine cheaper than waiting "
        "until the blade fails? Early Warning is secondary so CARE is still reported. "
        "Power, residual and CUSUM are stored in the CSVs; the app only plots them and "
        "adds up the costs. The labelled interval is a pre-fault window ending when "
        "the blade fails."
    )
    p.inputs.data_types = ["data_scada", "data_other_ts"]
    p.inputs.records = ["rec_expert"]
    p.inputs.cost_inputs = [
        "cost_dispatch", "cost_inspection", "cost_downtime",
        "cost_false_positive", "cost_other",
    ]
    p.inputs.method = "method_ad"
    p.inputs.method_notes = (
        "Direct AD: one-sided CUSUM on the power residual versus a simple piecewise "
        "power curve (cut-in 3 m/s, rated 12 m/s, cut-out 25 m/s, 2 MW). "
        "Fixed HPs: k = 0.5, τ = 0.99 training quantile. Not recomputed in the software."
    )

    p.stage1.primary_objective = "obj_cost"
    p.stage1.secondary_objectives = ["obj_early_warning"]
    p.stage1.early_warning.reference_event = (
        "Simulated blade-fault stop that ends the 28-day pre-fault window"
    )
    p.stage1.early_warning.detection_point = "detect_fd_condition"
    p.stage1.early_warning.notes = (
        "Secondary Early Warning: first time the persistence condition is met, not the "
        "first isolated residual alarm."
    )
    p.stage1.cost_impact.cost_terms = [
        "cost_dispatch", "cost_inspection", "cost_downtime",
        "cost_false_positive", "cost_other",
    ]
    p.stage1.cost_impact.sensitivity_planned = True
    p.stage1.cost_impact.notes = (
        "Euro values are tutorial assumptions for onshore Ireland, not a farm quote. "
        "Crane, access-track and H&S delay are omitted. Offshore vessel costs are out of scope."
    )
    m = p.stage1.cost_impact.model
    m.price_eur_per_mwh = 100.0
    m.inspection_eur = 4000.0
    m.planned_repair_eur = 12000.0
    m.planned_downtime_h = 24.0
    m.emergency_repair_eur = 50000.0
    m.emergency_downtime_h = 240.0
    m.rated_power_kw = 2000.0
    m.sample_hours = 1.0 / 6.0
    m.notes = (
        "€100/MWh sits between RESS 4 onshore-wind strike (€90.47/MWh) and recent SEM "
        "DAM averages (~€104/MWh in 2024, ~€114/MWh in 2025). RESS 5 wind ~€100.63/MWh. "
        "This is a constant selling-price assumption, not a contract. Crew visit €4,000 "
        "approximates an onshore rope-access call-out. Early repair €12,000 + 24 h is a "
        "limited leading-edge repair, not a blade swap. Repair after the blade fails "
        "€50,000 + 10 days follows the Wetzel/Sandia structural-repair order of magnitude, "
        "excluding crane."
    )

    p.stage2.fault_definition = (
        "Synthetic blade aerodynamic degradation (leading-edge style): region-2 power "
        "loss ramps from 0 to 5% over 28 days, then a simulated blade-fault stop. "
        "The labelled interval ends at that stop; it is not the faulted operating period."
    )
    p.stage2.labelled_level = "Component (rotor blade). Not a specific damage mechanism."
    p.stage2.evidence_tier = "tier_c"
    p.stage2.evidence_sources = ["rec_expert"]
    p.stage2.symptom_method = "symptom_rule"
    p.stage2.label_representation = "label_interval"
    p.stage2.uncertainty.timing_certainty = "time_point"
    p.stage2.uncertainty.evidence_certainty = "cert_categorical"
    p.stage2.healthy_case_evidence = (
        "Matched healthy case: identical wind series, no damage, higher measurement noise "
        "throughout so CUSUM does not reach the persistence threshold."
    )

    p.stage3.case_construction = "case_constructed"
    p.stage3.case_notes = "One synthetic faulty case and one matched healthy case with the same wind."
    p.stage3.event_windows.defined = True
    p.stage3.event_windows.window_kind = "window_prefault"
    p.stage3.event_windows.boundaries = (
        "Last 28 days of the test period (4,032 ten-minute steps). The window ends at the "
        "simulated blade-fault stop; it is a pre-fault window, not a fault window."
    )
    p.stage3.event_windows.reference_event = "Simulated blade-fault stop (end of window)"
    p.stage3.event_windows.timing_rules = (
        "Onset is known by construction: region-2 loss begins at window start and ramps linearly."
    )
    p.stage3.comparison = "cmp_pairs"
    p.stage3.data_periods.training = "First 288 samples (2 days)."
    p.stage3.data_periods.validation = "Next 72 samples (12 hours)."
    p.stage3.data_periods.test = (
        "Final 35 days; 7 days of healthy test then a 28-day pre-fault window."
    )
    p.stage3.valid_data_rules = "All synthetic samples are valid; no curtailment flags."
    p.stage3.tuning_mode = "tune_oracle"
    p.stage3.tuning_notes = "HPs are fixed for the tutorial, not tuned on this pair."
    p.stage3.fd_condition = "fd_persistence"
    p.stage3.fd_condition_notes = (
        f"Criticality counter with κ = {kappa} (12 hours at 10-minute sampling), the C2C default. "
        "Detection time for the cost model is the first sample at which this condition is met."
    )

    p.stage4.output_class = "out_binary"
    p.stage4.output_score = "out_hard"
    p.stage4.include_stability = "no_stability"
    p.stage4.accepted_metrics = [
        "expected_cost",
        "false_fd_rate",
        "faulty_detection_rate",
        "warning_lead",
        "care",
        "care_c",
        "care_a",
        "care_r",
        "care_e",
    ]
    p.stage4.rejected_metrics = ["cost_weighted_error"]
    p.stage4.override_notes = (
        "The comparison is: send a crew when the method flags the turbine, versus wait "
        "until the blade fails and then repair. Cost-weighted error is rejected as a "
        "duplicate summary of the same euro values. CARE is kept because Early Warning "
        "is a secondary objective."
    )

    p.case_data.faulty_csv = "tutorials/cost_blade_pair/faulty.csv"
    p.case_data.healthy_csv = "tutorials/cost_blade_pair/healthy.csv"
    p.case_data.kappa = kappa
    p.reproducibility.followed = ["data_source", "settings", "gt_provenance", "report"]
    p.reproducibility.notes = (
        "Euro values and the power-curve model are documented assumptions for this synthetic pair. "
        "Replace them with site values before treating the figures as operational."
    )

    save_project(p, OUT / "blade_cost_pair.fddx")
    (OUT / "blade_cost_pair.md").write_text(export_markdown(p), encoding="utf-8")
    c = summarise(p)
    print("Wrote", OUT / "blade_cost_pair.fddx")
    print("Wrote", OUT / "blade_cost_pair.md")
    print(f"Completeness {c.required_done}/{c.required_total}")
    if c.missing_required:
        for nid, msg in c.missing_required:
            print(" missing:", nid, msg)


def main() -> None:
    kappa = KAPPA
    seed = SEED
    faulty, healthy = _try_pair(seed)
    stats_f = detection_stats(faulty, kappa)
    stats_h = detection_stats(healthy, kappa)
    if not (stats_f["detected"] and not stats_h["detected"] and stats_f["alarms_event"] > 50):
        found = False
        for seed in range(0, 80):
            faulty, healthy = _try_pair(seed)
            stats_f = detection_stats(faulty, kappa)
            stats_h = detection_stats(healthy, kappa)
            if stats_f["detected"] and not stats_h["detected"] and stats_f["alarms_event"] > 50:
                found = True
                break
        if not found:
            raise RuntimeError("Could not find a seed with faulty detected and healthy not detected")
    write_csv(OUT / "faulty.csv", faulty)
    write_csv(OUT / "healthy.csv", healthy)
    write_readme(seed)
    print("Wrote", OUT / "faulty.csv")
    print("Wrote", OUT / "healthy.csv")
    print("seed", seed)
    print(
        f"{stats_f['role']}: tau={stats_f['tau']:.3f}, "
        f"test alarms={stats_f['alarms_test']}/{stats_f['n_test']}, "
        f"event alarms={stats_f['alarms_event']}/{stats_f['n_event']}, "
        f"max crit={stats_f['max_crit']} (kappa={kappa}), detected={stats_f['detected']}"
    )
    print(
        f"{stats_h['role']}: tau={stats_h['tau']:.3f}, "
        f"test alarms={stats_h['alarms_test']}/{stats_h['n_test']}, "
        f"event alarms={stats_h['alarms_event']}/{stats_h['n_event']}, "
        f"max crit={stats_h['max_crit']} (kappa={kappa}), detected={stats_h['detected']}"
    )
    write_project(kappa)


if __name__ == "__main__":
    main()
