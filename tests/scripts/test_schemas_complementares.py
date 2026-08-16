from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from scripts.schema_validation import supported_versions, validate

METRICS_ENTREGAS_PATH = Path(__file__).resolve().parent.parent.parent / "metrics" / "entregas.jsonl"

VALID_MANIFEST = {
    "manifest_schema_version": "2.0",
    "harness_version": "0.9.0",
    "canonical_path": "/home/fabiano/agent-harness-canonico",
    "installed_at": "2026-08-15",
    "mode": "ATUALIZACAO",
    "capabilities": {
        "workflow": True,
        "dev_loop": True,
        "delivery_metrics": True,
        "telemetry": {"claude_code": True, "cursor": "unavailable"},
    },
    "artefacts": {},
}


def test_manifest_accepts_per_executor_telemetry() -> None:
    ok, errors = validate(VALID_MANIFEST, "harness-manifest")
    assert ok, errors
    telemetry = VALID_MANIFEST["capabilities"]["telemetry"]
    assert telemetry["claude_code"] is True
    assert telemetry["cursor"] == "unavailable"


def test_manifest_rejects_global_boolean_telemetry_shape() -> None:
    payload = deepcopy(VALID_MANIFEST)
    payload["capabilities"]["telemetry"] = "not-an-object"
    ok, _errors = validate(payload, "harness-manifest")
    assert not ok


VALID_CONFIG = {
    "schema_version": "1.0",
    "project_id": "project_01K2XYZ",
    "project_name": "Meu Projeto",
    "created_at": "2026-08-15T10:00:00-03:00",
    "telemetry": {
        "enabled": True,
        "capture_prompts": False,
        "capture_tool_details": False,
    },
    "retention": {"days": 365},
    "storage": {"operational_logs": "local", "aggregated_metrics": "git"},
}


def test_harness_config_valid() -> None:
    ok, errors = validate(VALID_CONFIG, "harness-config")
    assert ok, errors


def test_harness_config_retention_days_must_be_positive_int() -> None:
    payload = deepcopy(VALID_CONFIG)
    payload["retention"] = {"days": 0}
    ok, _errors = validate(payload, "harness-config")
    assert not ok


def test_harness_config_capture_flags_must_be_bool() -> None:
    payload = deepcopy(VALID_CONFIG)
    payload["telemetry"]["capture_prompts"] = "no"
    ok, _errors = validate(payload, "harness-config")
    assert not ok


VALID_RUN_RESULT = {
    "schema_version": "1.0",
    "run_id": "run_01K2XYZ",
    "exit_code": 0,
    "tasks": ["task_04"],
    "gate": "verde",
    "review": "aprovado",
    "human_interventions": 0,
    "error_summary": None,
}


def test_run_result_valid() -> None:
    ok, errors = validate(VALID_RUN_RESULT, "run-result")
    assert ok, errors


VALID_DELIVERY_RECORD = {
    "schema_version": "1.0",
    "project_id": "project_01K2XYZ",
    "run_id": "run_01K2XYZ",
    "issue": 1,
    "titulo": "esqueleto andante",
    "data": "2026-06-27",
    "criterios_aceite": {"total": 3, "atendidos": 3},
    "gate": {"resultado": "verde", "tentativas_ate_verde": 1},
    "revisor": {"veredito": "aprovado", "bloqueantes": 0, "ressalvas": 0},
    "intervencoes_humanas": 0,
    "commit": "abc1234",
}


def test_delivery_record_valid() -> None:
    ok, errors = validate(VALID_DELIVERY_RECORD, "delivery-record")
    assert ok, errors


def test_delivery_record_maps_existing_entregas_jsonl_line() -> None:
    if not METRICS_ENTREGAS_PATH.exists():
        payload = deepcopy(VALID_DELIVERY_RECORD)
    else:
        first_line = METRICS_ENTREGAS_PATH.read_text().splitlines()[0]
        entrega = json.loads(first_line)
        payload = {
            "schema_version": "1.0",
            "project_id": "project_01K2XYZ",
            "run_id": None,
            **entrega,
        }
    ok, errors = validate(payload, "delivery-record")
    assert ok, errors


def test_compatibility_supported_versions_execution_event() -> None:
    versions = supported_versions("execution-event")
    assert versions == ["1.0"]


def test_compatibility_supported_versions_harness_manifest() -> None:
    versions = supported_versions("harness-manifest")
    assert versions == ["2.0"]
