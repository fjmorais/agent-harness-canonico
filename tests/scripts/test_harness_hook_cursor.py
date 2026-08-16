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


def test_cursor_session_start_creates_run_same_format_as_claude_code(tmp_path: Path) -> None:
    target = _install_with_telemetry(tmp_path)
    dispatch(
        target,
        {
            "hook_event_name": "sessionStart",
            "session_id": "cursor_sess_1",
            "workspace_roots": [str(target)],
            "composer_mode": "agent",
        },
    )

    run_dir = find_run_dir(harness_dir(target), "cursor_sess_1")
    assert run_dir is not None
    run = json.loads((run_dir / "run.json").read_text())
    assert run["status"] == "running"
    assert run["executor"] == "cursor"


def test_cursor_post_tool_use_normalizes_json_stringified_tool_output(tmp_path: Path) -> None:
    target = _install_with_telemetry(tmp_path)
    dispatch(
        target,
        {"hook_event_name": "sessionStart", "session_id": "cursor_sess_1", "cwd": str(target)},
    )
    dispatch(
        target,
        {
            "hook_event_name": "postToolUse",
            "session_id": "cursor_sess_1",
            "cwd": str(target),
            "tool_name": "Shell",
            "tool_input": {"command": "ls"},
            "tool_output": json.dumps({"result": "ok", "error": False}),
            "duration": 42,
        },
    )

    run_dir = find_run_dir(harness_dir(target), "cursor_sess_1")
    assert run_dir is not None
    timeline = rebuild_timeline(run_dir)
    assert len(timeline) == 1
    assert timeline[0]["event_type"] == "tool.executed"
    assert timeline[0]["payload"]["exit_code"] == 0


def test_cursor_post_tool_use_error_output_maps_to_nonzero_exit_code(tmp_path: Path) -> None:
    target = _install_with_telemetry(tmp_path)
    dispatch(
        target,
        {"hook_event_name": "sessionStart", "session_id": "cursor_sess_1", "cwd": str(target)},
    )
    dispatch(
        target,
        {
            "hook_event_name": "postToolUse",
            "session_id": "cursor_sess_1",
            "cwd": str(target),
            "tool_name": "Shell",
            "tool_input": {"command": "false"},
            "tool_output": json.dumps({"error": "command failed"}),
        },
    )

    run_dir = find_run_dir(harness_dir(target), "cursor_sess_1")
    assert run_dir is not None
    timeline = rebuild_timeline(run_dir)
    assert timeline[0]["payload"]["exit_code"] == 1


def test_cursor_subagent_stop_writes_to_distinct_writer_file(tmp_path: Path) -> None:
    target = _install_with_telemetry(tmp_path)
    dispatch(
        target,
        {"hook_event_name": "sessionStart", "session_id": "cursor_sess_1", "cwd": str(target)},
    )
    dispatch(
        target,
        {
            "hook_event_name": "subagentStop",
            "session_id": "cursor_sess_1",
            "cwd": str(target),
            "subagent_id": "sub_abc123",
            "subagent_type": "explore",
            "parent_conversation_id": "cursor_sess_1",
        },
    )

    run_dir = find_run_dir(harness_dir(target), "cursor_sess_1")
    assert run_dir is not None
    assert (run_dir / "events" / "subagent_explore.jsonl").exists()


def test_cursor_session_start_resolves_cwd_from_workspace_roots_without_cwd_field(
    tmp_path: Path,
) -> None:
    from scripts.harness_hook import _normalize_cursor_payload

    normalized = _normalize_cursor_payload(
        {"hook_event_name": "sessionStart", "session_id": "s1", "workspace_roots": ["/a/b"]}
    )
    assert normalized["cwd"] == "/a/b"
    assert normalized["hook_event_name"] == "SessionStart"
