"""Escritor de evento concorrente + reconstrução de timeline por run (task 06).

Cada escritor (agente principal, cada subagente) grava só no seu próprio arquivo dentro do
run — nunca há dois processos tocando o mesmo arquivo, eliminando condição de corrida sem
precisar de lock. Ver docs/adr/001-observabilidade-harness-control.md, Opção E.
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.schema_validation import validate

EVENTS_SUBDIR = "events"


def _events_dir(run_dir: Path) -> Path:
    return run_dir / EVENTS_SUBDIR


def write_event(run_dir: Path, writer_id: str, event: dict[str, object]) -> Path:
    """Valida `event` contra execution-event.schema.json e faz append em
    `run_dir/events/<writer_id>.jsonl`. Levanta ValueError se o evento for inválido. Nunca
    trunca/reescreve o arquivo — só append."""
    ok, errors = validate(event, "execution-event")
    if not ok:
        raise ValueError(f"evento inválido: {errors}")

    events_dir = _events_dir(run_dir)
    events_dir.mkdir(parents=True, exist_ok=True)
    path = events_dir / f"{writer_id}.jsonl"
    line = json.dumps(event, ensure_ascii=False)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    return path


def _sort_key(event: dict[str, object]) -> tuple[str, int, str]:
    occurred_at = str(event.get("occurred_at", ""))
    sequence_raw = event.get("sequence", 0)
    sequence = int(sequence_raw) if isinstance(sequence_raw, (int, str)) else 0
    writer_id = str(event.get("writer_id", ""))
    return (occurred_at, sequence, writer_id)


def rebuild_timeline(run_dir: Path) -> list[dict[str, object]]:
    """Lê todos os `events/*.jsonl` de um run e retorna a lista de eventos mesclada, ordenada
    por (occurred_at, sequence, writer_id). Função pura de leitura — idempotente por natureza,
    não consome nem apaga nada."""
    events_dir = _events_dir(run_dir)
    if not events_dir.exists():
        return []

    events: list[dict[str, object]] = []
    for writer_file in sorted(events_dir.glob("*.jsonl")):
        for line in writer_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            events.append(json.loads(line))

    events.sort(key=_sort_key)
    return events
