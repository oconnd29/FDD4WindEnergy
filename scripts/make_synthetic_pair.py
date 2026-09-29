"""Generate a synthetic faulty–healthy pair with a noisy sine Monitoring Indicator and CUSUM scores.

CUSUM is computed here only. The desktop app loads the CSVs and computes metrics.
"""

from __future__ import annotations

import csv
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tutorials" / "synthetic_pair"

N_TRAIN = 288   # 2 days at 10 min
N_VAL = 72      # 12 hours
N_TEST = 216    # 1.5 days
EVENT_LEN = 96  # 16 hours, ending at a simulated fault (pre-fault window)
SINE_PERIOD = 144  # 1 day
# One-sided CUSUM of |z|: k just above E[|Z|]≈0.80 under Gaussian noise.
K_ALLOW = 1.05
Q_TAU = 0.99
SEED = 1
KAPPA = 12


def median(xs: list[float]) -> float:
    ys = sorted(xs)
    n = len(ys)
    if n % 2:
        return ys[n // 2]
    return 0.5 * (ys[n // 2 - 1] + ys[n // 2])


def mad_scale(xs: list[float]) -> float:
    med = median(xs)
    return median([abs(x - med) for x in xs]) * 1.4826 or 1.0


def sine_series(n: int, amp: float, noise: float, rng: random.Random, phase: float = 0.0) -> list[float]:
    out = []
    for t in range(n):
        sig = amp * math.sin(2 * math.pi * t / SINE_PERIOD + phase)
        out.append(sig + rng.gauss(0.0, noise))
    return out


def cusum_scores(x: list[float], train: list[float], k: float) -> list[float]:
    """CUSUM of |z| so a variance increase (not a mean shift) can persist."""
    med = median(train)
    scale = mad_scale(train)
    s = 0.0
    scores = []
    for xi in x:
        z_abs = abs((xi - med) / scale)
        s = max(0.0, s + z_abs - k)
        scores.append(s)
    return scores


def quantile(xs: list[float], q: float) -> float:
    ys = sorted(xs)
    if not ys:
        return 0.0
    pos = q * (len(ys) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return ys[lo]
    w = pos - lo
    return ys[lo] * (1 - w) + ys[hi] * w


def build_case(
    role: str,
    amp: float,
    noise_base: float,
    rng: random.Random,
    *,
    event_noise: float | None = None,
) -> list[dict]:
    n = N_TRAIN + N_VAL + N_TEST
    event_start = N_TRAIN + N_VAL + (N_TEST - EVENT_LEN)
    event_end = N_TRAIN + N_VAL + N_TEST
    x: list[float] = []
    for t in range(n):
        in_event = event_start <= t < event_end
        noise = event_noise if (role == "faulty" and in_event and event_noise is not None) else noise_base
        sig = amp * math.sin(2 * math.pi * t / SINE_PERIOD)
        x.append(sig + rng.gauss(0.0, noise))
    train = x[:N_TRAIN]
    scores = cusum_scores(x, train, K_ALLOW)
    tau = quantile(scores[:N_TRAIN], Q_TAU)
    rows = []
    for t, (xi, si) in enumerate(zip(x, scores)):
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
            "raw": round(xi, 6),
            "monitoring_indicator": round(xi, 6),
            "anomaly_score": round(si, 6),
            "threshold": round(tau, 6),
            "alarm": int(si > tau),
            "in_event_window": in_event,
            "instance_label": label,
        })
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def detection_stats(rows: list[dict], kappa: int) -> dict:
    test = [r for r in rows if r["period"] == "test"]
    event = [r for r in test if r["in_event_window"]]
    alarms_test = sum(r["alarm"] for r in test)
    alarms_event = sum(r["alarm"] for r in event)
    crit = 0
    mx = 0
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


def summarise(rows: list[dict], kappa: int) -> str:
    s = detection_stats(rows, kappa)
    return (
        f"{s['role']}: tau={s['tau']:.3f}, "
        f"test alarms={s['alarms_test']}/{s['n_test']}, "
        f"event alarms={s['alarms_event']}/{s['n_event']}, "
        f"max crit={s['max_crit']} (kappa={kappa}), detected={s['detected']}"
    )


def _try_pair(seed: int) -> tuple[list[dict], list[dict]]:
    rng_f = random.Random(seed)
    rng_h = random.Random(seed + 11)
    # Faulty: sine + noise; std doubles in the pre-fault window.
    faulty = build_case(
        "faulty", amp=0.50, noise_base=0.10, rng=rng_f, event_noise=0.20,
    )
    # Healthy: smaller sine, higher noise throughout (stationary) so |z|-CUSUM
    # does not persist to κ. Matched window is still marked for plotting.
    healthy = build_case(
        "healthy", amp=0.16, noise_base=0.22, rng=rng_h,
    )
    return faulty, healthy


def main() -> None:
    kappa = KAPPA
    seed = SEED
    faulty, healthy = _try_pair(seed)
    stats_f = detection_stats(faulty, kappa)
    stats_h = detection_stats(healthy, kappa)
    if not (stats_f["detected"] and not stats_h["detected"] and stats_f["alarms_event"] > 20):
        found = False
        for seed in range(0, 80):
            faulty, healthy = _try_pair(seed)
            stats_f = detection_stats(faulty, kappa)
            stats_h = detection_stats(healthy, kappa)
            if stats_f["detected"] and not stats_h["detected"] and stats_f["alarms_event"] > 20:
                found = True
                break
        if not found:
            raise RuntimeError("Could not find a seed with faulty detected and healthy not detected")
    write_csv(OUT / "faulty.csv", faulty)
    write_csv(OUT / "healthy.csv", healthy)
    readme = OUT / "README.txt"
    readme.write_text(
        "Synthetic faulty–healthy pair for the Case data tab.\n"
        "Monitoring Indicator: noisy sine wave (stand-in for a residual or raw series).\n"
        "AD Algorithm: one-sided CUSUM of |z| after median/MAD standardisation on the "
        f"training period. Fixed HPs: k={K_ALLOW}, threshold = {Q_TAU} quantile of the "
        "training CUSUM score. Same HPs for both cases. CUSUM of |z| is used so a "
        "variance increase can persist; two-sided CUSUM on z is a mean-shift detector.\n"
        "Faulty event window: pre-fault window at the end of the test period; noise std "
        "is doubled. The window ends at a simulated fault start — it is not a fault window.\n"
        "Healthy case: reduced sine amplitude and higher noise throughout (stationary), "
        "so CUSUM does not reach the persistence threshold. A matched interval is still "
        "drawn on the test plot.\n"
        "The desktop app must not recompute CUSUM; it only plots these columns and CARE.\n"
        f"Persistence threshold used for this short series: kappa={kappa} "
        "(C2C uses 72 at 10-minute sampling).\n"
        f"Random seed: {seed}.\n",
        encoding="utf-8",
    )
    print("Wrote", OUT / "faulty.csv")
    print("Wrote", OUT / "healthy.csv")
    print("seed", seed)
    print(summarise(faulty, kappa))
    print(summarise(healthy, kappa))
    _write_project(kappa)


def _write_project(kappa: int) -> None:
    import sys
    sys.path.insert(0, str(ROOT))
    from fdd_eval.domain.project import Project
    from fdd_eval.io.project_io import save_project

    p = Project()
    p.title = "Synthetic tutorial — noisy sine + CUSUM pair"
    p.notes = (
        "Synthetic faulty–healthy pair used by the Case data tab. The Monitoring Indicator "
        "is a noisy sine wave. CUSUM of |z| (k = 1.05, threshold = 0.99 training quantile) "
        "was computed offline and stored in the CSVs. The app only plots those columns and "
        "computes CARE. The event interval is a pre-fault window ending at a simulated fault, "
        "not a fault window."
    )
    p.inputs.data_types = ["data_other_ts"]
    p.inputs.records = ["rec_expert"]
    p.inputs.method = "method_ad"
    p.inputs.method_notes = (
        "Direct AD: one-sided CUSUM of |z| on the Monitoring Indicator (noisy sine). "
        "Fixed HPs: allowance k = 1.05, τ = 0.99 quantile of training CUSUM scores. "
        "Not recomputed in the software."
    )
    p.stage1.primary_objective = "obj_early_warning"
    p.stage1.early_warning.reference_event = "Simulated fault at the end of the pre-fault window"
    p.stage1.early_warning.detection_point = "detect_fd_condition"
    p.stage2.fault_definition = (
        "Synthetic increase in Monitoring Indicator noise (std doubled) during a pre-fault "
        "window. The labelled interval ends at a simulated fault start; it is not the faulted period."
    )
    p.stage2.labelled_level = "Synthetic event (not a physical component fault)"
    p.stage2.evidence_tier = "tier_c"
    p.stage2.evidence_sources = ["rec_expert"]
    p.stage2.symptom_method = "symptom_rule"
    p.stage2.label_representation = "label_interval"
    p.stage2.uncertainty.timing_certainty = "time_point"
    p.stage2.uncertainty.evidence_certainty = "cert_categorical"
    p.stage2.healthy_case_evidence = (
        "Matched healthy case: same sampling; smaller sine amplitude and higher noise "
        "throughout (stationary). CUSUM of |z| does not reach the persistence threshold."
    )
    p.stage3.case_construction = "case_constructed"
    p.stage3.case_notes = "One synthetic faulty case and one matched healthy case."
    p.stage3.event_windows.defined = True
    p.stage3.event_windows.window_kind = "window_prefault"
    p.stage3.event_windows.boundaries = (
        "Last 96 ten-minute steps of the test period (16 hours). The window ends at the "
        "simulated fault; it is a pre-fault window, not a fault window."
    )
    p.stage3.event_windows.reference_event = "Simulated fault start (end of window)"
    p.stage3.event_windows.timing_rules = "Onset is known by construction (noise std doubles at window start)."
    p.stage3.comparison = "cmp_pairs"
    p.stage3.data_periods.training = "First 288 samples (2 days)."
    p.stage3.data_periods.validation = "Next 72 samples (12 hours)."
    p.stage3.data_periods.test = "Final 216 samples; pre-fault window in the last 96."
    p.stage3.valid_data_rules = "All synthetic samples are valid."
    p.stage3.tuning_mode = "tune_oracle"
    p.stage3.tuning_notes = "HPs are fixed for the tutorial, not tuned on this pair."
    p.stage3.fd_condition = "fd_persistence"
    p.stage3.fd_condition_notes = (
        f"Criticality counter with κ = {kappa} (short series). C2C uses κ = 72 at 10-minute sampling."
    )
    p.stage4.output_class = "out_binary"
    p.stage4.output_score = "out_hard"
    p.stage4.include_stability = "no_stability"
    p.stage4.accepted_metrics = ["care", "care_c", "care_a", "care_r", "care_e"]
    p.case_data.faulty_csv = "tutorials/synthetic_pair/faulty.csv"
    p.case_data.healthy_csv = "tutorials/synthetic_pair/healthy.csv"
    p.case_data.kappa = kappa
    p.reproducibility.followed = ["data_source", "settings", "gt_provenance", "report"]
    save_project(p, OUT / "synthetic_cusum_pair.fddx")
    print("Wrote", OUT / "synthetic_cusum_pair.fddx")


if __name__ == "__main__":
    main()
