"""Task 16 — assert_write_compatible() wireado nos writers reais (write_event,
apply_harness_update). Ver ressalva do revisor-codigo na task 13."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.harness_event_writer import write_event
from scripts.harness_scaffold import apply_harness_scaffold, apply_harness_update, harness_dir

CANONICAL = Path(__file__).resolve().parent.parent.parent
HOOK_SCRIPT = CANONICAL / "scripts" / "harness_hook.py"


def _event(schema_version: str = "1.0", sequence: int = 0) -> dict:
    return {
        "schema_version": schema_version,
        "event_id": "evt_1",
        "project_id": "project_01K2XYZ",
        "run_id": "run_01K2XYZ",
        "writer_id": "main",
        "source": "claude-code",
        "provider": "anthropic",
        "event_type": "tool.executed",
        "occurred_at": "2026-08-16T10:00:00-03:00",
        "sequence": sequence,
        "parent_event_id": None,
        "correlation_id": None,
        "payload": {"tool": "pytest", "exit_code": 0},
        "privacy": {"contains_prompt": False, "contains_pii": False},
    }


def test_write_event_rejects_newer_schema_version_than_pinned(tmp_path: Path) -> None:
    # execution-event.schema.json trava schema_version em const "1.0" (só existe uma versão
    # publicada hoje) — simula divergência rebaixando o PINNED do projeto em vez de subir o do
    # evento (que precisa continuar "1.0" pra passar na validação de schema básica).
    apply_harness_scaffold(tmp_path, "meu-projeto")
    config_path = harness_dir(tmp_path) / "config.json"
    config = json.loads(config_path.read_text())
    config["schema_version"] = "0.9"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    run_dir = harness_dir(tmp_path) / "runs" / "2026" / "08" / "run_x"
    run_dir.mkdir(parents=True)

    with pytest.raises(ValueError, match="rejeitada"):
        write_event(run_dir, "main", _event(schema_version="1.0"))

    assert not (run_dir / "events" / "main.jsonl").exists()  # nada foi gravado


def test_write_event_accepts_pinned_or_older_schema_version(tmp_path: Path) -> None:
    apply_harness_scaffold(tmp_path, "meu-projeto")
    run_dir = harness_dir(tmp_path) / "runs" / "2026" / "08" / "run_x"
    run_dir.mkdir(parents=True)

    write_event(run_dir, "main", _event(schema_version="1.0"))
    assert (run_dir / "events" / "main.jsonl").exists()


def test_write_event_without_real_harness_project_is_unaffected(tmp_path: Path) -> None:
    # run_dir "solto", sem .harness/config.json ancestral — guard desligado, comportamento
    # idêntico ao pré-task-16 (mantém os ~110 testes existentes passando, AC3).
    write_event(tmp_path, "main", _event(schema_version="1.0"))
    assert (tmp_path / "events" / "main.jsonl").exists()


def test_apply_harness_update_skips_incompatible_file_without_aborting_batch(
    tmp_path: Path,
) -> None:
    apply_harness_scaffold(tmp_path, "meu-projeto")
    config_path = harness_dir(tmp_path) / "config.json"
    config = json.loads(config_path.read_text())
    config["schema_version"] = "0.9"  # mais antigo que o que o código grava por default (1.0)
    config_path.write_text(json.dumps(config), encoding="utf-8")
    (harness_dir(tmp_path) / "state" / "current-workflow.json").unlink()  # força recriação

    result = apply_harness_update(tmp_path, "meu-projeto")

    assert "state/current-workflow.json" in result["skipped_incompatible"]
    assert not (harness_dir(tmp_path) / "state" / "current-workflow.json").exists()


def test_apply_harness_update_writes_compatible_file_normally(tmp_path: Path) -> None:
    apply_harness_scaffold(tmp_path, "meu-projeto")
    (harness_dir(tmp_path) / "state" / "current-workflow.json").unlink()

    result = apply_harness_update(tmp_path, "meu-projeto")

    assert result["skipped_incompatible"] == []
    assert (harness_dir(tmp_path) / "state" / "current-workflow.json").exists()


def test_hook_never_propagates_exception_on_schema_mismatch_via_stdin(tmp_path: Path) -> None:
    apply_harness_scaffold(tmp_path, "meu-projeto")
    config_path = harness_dir(tmp_path) / "config.json"
    config = json.loads(config_path.read_text())
    config["telemetry"]["enabled"] = True
    config_path.write_text(json.dumps(config), encoding="utf-8")

    session_payload = json.dumps(
        {"hook_event_name": "SessionStart", "session_id": "sess_1", "cwd": str(tmp_path)}
    )
    subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=session_payload,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(CANONICAL)},
        timeout=30,
    )

    # payload de tool call com schema_version implicitamente compatível (o hook sempre grava
    # "1.0"); simulamos incompatibilidade rebaixando o pinned do projeto após o SessionStart.
    config = json.loads(config_path.read_text())
    config["schema_version"] = "0.1"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    tool_payload = json.dumps(
        {
            "hook_event_name": "PostToolUse",
            "session_id": "sess_1",
            "cwd": str(tmp_path),
            "tool_name": "Bash",
            "tool_input": {},
            "tool_response": {"is_error": False},
        }
    )
    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=tool_payload,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(CANONICAL)},
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert "harness_hook:" in result.stderr  # erro logado, não silenciado nem propagado
