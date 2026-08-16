"""Adapter `deliveries/` — deriva `.harness/deliveries/deliveries.jsonl` de
`metrics/entregas.jsonl` (task 09).

`metrics/entregas.jsonl` continua sendo a fonte de verdade para `/scorecard` — este adapter só
produz uma view adicional em formato `delivery-record.schema.json` para consumo externo. Nunca
escreve em `metrics/entregas.jsonl`, só lê. Ver docs/adr/001-observabilidade-harness-control.md.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from scripts.harness_scaffold import harness_dir
from scripts.schema_validation import validate

# "pendente" é um estado de trânsito real e recorrente: o harness-build grava esse placeholder
# antes do revisor-codigo rodar (ver .claude/agents/workflow/harness-build.md). Não é erro —
# é uma entrega ainda não finalizada, que o adapter deve esperar, não travar em cima dela.
_PENDING_VERDICTS = {"pendente"}


def sync_deliveries(target: Path) -> int:
    """Traduz linhas novas e finalizadas de `metrics/entregas.jsonl` para
    `.harness/deliveries/deliveries.jsonl`. Idempotente: linhas já sincronizadas (por `issue`)
    nunca são duplicadas. Linhas com veredito ainda `pendente` são adiadas (não sincronizadas,
    não descartadas — reconsideradas na próxima chamada). Linha genuinamente inválida é pulada e
    logada em stderr — nunca derruba o batch inteiro. Retorna quantas linhas novas foram
    gravadas."""
    entregas_path = target / "metrics" / "entregas.jsonl"
    if not entregas_path.exists():
        print(
            f"harness_deliveries: {entregas_path} não existe, nada a sincronizar", file=sys.stderr
        )
        return 0

    base = harness_dir(target)
    project_state_path = base / "state" / "project.json"
    if not project_state_path.exists():
        print("harness_deliveries: .harness/ não instalado, nada a sincronizar", file=sys.stderr)
        return 0
    project_id = str(json.loads(project_state_path.read_text())["project_id"])

    deliveries_path = base / "deliveries" / "deliveries.jsonl"
    deliveries_path.parent.mkdir(parents=True, exist_ok=True)

    existing_issues: set[int] = set()
    if deliveries_path.exists():
        for line in deliveries_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                existing_issues.add(json.loads(line)["issue"])

    new_lines: list[str] = []
    for line in entregas_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entrega = json.loads(line)
        if entrega["issue"] in existing_issues:
            continue

        veredito = entrega.get("revisor", {}).get("veredito")
        if veredito in _PENDING_VERDICTS:
            continue  # entrega ainda em trânsito — nem sincroniza, nem marca como vista

        record = {
            "schema_version": "1.0",
            "project_id": project_id,
            "run_id": None,
            **entrega,
        }
        ok, errors = validate(record, "delivery-record")
        if not ok:
            print(
                f"harness_deliveries: pulando issue {entrega['issue']} — "
                f"delivery-record inválido: {errors}",
                file=sys.stderr,
            )
            continue

        new_lines.append(json.dumps(record, ensure_ascii=False))
        existing_issues.add(entrega["issue"])

    if new_lines:
        with deliveries_path.open("a", encoding="utf-8") as f:
            for line in new_lines:
                f.write(line + "\n")

    return len(new_lines)
