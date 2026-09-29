"""Domain-level checks for the v1 protocol builder (no GUI)."""

from fdd_eval.domain.advisor import recommend
from fdd_eval.domain.completeness import summarise
from fdd_eval.domain.project import Project
from fdd_eval.io.markdown_export import export_markdown
from fdd_eval.io.project_io import load_project, save_project


def test_roundtrip(tmp_path) -> None:
    path = tmp_path / "demo.fddx"
    project = Project(title="Demo farm")
    project.inputs.data_types = ["data_scada"]
    project.stage1.primary_objective = "obj_early_warning"
    save_project(project, path)
    loaded = load_project(path)
    assert loaded.title == "Demo farm"
    assert loaded.stage1.primary_objective == "obj_early_warning"
    assert loaded.inputs.data_types == ["data_scada"]


def test_completeness_and_advisor() -> None:
    p = Project()
    c = summarise(p)
    assert not c.protocol_complete
    assert c.required_done < c.required_total
    assert recommend(p) == []

    p.inputs.data_types = ["data_scada", "data_metmast"]
    p.inputs.method = "method_nbm"
    p.stage1.primary_objective = "obj_early_warning"
    p.stage1.early_warning.reference_event = "Generator bearing replacement"
    p.stage1.early_warning.detection_point = "detect_fd_condition"
    p.stage2.fault_definition = "Generator-bearing fault"
    p.stage2.labelled_level = "Component"
    p.stage2.evidence_tier = "tier_combined"
    p.stage2.label_representation = "label_interval"
    p.stage2.uncertainty.timing_certainty = "time_unknown"
    p.stage2.healthy_case_evidence = "No relevant alarm or maintenance in matched window"
    p.stage3.case_construction = "case_constructed"
    p.stage3.event_windows.defined = True
    p.stage3.event_windows.boundaries = "6-week window ending at replacement"
    p.stage3.event_windows.window_kind = "window_prefault"
    p.stage3.event_windows.reference_event = "Replacement"
    p.stage3.comparison = "cmp_pairs"
    p.stage3.data_periods.test = "Held-out pairs"
    p.stage3.valid_data_rules = "Exclude shutdown and missing"
    p.stage3.tuning_mode = "tune_heldout"
    p.stage3.tuning_inventory = "inv_all"
    p.stage3.fd_condition = "fd_persistence"
    p.stage4.output_class = "out_binary"
    p.stage4.output_score = "out_hard"
    recs = recommend(p)
    ids = {r.metric.id for r in recs}
    assert "care" in ids
    assert any(r.metric.id == "care" and r.valid for r in recs)
    p.stage4.accepted_metrics = ["care", "care_c", "care_a", "care_r", "care_e"]
    c2 = summarise(p)
    md = export_markdown(p)
    assert "Early Warning" in md
    assert "CARE" in md
    assert "pre-fault" in md.lower() or "Pre-fault" in md
    assert c2.required_done >= 10


def test_synthetic_pair_care_polarity() -> None:
    from pathlib import Path
    from fdd_eval.domain.care import care_pair
    from fdd_eval.domain.case_io import load_case_csv
    from fdd_eval.domain.completeness import summarise as protocol_summarise
    from fdd_eval.io.project_io import load_project

    root = Path(__file__).resolve().parents[1]
    folder = root / "tutorials" / "synthetic_pair"
    faulty = load_case_csv(folder / "faulty.csv", "faulty")
    healthy = load_case_csv(folder / "healthy.csv", "healthy")
    result = care_pair(faulty, healthy, 12)
    assert result.faulty_detected
    assert not result.healthy_detected
    assert result.unified > 0.5

    syn = load_project(folder / "synthetic_cusum_pair.fddx")
    assert protocol_summarise(syn).protocol_complete
    assert syn.stage3.event_windows.window_kind == "window_prefault"

    ch5 = load_project(root / "tutorials" / "chapter5_c2c_care.fddx")
    assert protocol_summarise(ch5).protocol_complete
    assert ch5.stage3.event_windows.window_kind == "window_prefault"


def test_cost_model_roundtrip(tmp_path) -> None:
    path = tmp_path / "cost.fddx"
    project = Project(title="Cost demo")
    project.stage1.primary_objective = "obj_cost"
    project.stage1.cost_impact.model.price_eur_per_mwh = 90.5
    project.stage1.cost_impact.model.inspection_eur = 3500.0
    save_project(project, path)
    loaded = load_project(path)
    assert loaded.has_objective("obj_cost")
    assert loaded.stage1.cost_impact.model.price_eur_per_mwh == 90.5
    assert loaded.stage1.cost_impact.model.inspection_eur == 3500.0


def test_blade_cost_pair() -> None:
    from pathlib import Path
    from fdd_eval.domain.advisor import recommend
    from fdd_eval.domain.care import care_pair
    from fdd_eval.domain.case_io import load_case_csv
    from fdd_eval.domain.completeness import summarise as protocol_summarise
    from fdd_eval.domain.cost import cost_pair

    root = Path(__file__).resolve().parents[1]
    folder = root / "tutorials" / "cost_blade_pair"
    faulty = load_case_csv(folder / "faulty.csv", "faulty")
    healthy = load_case_csv(folder / "healthy.csv", "healthy")
    assert faulty.has_power() and healthy.has_power()
    care = care_pair(faulty, healthy, 72)
    assert care.faulty_detected
    assert not care.healthy_detected

    project = load_project(folder / "blade_cost_pair.fddx")
    assert protocol_summarise(project).protocol_complete
    assert project.stage1.primary_objective == "obj_cost"
    assert "obj_early_warning" in project.stage1.secondary_objectives
    assert project.stage3.event_windows.window_kind == "window_prefault"
    ids = {r.metric.id for r in recommend(project)}
    assert "expected_cost" in ids
    assert "care" in ids

    result = cost_pair(faulty, healthy, project.stage1.cost_impact.model, 72)
    assert result.net_benefit > 0
    assert result.c_wait > result.c_detect
    assert result.healthy.total_eur == 0
    md = export_markdown(project)
    assert "Selling price" in md
    assert "pre-fault" in md.lower()
