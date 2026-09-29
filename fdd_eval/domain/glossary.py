"""Short glossary of thesis nomenclature."""

GLOSSARY: dict[str, str] = {
    "AD Algorithm": "Anomaly Detection Algorithm. Assigns a normal/abnormal decision or score to instances of a Monitoring Indicator.",
    "Monitoring Indicator": "The series processed by the AD Algorithm (a raw feature, an NBM residual, or another derived indicator).",
    "NBM": "Normal Behaviour Model. Estimates expected healthy behaviour of a target feature.",
    "Detected anomaly": "An instance flagged by the AD Algorithm. Not automatically a detected fault.",
    "Fault detection": "A case-level decision that detected anomalies provide sufficient evidence of a fault, using the fault-detection condition.",
    "Instance-level AD performance": "How well normal and abnormal instances are distinguished.",
    "Case-level fault-detection performance": "How well faulty and healthy cases are distinguished after the fault-detection condition is applied.",
    "Detection earliness": "When the chosen detection point occurs relative to a reference event.",
    "Event window": "The interval used for evaluation around a reference event. State whether it is a pre-fault window (abnormal behaviour leading up to a fault) or a fault window (the faulted period itself). Care to Compare uses pre-fault windows whose end is the start of the turbine fault.",
    "Pre-fault window": "A labelled anomaly interval that ends when the turbine fault begins. It is chosen instead of a fault window so Early Warning can be scored before other systems already know the fault. The window start is often expert-defined; Care to Compare does not publish the exact numerical conditions used to set that start.",
    "Reference event": "The later event from which warning lead time is measured (alarm, maintenance, replacement, …).",
    "Fault-detection condition": "The rule that converts instance-level detected anomalies into a case-level fault detection (count, persistence, density or pattern).",
    "Oracle tuning": "Hyperparameter selection that may use the evaluated cases. Achievable performance, not deployment.",
    "Held-out tuning": "The evaluated case or pair is excluded from the tuning inventory.",
    "Fault ontology": "What conditions the evaluation represents and at what level they are labelled.",
    "Tier A / B / C": "Evidence strength: confirmed condition (A), strong proxy or multi-source (B), symptom/behaviour (C).",
    "CARE": "Coverage, Accuracy, Reliability and Earliness — a combined Early Warning metric (Gück et al., 2024).",
}
