"""Agregação de `usage.json` por modelo e correlação (task 08).

Consome sempre a timeline reconstruída (`rebuild_timeline`, task 06) — nunca lê arquivos de
escritor diretamente, para não duplicar a lógica de mesclagem/ordenação. Eventos de uso têm
`event_type == "usage.recorded"` e carregam tokens brutos no `payload` — nunca custo em `$`
(ver docs/adr/001-observabilidade-harness-control.md, Opção G).
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.harness_event_writer import rebuild_timeline
from scripts.schema_validation import validate

USAGE_EVENT_TYPE = "usage.recorded"
_TOKEN_FIELDS = ("input", "output", "cache_read", "cache_write", "reasoning")


def aggregate_usage(run_dir: Path) -> dict[str, object]:
    """Agrupa eventos `usage.recorded` da timeline do run por (correlation_id, model_id) e
    retorna o payload de `usage.json`, já validado contra usage.schema.json."""
    timeline = rebuild_timeline(run_dir)

    totals: dict[tuple[object, str], dict[str, int]] = {}
    for event in timeline:
        if event.get("event_type") != USAGE_EVENT_TYPE:
            continue
        payload = event.get("payload")
        if not isinstance(payload, dict):
            continue
        model_id = str(payload.get("model_id", "unknown"))
        correlation_id = event.get("correlation_id")
        key = (correlation_id, model_id)
        bucket = totals.setdefault(key, dict.fromkeys(_TOKEN_FIELDS, 0))
        for field in _TOKEN_FIELDS:
            bucket[field] += int(payload.get(field, 0) or 0)

    usage_by_model = [
        {
            "model_id": model_id,
            "correlation_id": correlation_id,
            **bucket,
        }
        for (correlation_id, model_id), bucket in sorted(
            totals.items(), key=lambda kv: (str(kv[0][0]), kv[0][1])
        )
    ]

    run_id = _infer_run_id(run_dir, timeline)
    usage: dict[str, object] = {
        "schema_version": "1.0",
        "run_id": run_id,
        "usage_by_model": usage_by_model or _empty_bucket(run_id),
    }
    ok, errors = validate(usage, "usage")
    if not ok:
        raise ValueError(f"usage.json inválido: {errors}")
    return usage


def _empty_bucket(run_id: str) -> list[dict[str, object]]:
    # usage.schema.json exige usage_by_model com pelo menos 1 item — run sem nenhum evento de
    # uso ainda registra uma entrada zerada em vez de violar o schema.
    return [
        {
            "model_id": "none",
            "correlation_id": None,
            **dict.fromkeys(_TOKEN_FIELDS, 0),
        }
    ]


def _infer_run_id(run_dir: Path, timeline: list[dict[str, object]]) -> str:
    run_json_path = run_dir / "run.json"
    if run_json_path.exists():
        return str(json.loads(run_json_path.read_text())["run_id"])
    if timeline:
        return str(timeline[0].get("run_id", run_dir.name))
    return run_dir.name


def write_usage(run_dir: Path) -> Path:
    usage = aggregate_usage(run_dir)
    path = run_dir / "usage.json"
    path.write_text(json.dumps(usage, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
