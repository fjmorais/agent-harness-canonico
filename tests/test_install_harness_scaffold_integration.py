"""Integração: install_harness.py CLI cria .harness/ para um projeto novo (task 03,
critérios 1 e 5). Roda o script via subprocess, como ele é usado na prática (CLI standalone)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

CANONICAL = Path(__file__).resolve().parent.parent
INSTALL_SCRIPT = (
    CANONICAL / ".claude" / "skills" / "install-harness" / "scripts" / "install_harness.py"
)


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(INSTALL_SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=30,
    )


def _parse_json_documents(text: str) -> list[dict]:
    """--json com --decisions-file imprime dois documentos JSON em sequência (plano + applied)."""
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


def test_json_plan_lists_harness_scaffold_operations_before_writing(tmp_path: Path) -> None:
    target = tmp_path / "projeto-novo"
    result = _run(str(target), "--canonical", str(CANONICAL), "--json")
    assert result.returncode == 0, result.stderr

    plan = json.loads(result.stdout)
    assert "harness_scaffold" in plan
    paths = {op["path"] for op in plan["harness_scaffold"]}
    assert "config.json" in paths
    assert "state/project.json" in paths

    # nada foi escrito ainda — só o plano foi exibido
    assert not (target / ".harness").exists()


def test_json_apply_creates_full_harness_structure(tmp_path: Path) -> None:
    target = tmp_path / "projeto-novo"
    decisions_file = tmp_path / "decisions.json"
    decisions_file.write_text("{}", encoding="utf-8")

    result = _run(
        str(target),
        "--canonical",
        str(CANONICAL),
        "--json",
        "--decisions-file",
        str(decisions_file),
    )
    assert result.returncode == 0, result.stderr

    _plan, applied = _parse_json_documents(result.stdout)
    assert "harness_scaffold" in applied

    harness = target / ".harness"
    assert (harness / "config.json").exists()
    assert (harness / "state" / "project.json").exists()
    assert (harness / "runs").is_dir()
    assert (harness / ".gitignore").exists()

    manifest = json.loads((target / ".claude" / "harness-manifest.json").read_text())
    assert manifest["manifest_schema_version"] == "2.0"
    # telemetry.cursor: true é gravado pelo adapter Cursor (task 11) — .cursor/hooks.json
    # sempre é gerado junto com o scaffold do .harness/, claude_code fica de fora até o
    # dogfooding real de cada projeto habilitar (config.json.telemetry.enabled).
    assert manifest["capabilities"]["telemetry"] == {"cursor": True}
    assert (target / ".cursor" / "hooks.json").exists()
