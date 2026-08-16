"""Adapter de hooks do Claude Code — SessionStart/SessionEnd/PreToolUse/PostToolUse/
SubagentStop escrevendo em `.harness/` (task 07).

Executado como script standalone: lê o payload do hook via stdin (JSON), despacha para o
handler certo. No-op silencioso (exit 0) se `.harness/` não estiver instalado ou telemetria
estiver desligada — nunca quebra a sessão do usuário por causa de telemetria.

Limitação conhecida e documentada (não inventar valor): `correlation_id` não é derivável com
confiança a partir do payload de hook disponível hoje — sempre gravado como `None` explícito
até um mecanismo de correlação mais forte existir (ex.: variável de ambiente setada pelos
comandos/skills do harness).
"""

from __future__ import annotations

import json
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

from scripts.harness_deliveries import sync_deliveries
from scripts.harness_event_writer import rebuild_timeline, write_event
from scripts.harness_redact import redact
from scripts.harness_scaffold import harness_dir, is_harness_installed
from scripts.schema_validation import validate

EXECUTOR = "claude-code"
PROVIDER = "anthropic"
MAIN_WRITER_ID = "main"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _read_config(base: Path) -> dict[str, object]:
    data: dict[str, object] = json.loads((base / "config.json").read_text())
    return data


def telemetry_enabled(target: Path) -> bool:
    if not is_harness_installed(target):
        return False
    config = _read_config(harness_dir(target))
    telemetry = config.get("telemetry")
    return bool(isinstance(telemetry, dict) and telemetry.get("enabled"))


def _project_id(base: Path) -> str:
    project_state = json.loads((base / "state" / "project.json").read_text())
    return str(project_state["project_id"])


def find_run_dir(base: Path, session_id: str) -> Path | None:
    """Procura um run já criado para `session_id` (não recalcula a partir da data atual —
    evita mismatch se um evento chegar depois da virada do dia/mês)."""
    runs_dir = base / "runs"
    if not runs_dir.exists():
        return None
    matches = list(runs_dir.glob(f"*/*/run_{session_id}"))
    return matches[0] if matches else None


def _new_run_dir(base: Path, session_id: str) -> Path:
    today = datetime.now(UTC)
    return base / "runs" / f"{today.year:04d}" / f"{today.month:02d}" / f"run_{session_id}"


