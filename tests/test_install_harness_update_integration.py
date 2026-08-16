"""Integração: install_harness.py CLI detecta .harness/ existente e aplica update seguro
(task 04). Roda o script via subprocess, como na prática."""

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


def _apply(target: Path, decisions: dict) -> dict:
    decisions_file = target.parent / f"decisions-{target.name}.json"
    decisions_file.write_text(json.dumps(decisions), encoding="utf-8")
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
    return applied


def _plan(target: Path) -> dict:
    result = _run(str(target), "--canonical", str(CANONICAL), "--json")
    assert result.returncode == 0, result.stderr
    return dict(json.loads(result.stdout))


def test_second_run_against_existing_harness_uses_update_path(tmp_path: Path) -> None:
    target = tmp_path / "projeto"
    _apply(target, {})  # instalação inicial (scaffold)

    plan = _plan(target)
    assert "harness_scaffold" not in plan
    assert "harness_update" in plan
    assert plan["harness_update"]["migrations"] == []


def test_pending_migration_listed_but_not_applied_without_confirmation(tmp_path: Path) -> None:
    target = tmp_path / "projeto"
    _apply(target, {})

    config_path = target / ".harness" / "config.json"
    config = json.loads(config_path.read_text())
    config["schema_version"] = "0.9"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    plan = _plan(target)
    assert len(plan["harness_update"]["migrations"]) == 1
    assert plan["harness_update"]["migrations"][0]["requires_confirmation"] is True

    applied = _apply(target, {})  # sem confirm_harness_migrations
    assert applied["harness_update"]["migrations_applied"] == 0
    assert json.loads(config_path.read_text())["schema_version"] == "0.9"


def test_migration_applied_when_confirmed_via_decisions_file(tmp_path: Path) -> None:
    target = tmp_path / "projeto"
    _apply(target, {})

    config_path = target / ".harness" / "config.json"
    config = json.loads(config_path.read_text())
    config["schema_version"] = "0.9"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    applied = _apply(target, {"confirm_harness_migrations": True})
    assert applied["harness_update"]["migrations_applied"] == 1
    assert applied["harness_update"]["backups"] == 1
    assert json.loads(config_path.read_text())["schema_version"] == "1.0"
