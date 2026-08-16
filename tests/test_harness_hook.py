from __future__ import annotations

import json
from pathlib import Path

from scripts.harness_event_writer import rebuild_timeline
from scripts.harness_hook import dispatch, find_run_dir
from scripts.harness_scaffold import apply_harness_scaffold, harness_dir


def _install_with_telemetry(tmp_path: Path) -> Path:
    apply_harness_scaffold(tmp_path, "meu-projeto")
    config_path = harness_dir(tmp_path) / "config.json"
    config = json.loads(config_path.read_text())
    config["telemetry"]["enabled"] = True
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return tmp_path


def test_session_start_creates_run_running(tmp_path: Path) -> None:
    target = _install_with_telemetry(tmp_path)
    dispatch(
        target, {"hook_event_name": "SessionStart", "session_id": "sess_1", "cwd": str(target)}
    )

    run_dir = find_run_dir(harness_dir(target), "sess_1")
    assert run_dir is not None
    run = json.loads((run_dir / "run.json").read_text())
    assert run["status"] == "running"
    assert run["ended_at"] is None


def test_session_end_closes_run_with_terminal_status(tmp_path: Path) -> None:
    target = _install_with_telemetry(tmp_path)
    dispatch(
        target, {"hook_event_name": "SessionStart", "session_id": "sess_1", "cwd": str(target)}
    )
    dispatch(target, {"hook_event_name": "SessionEnd", "session_id": "sess_1", "cwd": str(target)})

    run_dir = find_run_dir(harness_dir(target), "sess_1")
    assert run_dir is not None
    run = json.loads((run_dir / "run.json").read_text())
    assert run["status"] == "completed"
    assert run["ended_at"] is not None


def test_session_end_maps_error_reason_to_failed_status(tmp_path: Path) -> None:
    target = _install_with_telemetry(tmp_path)
    dispatch(
        target, {"hook_event_name": "SessionStart", "session_id": "sess_1", "cwd": str(target)}
    )
    dispatch(
        target,
        {
            "hook_event_name": "SessionEnd",
            "session_id": "sess_1",
            "cwd": str(target),
            "reason": "tool_execution_error",
        },
    )

    run_dir = find_run_dir(harness_dir(target), "sess_1")
    assert run_dir is not None
    run = json.loads((run_dir / "run.json").read_text())
    assert run["status"] == "failed"


def test_post_tool_use_writes_redacted_event(tmp_path: Path) -> None:
    target = _install_with_telemetry(tmp_path)
    dispatch(
        target, {"hook_event_name": "SessionStart", "session_id": "sess_1", "cwd": str(target)}
    )
    dispatch(
        target,
        {
            "hook_event_name": "PostToolUse",
            "session_id": "sess_1",
            "cwd": str(target),
            "tool_name": "Bash",
            "tool_input": {"command": "echo meu CPF é 123.456.789-00"},
            "tool_response": {"is_error": False},
        },
    )

    run_dir = find_run_dir(harness_dir(target), "sess_1")
    assert run_dir is not None
    events_file = run_dir / "events" / "main.jsonl"
    content = events_file.read_text()
    assert "123.456.789-00" not in content
    assert "***.***.***-**" in content

    timeline = rebuild_timeline(run_dir)
    assert any(e["event_type"] == "tool.executed" for e in timeline)


def test_subagent_stop_writes_to_distinct_writer_file(tmp_path: Path) -> None:
    target = _install_with_telemetry(tmp_path)
    dispatch(
        target, {"hook_event_name": "SessionStart", "session_id": "sess_1", "cwd": str(target)}
    )
    dispatch(
        target,
        {
            "hook_event_name": "PostToolUse",
            "session_id": "sess_1",
            "cwd": str(target),
            "tool_name": "Read",
            "tool_input": {},
            "tool_response": {"is_error": False},
        },
    )
    dispatch(
        target,
        {
            "hook_event_name": "SubagentStop",
            "session_id": "sess_1",
            "cwd": str(target),
            "agent_type": "revisor-codigo",
        },
    )

    run_dir = find_run_dir(harness_dir(target), "sess_1")
    assert run_dir is not None
    main_file = run_dir / "events" / "main.jsonl"
    subagent_file = run_dir / "events" / "subagent_revisor-codigo.jsonl"
    assert main_file.exists()
    assert subagent_file.exists()
    assert main_file != subagent_file


def test_correlation_id_is_explicit_none_when_undeterminable(tmp_path: Path) -> None:
    target = _install_with_telemetry(tmp_path)
    dispatch(
        target, {"hook_event_name": "SessionStart", "session_id": "sess_1", "cwd": str(target)}
    )
    dispatch(
        target,
        {
            "hook_event_name": "PostToolUse",
            "session_id": "sess_1",
            "cwd": str(target),
            "tool_name": "Bash",
            "tool_input": {},
            "tool_response": {"is_error": False},
        },
    )

    run_dir = find_run_dir(harness_dir(target), "sess_1")
    assert run_dir is not None
    timeline = rebuild_timeline(run_dir)
    assert len(timeline) == 1
    assert "correlation_id" in timeline[0]
    assert timeline[0]["correlation_id"] is None


def test_dispatch_is_noop_without_harness_installed(tmp_path: Path) -> None:
    # não roda apply_harness_scaffold — .harness/ não existe
    dispatch(
        tmp_path, {"hook_event_name": "SessionStart", "session_id": "sess_1", "cwd": str(tmp_path)}
    )
    assert not (tmp_path / ".harness").exists()


def test_dispatch_is_noop_when_telemetry_disabled(tmp_path: Path) -> None:
    apply_harness_scaffold(tmp_path, "meu-projeto")  # telemetry.enabled=False por padrão
    dispatch(
        tmp_path, {"hook_event_name": "SessionStart", "session_id": "sess_1", "cwd": str(tmp_path)}
    )
    assert find_run_dir(harness_dir(tmp_path), "sess_1") is None
