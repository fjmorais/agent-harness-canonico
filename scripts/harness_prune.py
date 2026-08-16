"""`harness_prune.py` — retenção manual confirmada (task 14).

Nunca remove nada sem `--confirm` explícito — `runs/**` não tem backup no Git (está no
`.gitignore` do scaffold, task 03), então exclusão automática violaria
`.claude/rules/seguranca.md` (operação destrutiva sempre confirmada pelo usuário).
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from scripts.harness_scaffold import harness_dir


@dataclass
class PruneCandidate:
    run_id: str
    path: Path
    started_at: str
    age_days: float


def _read_retention_days(target: Path) -> int:
    config_path = harness_dir(target) / "config.json"
    config = json.loads(config_path.read_text())
    days = config.get("retention", {}).get("days")
    if not isinstance(days, int):
        raise ValueError("config.json: retention.days ausente ou inválido")
    return days


def plan_prune(target: Path, now: datetime | None = None) -> list[PruneCandidate]:
    """Lista runs mais velhos que `retention.days`, sem tocar em nada. Idade calculada a partir
    de `run.json.started_at` (nunca do nome do diretório — mais preciso que granularidade
    YYYY/MM)."""
    now = now or datetime.now(UTC)
    retention_days = _read_retention_days(target)

    runs_dir = harness_dir(target) / "runs"
    if not runs_dir.exists():
        return []

    candidates: list[PruneCandidate] = []
    for run_json_path in sorted(runs_dir.glob("*/*/run_*/run.json")):
        run = json.loads(run_json_path.read_text())
        started_at = datetime.fromisoformat(str(run["started_at"]))
        age_days = (now - started_at).total_seconds() / 86400
        if age_days > retention_days:
            candidates.append(
                PruneCandidate(
                    run_id=str(run["run_id"]),
                    path=run_json_path.parent,
                    started_at=str(run["started_at"]),
                    age_days=age_days,
                )
            )
    return candidates


def apply_prune(target: Path, confirm: bool) -> dict[str, int]:
    """Sem `confirm=True`, nunca remove nada (só relata quantos seriam removidos)."""
    candidates = plan_prune(target)
    if not confirm:
        return {"would_remove": len(candidates), "removed": 0}

    removed = 0
    failed = 0
    for candidate in candidates:
        try:
            shutil.rmtree(candidate.path)
            removed += 1
        except OSError as exc:
            # ferramenta administrativa manual — reporta e segue pros próximos candidatos em
            # vez de abortar o batch inteiro (ex.: permissão negada, removido por outro processo)
            print(f"harness_prune: falha ao remover {candidate.run_id}: {exc}", file=sys.stderr)
            failed += 1
    return {"would_remove": len(candidates), "removed": removed, "failed": failed}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="path do projeto (contém .harness/)")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="remove de fato os runs fora da retenção (sem isso, só lista — dry-run é o padrão)",
    )
    args = parser.parse_args()

    target = Path(args.target).resolve()
    candidates = plan_prune(target)
    if not candidates:
        print("harness_prune: nenhum run fora da janela de retenção.")
        return

    print(f"harness_prune: {len(candidates)} run(s) fora da janela de retenção:")
    for c in candidates:
        print(f"  - {c.run_id} (iniciado em {c.started_at}, {c.age_days:.1f} dias)")

    if not args.confirm:
        print("\nDry-run — nada foi removido. Rode com --confirm para remover de fato.")
        return

    result = apply_prune(target, confirm=True)
    print(f"\nRemovido(s): {result['removed']}.")


if __name__ == "__main__":
    main()
