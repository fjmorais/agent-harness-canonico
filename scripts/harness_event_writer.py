"""Escritor de evento concorrente + reconstrução de timeline por run (task 06).

Cada escritor (agente principal, cada subagente) grava só no seu próprio arquivo dentro do
run — nunca há dois processos tocando o mesmo arquivo, eliminando condição de corrida sem
precisar de lock. Ver docs/adr/001-observabilidade-harness-control.md, Opção E.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from scripts.schema_validation import assert_write_compatible, validate

EVENTS_SUBDIR = "events"
HARNESS_DIRNAME = ".harness"  # duplica scripts.harness_scaffold.HARNESS_DIRNAME (evita import
# circular: harness_scaffold importa schema_validation, não harness_event_writer).


def _events_dir(run_dir: Path) -> Path:
    return run_dir / EVENTS_SUBDIR


def _find_pinned_schema_version(run_dir: Path) -> str | None:
    """Sobe a árvore a partir de `run_dir` procurando `.harness/config.json`. Retorna `None`
    (não `"1.0"` nem qualquer default) quando `run_dir` não está dentro de um projeto real com
    `.harness/` — nesse caso o guard de compatibilidade fica desligado, não fabrica um pinned
    inexistente (mantém os testes que chamam `write_event` com um `run_dir` solto, ex.:
    `tmp_path` direto, funcionando sem mudança de comportamento — task 16, AC3)."""
    for ancestor in (run_dir, *run_dir.parents):
        if ancestor.name == HARNESS_DIRNAME:
            config_path = ancestor / "config.json"
            if not config_path.exists():
                return None
            config = json.loads(config_path.read_text())
            version = config.get("schema_version")
            return str(version) if version is not None else None
    return None


def write_event(run_dir: Path, writer_id: str, event: dict[str, object]) -> Path:
    """Valida `event` contra execution-event.schema.json e faz append em
    `run_dir/events/<writer_id>.jsonl`. Levanta ValueError se o evento for inválido. Nunca
    trunca/reescreve o arquivo — só append.

    Se `run_dir` estiver dentro de um projeto com `.harness/config.json` (task 16), rejeita
    também um evento cujo `schema_version` seja mais novo que a versão pinned do projeto —
    nunca grava um payload que o projeto ainda não sabe interpretar."""
    ok, errors = validate(event, "execution-event")
    if not ok:
        raise ValueError(f"evento inválido: {errors}")

    pinned_version = _find_pinned_schema_version(run_dir)
    if pinned_version is not None:
        assert_write_compatible(
            pinned_version=pinned_version,
            payload_version=str(event.get("schema_version", pinned_version)),
        )

    events_dir = _events_dir(run_dir)
    events_dir.mkdir(parents=True, exist_ok=True)
    path = events_dir / f"{writer_id}.jsonl"
    line = json.dumps(event, ensure_ascii=False)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    return path


def _sort_key(event: dict[str, object]) -> tuple[datetime, int, str]:
    # normaliza para instante comparável — comparar string crua quebraria silenciosamente se
    # escritores diferentes usassem offsets de timezone diferentes (ex.: UTC vs. -03:00).
    occurred_at = datetime.fromisoformat(str(event.get("occurred_at", "1970-01-01T00:00:00+00:00")))
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
