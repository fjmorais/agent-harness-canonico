"""Scaffold e fingerprint do `.harness/` para um projeto novo (task 03).

`project_id` é gerado uma única vez (hash de path absoluto + timestamp de criação) e depois
tratado como imutável — ver docs/adr/001-observabilidade-harness-control.md, Opção K.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

HARNESS_DIRNAME = ".harness"

# Ignora exatamente estes três padrões — ver critério de aceite da task 03.
GITIGNORE_CONTENT = "runs/**\naudit/**\nindexes/**\n"

VERSIONED_EMPTY_DIRS = ["locks", "runtime"]
IGNORED_EMPTY_DIRS = ["runs", "audit", "indexes", "deliveries"]


def harness_dir(target: Path) -> Path:
    return target / HARNESS_DIRNAME


def generate_project_id(path: Path, created_at: str) -> str:
    """Hash determinístico de (path absoluto, timestamp de criação). Chamar só uma vez por
    projeto — o resultado é gravado e nunca recalculado depois."""
    digest = hashlib.sha256(f"{path.resolve()}:{created_at}".encode()).hexdigest()
    return f"project_{digest[:32]}"


def fingerprint_file(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


@dataclass
class ScaffoldOperation:
    action: str  # "create_directory" | "create_file"
    path: str  # relativo a target/.harness/


@dataclass
class ScaffoldPlan:
    operations: list[ScaffoldOperation] = field(default_factory=list)

    def as_json(self) -> list[dict[str, str]]:
        return [{"action": op.action, "path": op.path} for op in self.operations]


def plan_harness_scaffold(target: Path) -> ScaffoldPlan:
    """Plano de scaffold para um projeto SEM `.harness/` ainda. Não escreve nada."""
    plan = ScaffoldPlan()
    plan.operations.append(ScaffoldOperation("create_file", "README.md"))
    plan.operations.append(ScaffoldOperation("create_file", "config.json"))
    plan.operations.append(ScaffoldOperation("create_file", ".gitignore"))
    plan.operations.append(ScaffoldOperation("create_directory", "state"))
    plan.operations.append(ScaffoldOperation("create_file", "state/project.json"))
    plan.operations.append(ScaffoldOperation("create_file", "state/current-workflow.json"))
    for d in VERSIONED_EMPTY_DIRS + IGNORED_EMPTY_DIRS:
        plan.operations.append(ScaffoldOperation("create_directory", d))
    plan.operations.append(ScaffoldOperation("create_file", "audit/audit.jsonl"))
    plan.operations.append(ScaffoldOperation("create_file", "state/installed-files.json"))
    return plan


def _readme_content(project_name: str) -> str:
    return (
        f"# .harness/ — {project_name}\n\n"
        "Estrutura de observabilidade gerada pelo install-harness. Ver "
        "docs/adr/001-observabilidade-harness-control.md no canônico para o design.\n"
    )


def apply_harness_scaffold(target: Path, project_name: str) -> dict[str, int]:
    """Cria o `.harness/` completo. Idempotente só na primeira chamada — chamar contra um
    projeto que já tem `.harness/` é responsabilidade da task 04 (update seguro), não desta
    função."""
    base = harness_dir(target)
    created_at = datetime.now(UTC).isoformat()
    project_id = generate_project_id(target, created_at)

    for d in VERSIONED_EMPTY_DIRS + IGNORED_EMPTY_DIRS + ["state"]:
        (base / d).mkdir(parents=True, exist_ok=True)

    (base / "README.md").write_text(_readme_content(project_name), encoding="utf-8")
    (base / ".gitignore").write_text(GITIGNORE_CONTENT, encoding="utf-8")

    config = {
        "schema_version": "1.0",
        "project_id": project_id,
        "project_name": project_name,
        "created_at": created_at,
        "telemetry": {
            "enabled": False,
            "capture_prompts": False,
            "capture_tool_details": False,
        },
        "retention": {"days": 365},
        "storage": {"operational_logs": "local", "aggregated_metrics": "git"},
    }
    (base / "config.json").write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    project_state = {
        "schema_version": "1.0",
        "project_id": project_id,
        "project_name": project_name,
        "created_at": created_at,
    }
    (base / "state" / "project.json").write_text(
        json.dumps(project_state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    workflow_state: dict[str, object] = {
        "schema_version": "1.0",
        "project_id": project_id,
        "active_run_id": None,
        "active_writers": [],
        "updated_at": created_at,
    }
    (base / "state" / "current-workflow.json").write_text(
        json.dumps(workflow_state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    (base / "audit" / "audit.jsonl").write_text("", encoding="utf-8")

    fingerprints = {
        str(p.relative_to(base)): fingerprint_file(p)
        for p in sorted(base.rglob("*"))
        if p.is_file() and p.name != "installed-files.json"
    }
    installed_files = {"schema_version": "1.0", "files": fingerprints}
    (base / "state" / "installed-files.json").write_text(
        json.dumps(installed_files, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    return {
        "created_files": len(fingerprints) + 1,
        "created_dirs": len(VERSIONED_EMPTY_DIRS) + len(IGNORED_EMPTY_DIRS) + 1,
    }


def read_installed_files(target: Path) -> dict[str, str]:
    path = harness_dir(target) / "state" / "installed-files.json"
    data: dict[str, object] = json.loads(path.read_text())
    files = data["files"]
    assert isinstance(files, dict)
    return {str(k): str(v) for k, v in files.items()}
