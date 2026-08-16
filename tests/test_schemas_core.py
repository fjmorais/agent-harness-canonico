from __future__ import annotations

from copy import deepcopy

import pytest

from scripts.schema_validation import validate

VALID_EVENT = {
    "schema_version": "1.0",
    "event_id": "evt_001",
    "project_id": "project_01K2XYZ",
    "run_id": "run_01K2XYZ",
    "writer_id": "main",
    "source": "claude-code",
    "provider": "anthropic",
    "event_type": "tool.executed",
    "occurred_at": "2026-08-15T10:35:00-03:00",
    "sequence": 12,
    "parent_event_id": None,
    "correlation_id": "task_04",
    "payload": {"tool": "pytest", "exit_code": 0},
    "privacy": {"contains_prompt": False, "contains_pii": False},
}


def test_execution_event_valid() -> None:
    ok, errors = validate(VALID_EVENT, "execution-event")
    assert ok, errors


def test_execution_event_missing_field_is_invalid() -> None:
    payload = deepcopy(VALID_EVENT)
    del payload["writer_id"]
    ok, errors = validate(payload, "execution-event")
    assert not ok
    assert errors


def test_execution_event_wrong_type_is_invalid() -> None:
    payload = deepcopy(VALID_EVENT)
    payload["sequence"] = "twelve"
    ok, errors = validate(payload, "execution-event")
    assert not ok


VALID_RUN = {
    "schema_version": "1.0",
    "run_id": "run_01K2XYZ",
    "project_id": "project_01K2XYZ",
    "executor": "claude-code",
    "provider": "anthropic",
    "started_at": "2026-08-15T10:00:00-03:00",
    "ended_at": None,
    "status": "running",
}

VALID_TRANSITIONS = [
    "created",
    "queued",
    "running",
    "waiting_approval",
    "paused",
    "completed",
    "failed",
    "cancelled",
    "interrupted",
    "recovering",
]


@pytest.mark.parametrize("status", VALID_TRANSITIONS)
def test_run_valid_status(status: str) -> None:
    payload = deepcopy(VALID_RUN)
    payload["status"] = status
    ok, errors = validate(payload, "run")
    assert ok, errors


@pytest.mark.parametrize("status", ["done", "started", "", "RUNNING"])
def test_run_invalid_status(status: str) -> None:
    payload = deepcopy(VALID_RUN)
    payload["status"] = status
    ok, _errors = validate(payload, "run")
    assert not ok


VALID_USAGE = {
    "schema_version": "1.0",
    "run_id": "run_01K2XYZ",
    "usage_by_model": [
        {
            "model_id": "claude-sonnet-5",
            "correlation_id": "task_04",
            "input": 1000,
            "output": 200,
            "cache_read": 50,
            "cache_write": 10,
            "reasoning": 0,
        },
        {
            "model_id": "claude-haiku-4-5",
            "correlation_id": "task_04",
            "input": 300,
            "output": 40,
            "cache_read": 0,
            "cache_write": 0,
            "reasoning": 0,
        },
    ],
}


def test_usage_accepts_multiple_models() -> None:
    ok, errors = validate(VALID_USAGE, "usage")
    assert ok, errors
    assert len(VALID_USAGE["usage_by_model"]) == 2


VALID_PROJECT_STATE = {
    "schema_version": "1.0",
    "project_id": "project_01K2XYZ",
    "project_name": "Harness Control",
    "created_at": "2026-08-15T10:00:00-03:00",
}


def test_project_state_valid() -> None:
    ok, errors = validate(VALID_PROJECT_STATE, "project-state")
    assert ok, errors


VALID_WORKFLOW_STATE = {
    "schema_version": "1.0",
    "project_id": "project_01K2XYZ",
    "active_run_id": "run_01K2XYZ",
    "active_writers": ["main", "subagent_a1"],
    "updated_at": "2026-08-15T10:35:00-03:00",
}


def test_workflow_state_valid() -> None:
    ok, errors = validate(VALID_WORKFLOW_STATE, "workflow-state")
    assert ok, errors


@pytest.mark.parametrize(
    "schema_name,payload",
    [
        ("execution-event", VALID_EVENT),
        ("run", VALID_RUN),
        ("usage", VALID_USAGE),
        ("project-state", VALID_PROJECT_STATE),
        ("workflow-state", VALID_WORKFLOW_STATE),
    ],
)
def test_schema_version_required(schema_name: str, payload: dict) -> None:
    without_version = deepcopy(payload)
    del without_version["schema_version"]
    ok, _errors = validate(without_version, schema_name)
    assert not ok
