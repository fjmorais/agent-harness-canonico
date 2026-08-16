from __future__ import annotations

import json
from pathlib import Path

import pytest

import scripts.schema_validation as schema_validation
from scripts.harness_doctor import diagnose
from scripts.harness_scaffold import apply_harness_scaffold, harness_dir
from scripts.schema_validation import assert_write_compatible, is_schema_version_newer


def test_is_schema_version_newer() -> None:
    assert is_schema_version_newer("1.1", "1.0") is True
    assert is_schema_version_newer("1.0", "1.1") is False
    assert is_schema_version_newer("1.0", "1.0") is False
    assert is_schema_version_newer("1.10", "1.9") is True  # comparação numérica, não lexicográfica


def test_write_with_newer_schema_version_than_pinned_is_rejected() -> None:
    with pytest.raises(ValueError, match="rejeitada"):
        assert_write_compatible(pinned_version="1.0", payload_version="1.1")


def test_write_with_pinned_or_older_schema_version_is_accepted() -> None:
    assert_write_compatible(pinned_version="1.0", payload_version="1.0")  # não levanta
    assert_write_compatible(pinned_version="1.0", payload_version="0.9")  # não levanta


def _write_compatibility_fixture(schemas_dir: Path, supported: list[str]) -> None:
    compatibility = {
        "policy": "current_and_previous",
        "schemas": {"harness-config": {"current": supported[0], "supported": supported}},
    }
    (schemas_dir / "compatibility.json").write_text(json.dumps(compatibility), encoding="utf-8")


def test_doctor_reports_ok_when_schema_version_within_n_minus_1_window(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture_schemas_dir = tmp_path / "fixture_schemas"
    fixture_schemas_dir.mkdir()
    _write_compatibility_fixture(fixture_schemas_dir, ["1.0", "0.9"])
    monkeypatch.setattr(
        schema_validation, "COMPATIBILITY_PATH", fixture_schemas_dir / "compatibility.json"
    )

    project = tmp_path / "projeto"
    apply_harness_scaffold(project, "meu-projeto")
    config_path = harness_dir(project) / "config.json"
    config = json.loads(config_path.read_text())
    config["schema_version"] = "0.9"  # N-1, dentro da janela
    config_path.write_text(json.dumps(config), encoding="utf-8")

    report = diagnose(project)
    assert report["schema_compatibility"]["status"] == "ok"


def test_doctor_reports_outdated_when_schema_version_older_than_n_minus_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture_schemas_dir = tmp_path / "fixture_schemas"
    fixture_schemas_dir.mkdir()
    _write_compatibility_fixture(fixture_schemas_dir, ["1.0", "0.9"])
    monkeypatch.setattr(
        schema_validation, "COMPATIBILITY_PATH", fixture_schemas_dir / "compatibility.json"
    )

    project = tmp_path / "projeto"
    apply_harness_scaffold(project, "meu-projeto")
    config_path = harness_dir(project) / "config.json"
    config = json.loads(config_path.read_text())
    config["schema_version"] = "0.8"  # N-2, fora da janela
    config_path.write_text(json.dumps(config), encoding="utf-8")

    report = diagnose(project)
    assert report["schema_compatibility"]["status"] == "outdated"
    assert "reason" in report["schema_compatibility"]


def test_compatibility_json_is_the_single_source_changing_it_changes_doctor_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture_schemas_dir = tmp_path / "fixture_schemas"
    fixture_schemas_dir.mkdir()
    compat_path = fixture_schemas_dir / "compatibility.json"
    monkeypatch.setattr(schema_validation, "COMPATIBILITY_PATH", compat_path)

    project = tmp_path / "projeto"
    apply_harness_scaffold(project, "meu-projeto")
    config_path = harness_dir(project) / "config.json"
    config = json.loads(config_path.read_text())
    config["schema_version"] = "0.9"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    _write_compatibility_fixture(fixture_schemas_dir, ["1.0"])  # 0.9 fora da janela
    assert diagnose(project)["schema_compatibility"]["status"] == "outdated"

    _write_compatibility_fixture(fixture_schemas_dir, ["1.0", "0.9"])  # agora dentro
    assert diagnose(project)["schema_compatibility"]["status"] == "ok"
