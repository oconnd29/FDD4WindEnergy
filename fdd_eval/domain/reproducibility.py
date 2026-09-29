"""Chapter 3 reproducibility tips: recommended practice."""

from __future__ import annotations

from dataclasses import dataclass

from fdd_eval.domain.project import Project


@dataclass(frozen=True)
class Tip:
    id: str
    title: str
    ideal: str
    why: str
    when: str = ""


TIPS: list[Tip] = [
    Tip(
        "data_source",
        "Record data source and access",
        "Name the operational datasets (farm, met mast, work-order system, …), version or access date, and how they can be retrieved.",
        "Another reader cannot interpret or repeat the evaluation if the records behind the cases are unnamed.",
        "Always relevant for a wind-farm evaluation.",
    ),
    Tip(
        "preprocessing",
        "Document preprocessing",
        "State filtering, resampling, missing-data handling and feature derivation used before the method is applied.",
        "Preprocessing changes both the Monitoring Indicator and the evaluated instances. It is part of the result.",
    ),
    Tip(
        "split_trace",
        "Keep training, tuning and held-out cases traceable",
        "List which cases or periods were available for model development, AD Algorithm tuning, and final evaluation.",
        "Chapter 5 showed that oracle and held-out tuning can change the conclusion. The split is part of the evaluation design.",
        "Especially when Stage 3 uses held-out tuning.",
    ),
    Tip(
        "settings",
        "Record method settings with the result",
        "Store AD Algorithm hyperparameters, the fault-detection condition, thresholds and metric definitions next to the scores.",
        "A metric value without the operating condition cannot be compared.",
    ),
    Tip(
        "gt_provenance",
        "Keep ground-truth provenance",
        "Record evidence sources, tier, timing rules and any cases excluded because of conflicting records.",
        "Unclear ground truth can change the ranking of methods (Wu and Keogh, 2023).",
    ),
    Tip(
        "environment",
        "Note the software environment when scores are computed",
        "When this application (or another script) computes metrics, record package versions or an environment file.",
        "Computational reproducibility in Chapter 3 treats the environment as part of the workflow, not an afterthought.",
        "Required in spirit when v1.1 scoring is used; optional for a protocol-only project.",
    ),
    Tip(
        "report",
        "Export a protocol that another group could interpret",
        "Export the protocol (and later the scores) so the objective, ground truth, design and metrics can be read without the GUI.",
        "Chapter 3 treats reporting and dissemination as part of the workflow.",
    ),
]


def tip_state(project: Project, tip_id: str) -> str:
    if tip_id in project.reproducibility.followed:
        return "followed"
    if tip_id in project.reproducibility.skipped:
        return "skipped"
    return "open"


def mark(project: Project, tip_id: str, followed: bool) -> None:
    for bucket in (project.reproducibility.followed, project.reproducibility.skipped):
        if tip_id in bucket:
            bucket.remove(tip_id)
    if followed:
        project.reproducibility.followed.append(tip_id)
    else:
        project.reproducibility.skipped.append(tip_id)


def open_tips(project: Project) -> list[Tip]:
    return [t for t in TIPS if tip_state(project, t.id) == "open"]