def _write_run_json(run_dir: Path, run: dict[str, object]) -> None:
    ok, errors = validate(run, "run")
    if not ok:
        raise ValueError(f"run.json inválido: {errors}")
    (run_dir / "run.json").write_text(
        json.dumps(run, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def handle_session_start(target: Path, session_id: str) -> Path:
    base = harness_dir(target)
    run_dir = _new_run_dir(base, session_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    run: dict[str, object] = {
        "schema_version": "1.0",
        "run_id": session_id,
        "project_id": _project_id(base),
        "executor": EXECUTOR,
        "provider": PROVIDER,
        "started_at": _now(),
        "ended_at": None,
        "status": "running",
    }
    _write_run_json(run_dir, run)
    return run_dir


def _terminal_status_from_reason(reason: object) -> str:
    """Best-effort: o payload de SessionEnd do Claude Code traz um campo `reason` sem enum
    documentado com confiança — mapeamento conservador, `completed` é o default seguro."""
    reason_str = str(reason or "").lower()
    if "error" in reason_str or "fail" in reason_str:
        return "failed"
    if "cancel" in reason_str:
        return "cancelled"
    return "completed"


def handle_session_end(
    target: Path, session_id: str, hook_payload: dict[str, object] | None = None
) -> Path | None:
    base = harness_dir(target)
    run_dir = find_run_dir(base, session_id)
    if run_dir is None:
        return None

    run = json.loads((run_dir / "run.json").read_text())
    run["ended_at"] = _now()
    run["status"] = _terminal_status_from_reason((hook_payload or {}).get("reason"))
    _write_run_json(run_dir, run)

    timeline = rebuild_timeline(run_dir)
    _update_runs_index(base, session_id, run, len(timeline))
    sync_deliveries(target)  # entregas finalizadas desde o início da sessão viram delivery-record
    return run_dir


def _update_runs_index(base: Path, run_id: str, run: dict[str, object], event_count: int) -> None:
    index_path = base / "indexes" / "runs.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index: dict[str, object] = {}
    if index_path.exists():
        index = json.loads(index_path.read_text())
    index[run_id] = {
        "status": run["status"],
        "started_at": run["started_at"],
        "ended_at": run["ended_at"],
        "event_count": event_count,
    }
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _next_sequence(run_dir: Path, writer_id: str) -> int:
    path = run_dir / "events" / f"{writer_id}.jsonl"
    if not path.exists():
        return 0
    return len(path.read_text().splitlines())


def _build_event(
    *,
    run_dir: Path,
    project_id: str,
    session_id: str,
    writer_id: str,
    event_type: str,
    payload: dict[str, object],
) -> dict[str, object]:
    sequence = _next_sequence(run_dir, writer_id)
    raw_event: dict[str, object] = {
        "schema_version": "1.0",
        "event_id": f"evt_{session_id}_{writer_id}_{sequence}_{uuid.uuid4().hex[:8]}",
        "project_id": project_id,
        "run_id": session_id,
        "writer_id": writer_id,
        "source": EXECUTOR,
        "provider": PROVIDER,
        "event_type": event_type,
        "occurred_at": _now(),
        "sequence": sequence,
        "parent_event_id": None,
        # correlation_id: não inventar — sempre None até existir mecanismo de correlação forte.
        "correlation_id": None,
        "payload": payload,
        "privacy": {"contains_prompt": False, "contains_pii": False},
    }
    redacted_payload = redact({"payload": raw_event["payload"]})["payload"]
    contains_pii = redacted_payload != raw_event["payload"]
    raw_event["payload"] = redacted_payload
    raw_event["privacy"] = {"contains_prompt": False, "contains_pii": contains_pii}
    return raw_event


def handle_tool_use(
    target: Path, session_id: str, hook_event: str, hook_payload: dict[str, object]
) -> Path | None:
    if hook_event != "PostToolUse":
        return None  # MVP: só emitimos evento com resultado conhecido (pós tool call)

    base = harness_dir(target)
    run_dir = find_run_dir(base, session_id)
    if run_dir is None:
        return None

    tool_response = hook_payload.get("tool_response")
    exit_code = None
    if isinstance(tool_response, dict):
        exit_code = 1 if tool_response.get("is_error") else 0

    event = _build_event(
        run_dir=run_dir,
        project_id=_project_id(base),
        session_id=session_id,
        writer_id=MAIN_WRITER_ID,
        event_type="tool.executed",
        payload={
            "tool": hook_payload.get("tool_name"),
            "tool_input": hook_payload.get("tool_input"),
            "exit_code": exit_code,
        },
    )
    write_event(run_dir, MAIN_WRITER_ID, event)
    return run_dir


def handle_subagent_stop(
    target: Path, session_id: str, hook_payload: dict[str, object]
) -> Path | None:
    base = harness_dir(target)
    run_dir = find_run_dir(base, session_id)
    if run_dir is None:
        return None

    writer_id = "subagent_" + str(
        hook_payload.get("agent_type") or hook_payload.get("subagent_id") or "unknown"
    )
    event = _build_event(
        run_dir=run_dir,
        project_id=_project_id(base),
        session_id=session_id,
        writer_id=writer_id,
        event_type="subagent.completed",
        payload={"agent_type": hook_payload.get("agent_type")},
    )
    write_event(run_dir, writer_id, event)
    return run_dir


def dispatch(target: Path, hook_payload: dict[str, object]) -> None:
    if not telemetry_enabled(target):
        return
    hook_event = hook_payload.get("hook_event_name")
    session_id = str(hook_payload.get("session_id", "unknown"))

    if hook_event == "SessionStart":
        handle_session_start(target, session_id)
    elif hook_event == "SessionEnd":
        handle_session_end(target, session_id, hook_payload)
    elif hook_event in ("PreToolUse", "PostToolUse"):
        handle_tool_use(target, session_id, str(hook_event), hook_payload)
    elif hook_event == "SubagentStop":
        handle_subagent_stop(target, session_id, hook_payload)


def main() -> None:
    """Nunca deixa telemetria quebrar a sessão do usuário — qualquer falha (payload malformado,
    .harness/ corrompido, etc.) é logada em stderr e engolida; o hook sempre sai limpo."""
    try:
        raw = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"harness_hook: payload JSON inválido, ignorando: {exc}", file=sys.stderr)
        return
    if not isinstance(raw, dict):
        print("harness_hook: payload não é um objeto JSON, ignorando", file=sys.stderr)
        return

    hook_payload: dict[str, object] = raw
    cwd = Path(str(hook_payload.get("cwd", "."))).resolve()
    try:
        dispatch(cwd, hook_payload)
    except Exception as exc:  # noqa: BLE001 — barreira intencional, nunca propaga pro Claude Code
        print(f"harness_hook: erro ao processar hook (ignorado): {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
