Synthetic faulty–healthy pair for the Case data tab.
Monitoring Indicator: noisy sine wave (stand-in for a residual or raw series).
AD Algorithm: one-sided CUSUM of |z| after median/MAD standardisation on the training period. Fixed HPs: k=1.05, threshold = 0.99 quantile of the training CUSUM score. Same HPs for both cases. CUSUM of |z| is used so a variance increase can persist; two-sided CUSUM on z is a mean-shift detector.
Faulty event window: pre-fault window at the end of the test period; noise std is doubled. The window ends at a simulated fault start — it is not a fault window.
Healthy case: reduced sine amplitude and higher noise throughout (stationary), so CUSUM does not reach the persistence threshold. A matched interval is still drawn on the test plot.
The desktop app must not recompute CUSUM; it only plots these columns and CARE.
Persistence threshold used for this short series: kappa=12 (C2C uses 72 at 10-minute sampling).
Random seed: 1.
