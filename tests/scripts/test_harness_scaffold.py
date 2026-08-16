from __future__ import annotations

import json
from pathlib import Path

from scripts.harness_scaffold import (
    apply_harness_scaffold,
    fingerprint_file,
    generate_project_id,
    harness_dir,
    plan_harness_scaffold,
    read_installed_files,
)
from scripts.schema_validation import validate


def test_scaffold_creates_full_structure(tmp_path: Path) -> None:
    apply_harness_scaffold(tmp_path, "meu-projeto")
    base = harness_dir(tmp_path)

    assert (base / "README.md").exists()
    assert (base / "config.json").exists()
    assert (base / ".gitignore").exists()
    assert (base / "state" / "project.json").exists()
    assert (base / "state" / "current-workflow.json").exists()
    assert (base / "state" / "installed-files.json").exists()
    assert (base / "runs").is_dir()
    assert (base / "deliveries").is_dir()
    assert (base / "audit" / "audit.jsonl").exists()
    assert (base / "locks").is_dir()
    assert (base / "runtime").is_dir()
    assert (base / "indexes").is_dir()


def test_scaffold_config_and_project_state_validate_against_schema(tmp_path: Path) -> None:
    apply_harness_scaffold(tmp_path, "meu-projeto")
    base = harness_dir(tmp_path)

    config = json.loads((base / "config.json").read_text())
    ok, errors = validate(config, "harness-config")
    assert ok, errors

    project_state = json.loads((base / "state" / "project.json").read_text())
    ok, errors = validate(project_state, "project-state")
    assert ok, errors

    workflow_state = json.loads((base / "state" / "current-workflow.json").read_text())
    ok, errors = validate(workflow_state, "workflow-state")
    assert ok, errors


def test_scaffold_telemetry_disabled_by_default(tmp_path: Path) -> None:
    apply_harness_scaffold(tmp_path, "meu-projeto")
    config = json.loads((harness_dir(tmp_path) / "config.json").read_text())
    assert config["telemetry"]["enabled"] is False


def test_generate_project_id_is_deterministic_for_same_input(tmp_path: Path) -> None:
    created_at = "2026-08-16T10:00:00+00:00"
    id_1 = generate_project_id(tmp_path, created_at)
    id_2 = generate_project_id(tmp_path, created_at)
    assert id_1 == id_2


def test_generate_project_id_differs_for_different_path(tmp_path: Path) -> None:
    created_at = "2026-08-16T10:00:00+00:00"
    id_a = generate_project_id(tmp_path / "a", created_at)
    id_b = generate_project_id(tmp_path / "b", created_at)
    assert id_a != id_b


def test_gitignore_ignores_exactly_runs_audit_indexes(tmp_path: Path) -> None:
    apply_harness_scaffold(tmp_path, "meu-projeto")
    content = (harness_dir(tmp_path) / ".gitignore").read_text()
    patterns = {line.strip() for line in content.splitlines() if line.strip()}
    assert patterns == {"runs/**", "audit/**", "indexes/**"}


def test_installed_files_has_checksum_for_every_generated_file(tmp_path: Path) -> None:
    apply_harness_scaffold(tmp_path, "meu-projeto")
    base = harness_dir(tmp_path)
    fingerprints = read_installed_files(tmp_path)

    for rel_path, recorded in fingerprints.items():
        recomputed = fingerprint_file(base / rel_path)
        assert recomputed == recorded

    # o próprio installed-files.json não se auto-referencia
    assert "state/installed-files.json" not in fingerprints
    # config.json e README.md, que foram de fato gerados, estão no registro
    assert "config.json" in fingerprints
    assert "README.md" in fingerprints


def test_plan_lists_all_operations_before_writing(tmp_path: Path) -> None:
    plan = plan_harness_scaffold(tmp_path)
    paths = {op.path for op in plan.operations}

    assert not harness_dir(tmp_path).exists()
    assert "config.json" in paths
    assert "state/project.json" in paths
    assert "state/installed-files.json" in paths
    assert len(plan.operations) > 5
