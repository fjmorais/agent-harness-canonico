from __future__ import annotations

from pathlib import Path

from scripts.harness_event_writer import write_event
from scripts.harness_usage import aggregate_usage


def _usage_event(
    *,
    sequence: int,
    writer_id: str,
    model_id: str,
    correlation_id: str | None,
    input_tokens: int,
    output_tokens: int,
) -> dict:
    return {
        "schema_version": "1.0",
        "event_id": f"evt_{writer_id}_{sequence}",
        "project_id": "project_01K2XYZ",
        "run_id": "run_01K2XYZ",
        "writer_id": writer_id,
        "source": "claude-code",
        "provider": "anthropic",
        "event_type": "usage.recorded",
        "occurred_at": "2026-08-16T10:00:00-03:00",
        "sequence": sequence,
        "parent_event_id": None,
        "correlation_id": correlation_id,
        "payload": {
            "model_id": model_id,
            "input": input_tokens,
            "output": output_tokens,
            "cache_read": 0,
            "cache_write": 0,
            "reasoning": 0,
        },
        "privacy": {"contains_prompt": False, "contains_pii": False},
    }


def test_two_different_models_get_separate_entries(tmp_path: Path) -> None:
    write_event(
        tmp_path,
        "main",
        _usage_event(
            sequence=0,
            writer_id="main",
            model_id="claude-sonnet-5",
            correlation_id="task_04",
            input_tokens=100,
            output_tokens=20,
        ),
    )
    write_event(
        tmp_path,
        "main",
        _usage_event(
            sequence=1,
            writer_id="main",
            model_id="claude-haiku-4-5",
            correlation_id="task_04",
            input_tokens=50,
            output_tokens=10,
        ),
    )

    usage = aggregate_usage(tmp_path)
    model_ids = {entry["model_id"] for entry in usage["usage_by_model"]}
    assert model_ids == {"claude-sonnet-5", "claude-haiku-4-5"}


def test_same_model_different_correlation_id_separated(tmp_path: Path) -> None:
    write_event(
        tmp_path,
        "main",
        _usage_event(
            sequence=0,
            writer_id="main",
            model_id="claude-sonnet-5",
            correlation_id="task_01",
            input_tokens=100,
            output_tokens=20,
        ),
    )
    write_event(
        tmp_path,
        "main",
        _usage_event(
            sequence=1,
            writer_id="main",
            model_id="claude-sonnet-5",
            correlation_id="task_02",
            input_tokens=200,
            output_tokens=40,
        ),
    )

    usage = aggregate_usage(tmp_path)
    entries = {(e["correlation_id"], e["model_id"]): e for e in usage["usage_by_model"]}
    assert entries[("task_01", "claude-sonnet-5")]["input"] == 100
    assert entries[("task_02", "claude-sonnet-5")]["input"] == 200


def test_tokens_summed_correctly_within_same_group(tmp_path: Path) -> None:
    write_event(
        tmp_path,
        "main",
        _usage_event(
            sequence=0,
            writer_id="main",
            model_id="claude-sonnet-5",
            correlation_id="task_04",
            input_tokens=100,
            output_tokens=20,
        ),
    )
    write_event(
        tmp_path,
        "sub_a",
        _usage_event(
            sequence=0,
            writer_id="sub_a",
            model_id="claude-sonnet-5",
            correlation_id="task_04",
            input_tokens=50,
            output_tokens=5,
        ),
    )

    usage = aggregate_usage(tmp_path)
    assert len(usage["usage_by_model"]) == 1
    entry = usage["usage_by_model"][0]
    assert entry["input"] == 150
    assert entry["output"] == 25


def test_usage_json_never_has_price_field(tmp_path: Path) -> None:
    write_event(
        tmp_path,
        "main",
        _usage_event(
            sequence=0,
            writer_id="main",
            model_id="claude-sonnet-5",
            correlation_id="task_04",
            input_tokens=100,
            output_tokens=20,
        ),
    )

    usage = aggregate_usage(tmp_path)
    assert "cost" not in usage
    assert "price" not in usage
    for entry in usage["usage_by_model"]:
        assert "cost" not in entry
        assert "price" not in entry
        assert set(entry.keys()) == {
            "model_id",
            "correlation_id",
            "input",
            "output",
            "cache_read",
            "cache_write",
            "reasoning",
        }
