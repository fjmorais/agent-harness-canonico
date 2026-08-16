from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.harness_scaffold import (
    CURSOR_HOOKS_REL,
    generate_cursor_hooks_config,
    write_cursor_hooks_config,
)

CANONICAL = Path(__file__).resolve().parent.parent
INSTALL_SCRIPT = (
    CANONICAL / ".claude" / "skills" / "install-harness" / "scripts" / "install_harness.py"
)


def test_generate_cursor_hooks_config_references_same_script_as_claude_code() -> None:
    config = generate_cursor_hooks_config()
    assert config["version"] == 1
    for event in ("sessionStart", "sessionEnd", "preToolUse", "postToolUse", "subagentStop"):
        commands = [h["command"] for h in config["hooks"][event]]
        assert any("scripts/harness_hook.py" in c for c in commands)


def test_write_cursor_hooks_config_writes_valid_json(tmp_path: Path) -> None:
    path = write_cursor_hooks_config(tmp_path)
    assert path == tmp_path / CURSOR_HOOKS_REL
    assert json.loads(path.read_text())["version"] == 1


def _parse_json_documents(text: str) -> list[dict]:
    decoder = json.JSONDecoder()
    documents = []
    idx = 0
    text = text.strip()
    while idx < len(text):
        obj, end = decoder.raw_decode(text, idx)
        documents.append(obj)
        idx = end
        while idx < len(text) and text[idx].isspace():
            idx += 1
    return documents


def test_install_harness_generates_cursor_hooks_json_and_manifest_capability(
    tmp_path: Path,
) -> None:
    target = tmp_path / "projeto-novo"
    decisions_file = tmp_path / "decisions.json"
    decisions_file.write_text("{}", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(INSTALL_SCRIPT),
            str(target),
            "--canonical",
            str(CANONICAL),
            "--json",
            "--decisions-file",
            str(decisions_file),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    _plan, applied = _parse_json_documents(result.stdout)
    assert applied.get("cursor_hooks") == "written"

    hooks_path = target / ".cursor" / "hooks.json"
    assert hooks_path.exists()
    hooks_config = json.loads(hooks_path.read_text())
    assert "sessionStart" in hooks_config["hooks"]

    # script scripts/harness_hook.py não foi propagado pro alvo (target não tem scripts/) —
    # honestamente "unavailable", nunca "true" incondicional (bloqueante do revisor-codigo).
    manifest = json.loads((target / ".claude" / "harness-manifest.json").read_text())
    assert manifest["capabilities"]["telemetry"]["cursor"] == "unavailable"


def test_manifest_reports_cursor_true_only_when_script_is_actually_reachable(
    tmp_path: Path,
) -> None:
    target = tmp_path / "projeto-com-script"
    decisions_file = tmp_path / "decisions.json"
    decisions_file.write_text("{}", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(INSTALL_SCRIPT),
            str(target),
            "--canonical",
            str(CANONICAL),
            "--json",
            "--decisions-file",
            str(decisions_file),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr

    # simula propagação futura do script pro alvo (hoje não acontece — ver Notes da task 11)
    (target / "scripts").mkdir(parents=True, exist_ok=True)
    (target / "scripts" / "harness_hook.py").write_text("# placeholder\n", encoding="utf-8")

    from scripts.harness_scaffold import harness_dir

    assert harness_dir(target).exists()  # confirma que o scaffold já rodou nesta pasta

    sys.path.insert(0, str(CANONICAL / ".claude" / "skills" / "install-harness" / "scripts"))
    import install_harness

    install_harness._enable_cursor_telemetry_capability(target)
    manifest = json.loads((target / ".claude" / "harness-manifest.json").read_text())
    assert manifest["capabilities"]["telemetry"]["cursor"] is True
