from __future__ import annotations

import json
from pathlib import Path

from scripts.harness_scaffold import (
    apply_harness_scaffold,
    apply_harness_update,
    fingerprint_file,
    harness_dir,
    plan_harness_update,
)


def _install_fresh(tmp_path: Path, project_name: str = "meu-projeto") -> Path:
    apply_harness_scaffold(tmp_path, project_name)
    return tmp_path


def _populate_runs(target: Path) -> Path:
    run_file = harness_dir(target) / "runs" / "2026" / "08" / "run_abc" / "run.json"
    run_file.parent.mkdir(parents=True, exist_ok=True)
    run_file.write_text('{"schema_version": "1.0", "status": "completed"}\n', encoding="utf-8")
    return run_file


def test_update_preserves_runs_intact(tmp_path: Path) -> None:
    target = _install_fresh(tmp_path)
    run_file = _populate_runs(target)
    before = fingerprint_file(run_file)

    apply_harness_update(target, "meu-projeto")

    after = fingerprint_file(run_file)
    assert before == after
    assert run_file.exists()


def test_update_preserves_project_id_and_custom_config(tmp_path: Path) -> None:
    target = _install_fresh(tmp_path)
    config_path = harness_dir(target) / "config.json"
    config = json.loads(config_path.read_text())
    original_project_id = config["project_id"]
    config["retention"]["days"] = 999  # valor customizado manualmente
    config_path.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    apply_harness_update(target, "meu-projeto")

    after = json.loads(config_path.read_text())
    assert after["project_id"] == original_project_id
    assert after["retention"]["days"] == 999


def test_pending_migration_is_listed_with_requires_confirmation(tmp_path: Path) -> None:
    target = _install_fresh(tmp_path)
    config_path = harness_dir(target) / "config.json"
    config = json.loads(config_path.read_text())
    config["schema_version"] = "0.9"  # simula versão desatualizada
    config_path.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    plan = plan_harness_update(target)

    assert len(plan.migrations) == 1
    migration = plan.migrations[0]
    assert migration.requires_confirmation is True
    assert migration.from_version == "0.9"
    assert migration.to_version == "1.0"


def test_migration_only_applied_after_explicit_confirmation(tmp_path: Path) -> None:
    target = _install_fresh(tmp_path)
    config_path = harness_dir(target) / "config.json"
    config = json.loads(config_path.read_text())
    config["schema_version"] = "0.9"
    config_path.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    result_without_confirmation = apply_harness_update(
        target, "meu-projeto", confirm_migrations=False
    )
    assert result_without_confirmation["migrations_applied"] == 0
    assert json.loads(config_path.read_text())["schema_version"] == "0.9"

    result_with_confirmation = apply_harness_update(target, "meu-projeto", confirm_migrations=True)
    assert result_with_confirmation["migrations_applied"] == 1
    assert json.loads(config_path.read_text())["schema_version"] == "1.0"


def test_canceled_migration_leaves_harness_exactly_as_before(tmp_path: Path) -> None:
    target = _install_fresh(tmp_path)
    config_path = harness_dir(target) / "config.json"
    config = json.loads(config_path.read_text())
    config["schema_version"] = "0.9"
    config_path.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    snapshot = {p: p.read_bytes() for p in sorted(harness_dir(target).rglob("*")) if p.is_file()}

    plan_harness_update(target)  # só planeja, nunca escreve

    after = {p: p.read_bytes() for p in sorted(harness_dir(target).rglob("*")) if p.is_file()}
    assert snapshot == after


def test_backup_created_before_migration_applied(tmp_path: Path) -> None:
    target = _install_fresh(tmp_path)
    config_path = harness_dir(target) / "config.json"
    config = json.loads(config_path.read_text())
    config["schema_version"] = "0.9"
    config_path.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    backup_dir = harness_dir(target) / "backups"
    assert not backup_dir.exists()

    apply_harness_update(target, "meu-projeto", confirm_migrations=True)

    assert backup_dir.exists()
    backups = list(backup_dir.glob("config.json.*.bak"))
    assert len(backups) == 1
    backed_up = json.loads(backups[0].read_text())
    assert backed_up["schema_version"] == "0.9"  # backup guarda o estado ANTES da migration
