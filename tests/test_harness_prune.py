from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from scripts.harness_prune import apply_prune, plan_prune
from scripts.harness_scaffold import apply_harness_scaffold, harness_dir


def _make_run(target: Path, run_id: str, started_at: datetime) -> Path:
    base = (
        harness_dir(target)
        / "runs"
        / f"{started_at.year:04d}"
        / f"{started_at.month:02d}"
        / f"run_{run_id}"
    )
    base.mkdir(parents=True, exist_ok=True)
    run = {
        "schema_version": "1.0",
        "run_id": run_id,
        "project_id": "project_01K2XYZ",
        "executor": "claude-code",
        "provider": "anthropic",
        "started_at": started_at.isoformat(),
        "ended_at": None,
        "status": "completed",
    }
    (base / "run.json").write_text(json.dumps(run), encoding="utf-8")
    return base


def _install_with_retention(tmp_path: Path, days: int) -> Path:
    apply_harness_scaffold(tmp_path, "meu-projeto")
    config_path = harness_dir(tmp_path) / "config.json"
    config = json.loads(config_path.read_text())
    config["retention"]["days"] = days
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return tmp_path


def test_dry_run_lists_old_runs_without_deleting(tmp_path: Path) -> None:
    target = _install_with_retention(tmp_path, days=30)
    now = datetime.now(UTC)
    old_run = _make_run(target, "old", now - timedelta(days=60))
    recent_run = _make_run(target, "recent", now - timedelta(days=5))

    result = apply_prune(target, confirm=False)

    assert result["would_remove"] == 1
    assert result["removed"] == 0
    assert old_run.exists()
    assert recent_run.exists()


def test_without_confirm_flag_nothing_is_deleted_even_without_dry_run_flag(tmp_path: Path) -> None:
    target = _install_with_retention(tmp_path, days=30)
    now = datetime.now(UTC)
    old_run = _make_run(target, "old", now - timedelta(days=60))

    # apply_prune sem confirm=True é o "não dry-run explícito, mas ainda sem --confirm"
    apply_prune(target, confirm=False)

    assert old_run.exists()


def test_confirm_removes_only_runs_outside_retention_window(tmp_path: Path) -> None:
    target = _install_with_retention(tmp_path, days=30)
    now = datetime.now(UTC)
    old_run = _make_run(target, "old", now - timedelta(days=60))
    recent_run = _make_run(target, "recent", now - timedelta(days=5))

    result = apply_prune(target, confirm=True)

    assert result["removed"] == 1
    assert not old_run.exists()
    assert recent_run.exists()


def test_prune_never_touches_another_project(tmp_path: Path) -> None:
    project_a = _install_with_retention(tmp_path / "a", days=30)
    project_b = _install_with_retention(tmp_path / "b", days=30)
    now = datetime.now(UTC)
    old_run_a = _make_run(project_a, "old", now - timedelta(days=60))
    old_run_b = _make_run(project_b, "old", now - timedelta(days=60))

    apply_prune(project_a, confirm=True)

    assert not old_run_a.exists()
    assert old_run_b.exists()  # projeto b não foi tocado


def test_plan_prune_is_pure_never_writes(tmp_path: Path) -> None:
    target = _install_with_retention(tmp_path, days=30)
    now = datetime.now(UTC)
    old_run = _make_run(target, "old", now - timedelta(days=60))

    candidates = plan_prune(target, now=now)

    assert len(candidates) == 1
    assert candidates[0].run_id == "old"
    assert old_run.exists()  # plan nunca escreve/apaga
