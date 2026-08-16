from __future__ import annotations

import json
from pathlib import Path

from scripts.harness_doctor import diagnose
from scripts.harness_scaffold import apply_harness_scaffold, harness_dir


def _write_manifest(target: Path, telemetry: dict[str, object]) -> None:
    manifest_dir = target / ".claude"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "manifest_schema_version": "2.0",
        "harness_version": "0.1.0",
        "canonical_path": "/home/fabiano/agent-harness-canonico",
        "installed_at": "2026-08-16",
        "mode": "NOVO",
        "capabilities": {
            "workflow": True,
            "dev_loop": True,
            "delivery_metrics": True,
            "telemetry": telemetry,
        },
        "artefacts": {},
    }
    (manifest_dir / "harness-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_intact_project_reports_ok_for_all_capabilities(tmp_path: Path) -> None:
    apply_harness_scaffold(tmp_path, "meu-projeto")
    _write_manifest(tmp_path, {"claude_code": True})

    report = diagnose(tmp_path)
    for capability in ("workflow", "dev_loop", "delivery_metrics"):
        assert report["capabilities"][capability]["status"] == "ok"


def test_manually_edited_file_reports_customized_only_for_its_capability(tmp_path: Path) -> None:
    apply_harness_scaffold(tmp_path, "meu-projeto")
    _write_manifest(tmp_path, {"claude_code": True})

    # edita config.json manualmente, sem passar pelo instalador — mapeado só pra "workflow"
    config_path = harness_dir(tmp_path) / "config.json"
    config_path.write_text(config_path.read_text() + "\n", encoding="utf-8")

    report = diagnose(tmp_path)
    assert report["capabilities"]["workflow"]["status"] == "customized"
    assert report["capabilities"]["dev_loop"]["status"] == "ok"
    assert report["capabilities"]["delivery_metrics"]["status"] == "ok"


def test_missing_expected_file_reports_missing_for_its_capability(tmp_path: Path) -> None:
    apply_harness_scaffold(tmp_path, "meu-projeto")
    _write_manifest(tmp_path, {"claude_code": True})

    (harness_dir(tmp_path) / "audit" / "audit.jsonl").unlink()

    report = diagnose(tmp_path)
    assert report["capabilities"]["delivery_metrics"]["status"] == "missing"
    assert report["capabilities"]["workflow"]["status"] == "ok"


def test_telemetry_declared_false_reports_missing_with_reason(tmp_path: Path) -> None:
    apply_harness_scaffold(tmp_path, "meu-projeto")
    _write_manifest(tmp_path, {"claude_code": False})

    report = diagnose(tmp_path)
    assert report["telemetry"]["claude_code"]["status"] == "missing"
    assert report["telemetry"]["claude_code"]["reason"] is not None


def test_unavailable_executor_reports_unavailable_with_reason_not_missing(tmp_path: Path) -> None:
    apply_harness_scaffold(tmp_path, "meu-projeto")
    _write_manifest(tmp_path, {"claude_code": True, "cursor": "unavailable"})

    report = diagnose(tmp_path)
    assert report["telemetry"]["cursor"]["status"] == "unavailable"
    assert report["telemetry"]["cursor"]["status"] != "missing"
    assert report["telemetry"]["cursor"]["reason"] is not None


def test_diagnose_never_returns_zero_for_unknown_data() -> None:
    empty = Path("/tmp/definitely-does-not-exist-harness-doctor-test")
    report = diagnose(empty)
    assert report["scaffold_checked_files_count"] is None
    for capability in report["capabilities"].values():
        assert capability["status"] == "blocked"
        assert "reason" in capability
