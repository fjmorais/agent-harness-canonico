"""Integração: scripts/harness_hook.py invocado como CLI real (stdin JSON), do jeito que o
Claude Code de fato dispara um hook — não só via chamada direta de função."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.harness_scaffold import apply_harness_scaffold, harness_dir

CANONICAL = Path(__file__).resolve().parent.parent
HOOK_SCRIPT = CANONICAL / "scripts" / "harness_hook.py"


def _run_hook(payload: dict) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(CANONICAL),
        env={"PYTHONPATH": str(CANONICAL)},
        timeout=30,
    )


def test_session_start_via_stdin_creates_run(tmp_path: Path) -> None:
    apply_harness_scaffold(tmp_path, "projeto-cli")
    config_path = harness_dir(tmp_path) / "config.json"
    config = json.loads(config_path.read_text())
    config["telemetry"]["enabled"] = True
    config_path.write_text(json.dumps(config), encoding="utf-8")

    result = _run_hook(
        {"hook_event_name": "SessionStart", "session_id": "sess_cli", "cwd": str(tmp_path)}
    )
    assert result.returncode == 0, result.stderr

    runs = list((harness_dir(tmp_path) / "runs").glob("*/*/run_sess_cli"))
    assert len(runs) == 1
    run = json.loads((runs[0] / "run.json").read_text())
    assert run["status"] == "running"


def test_hook_is_noop_and_exits_cleanly_without_harness(tmp_path: Path) -> None:
    result = _run_hook(
        {"hook_event_name": "SessionStart", "session_id": "sess_cli", "cwd": str(tmp_path)}
    )
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / ".harness").exists()
