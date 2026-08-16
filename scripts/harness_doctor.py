"""`harness_doctor.py` — diagnóstico honesto por capability (task 12).

Recalcula o checksum de todo arquivo registrado em `state/installed-files.json` (tasks 03/04),
compara com o valor gravado, e reporta status por capability declarada no manifest. Nunca
preenche métrica ausente com zero ou estimativa — lacuna sempre `None`/`"unavailable"` com
motivo explícito. Ver seção 5 do plano original e Pergunta 6 do grill.
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.harness_scaffold import fingerprint_file, harness_dir

MANIFEST_REL = ".claude/harness-manifest.json"

# Mapeamento best-effort arquivo -> capability que ele evidencia. Capabilities são conceitos
# amplos (seção 3.1 do plano) sem 1:1 óbvio com arquivo — este mapeamento é o ponto de partida
# do MVP, não uma verdade definitiva.
_FILE_CAPABILITY_MAP = {
    "config.json": "workflow",
    "state/project.json": "workflow",
    "README.md": "workflow",
    "state/current-workflow.json": "dev_loop",
    "audit/audit.jsonl": "delivery_metrics",
}

_STATUS_PRIORITY = ["missing", "customized", "ok"]  # pior status vence quando há múltiplos arquivos


def _read_manifest(project_path: Path) -> dict[str, object] | None:
    manifest_path = project_path / MANIFEST_REL
    if not manifest_path.exists():
        return None
    try:
        data: dict[str, object] = json.loads(manifest_path.read_text())
        return data
    except json.JSONDecodeError:
        return None


def _read_installed_files(project_path: Path) -> dict[str, str] | None:
    path = harness_dir(project_path) / "state" / "installed-files.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return None
    files = data.get("files")
    if not isinstance(files, dict):
        return None
    return {str(k): str(v) for k, v in files.items()}


def _diagnose_files(project_path: Path, registered: dict[str, str]) -> dict[str, str]:
    """Retorna {rel_path: status} para cada arquivo registrado — 'ok'/'customized'/'missing'."""
    base = harness_dir(project_path)
    result: dict[str, str] = {}
    for rel_path, recorded_fingerprint in registered.items():
        file_path = base / rel_path
        if not file_path.exists():
            result[rel_path] = "missing"
            continue
        current_fingerprint = fingerprint_file(file_path)
        result[rel_path] = "ok" if current_fingerprint == recorded_fingerprint else "customized"
    return result


def _aggregate_capability_status(
    file_statuses: dict[str, str], capability: str
) -> tuple[str, dict[str, object]]:
    relevant = {
        rel_path: status
        for rel_path, status in file_statuses.items()
        if _FILE_CAPABILITY_MAP.get(rel_path) == capability
    }
    if not relevant:
        return "blocked", {"reason": "nenhum arquivo mapeado para esta capability foi encontrado"}
    for candidate in _STATUS_PRIORITY:
        if candidate in relevant.values():
            return candidate, {"files": relevant}
    return "ok", {
        "files": relevant
    }  # pragma: no cover — inalcançável, _STATUS_PRIORITY é exaustivo


def _diagnose_telemetry(manifest: dict[str, object] | None) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    if manifest is None:
        return result
    capabilities = manifest.get("capabilities")
    if not isinstance(capabilities, dict):
        return result
    telemetry = capabilities.get("telemetry")
    if not isinstance(telemetry, dict):
        return result

    for executor, declared in telemetry.items():
        if declared is True:
            result[executor] = {"status": "ok", "reason": None}
        elif declared is False:
            result[executor] = {"status": "missing", "reason": "capability desativada no manifest"}
        elif isinstance(declared, str):
            # "unavailable" / "blocked" — nunca inventamos um "ok" ou "0" aqui, repassa o motivo
            result[executor] = {
                "status": declared,
                "reason": f"executor sem adapter configurado ({declared})",
            }
        else:
            result[executor] = {
                "status": "blocked",
                "reason": "valor de capability inesperado no manifest",
            }
    return result


def diagnose(project_path: Path) -> dict[str, object]:
    """Diagnóstico honesto por capability. Nunca retorna `0`/valor fabricado para dado
    desconhecido — sempre `None`/`"blocked"`/`"unavailable"` com motivo explícito."""
    manifest = _read_manifest(project_path)
    registered = _read_installed_files(project_path)

    if registered is None:
        # .harness/ não instalado ou registro de fingerprint corrompido/ausente — não inventamos
        # status "ok" nem contagem "0"; é uma lacuna explícita.
        return {
            "scaffold_checked_files_count": None,
            "capabilities": {
                cap: {
                    "status": "blocked",
                    "reason": ".harness/state/installed-files.json ausente ou ilegível",
                }
                for cap in ("workflow", "dev_loop", "delivery_metrics")
            },
            "telemetry": _diagnose_telemetry(manifest),
        }

    file_statuses = _diagnose_files(project_path, registered)
    capabilities: dict[str, object] = {}
    for capability in ("workflow", "dev_loop", "delivery_metrics"):
        status, details = _aggregate_capability_status(file_statuses, capability)
        capabilities[capability] = {"status": status, **details}

    return {
        "scaffold_checked_files_count": len(registered),
        "capabilities": capabilities,
        "telemetry": _diagnose_telemetry(manifest),
    }
