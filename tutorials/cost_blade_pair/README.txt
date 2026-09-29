Synthetic onshore blade-damage pair for the Cost / Impact tutorial.
Setting: 2 MW onshore turbine, 10-minute samples, Ireland-style selling price.

Monitoring Indicator: power residual (expected curve minus measured power).
AD Algorithm: one-sided CUSUM on the residual, k=0.5, threshold = 0.99 quantile of
training CUSUM. Same HPs for both cases. Not recomputed in the software.

Faulty event: 28-day pre-fault window. Region-2 power loss ramps from 0 to 5%
(Sandia/NREL heavy leading-edge erosion is typically up to ~5% AEP). The window
ends at a simulated blade-fault stop — it is a pre-fault window, not a fault window.
Healthy case: identical wind, no damage, higher measurement noise throughout.

Default euro values (change them in the Case data cost panel):
  selling price   100 €/MWh  (between RESS 4/5 onshore-wind strikes and 2024–25 SEM DAM)
  crew if healthy €4,000     (onshore rope-access call-out order of magnitude)
  early repair    €12,000 + 24 h stop
  repair if wait  €50,000 + 10 days stop (structural repair, no crane)
Selling price is a constant €/MWh assumption, not a contract. RESS is a two-way CfD; wind capture is often below the DAM average.
Persistence threshold kappa=72 (12 h at 10 min). Random seed: 4.
