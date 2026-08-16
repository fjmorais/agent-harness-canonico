"""Scaffold e fingerprint do `.harness/` para um projeto novo (task 03).

`project_id` é gerado uma única vez (hash de path absoluto + timestamp de criação) e depois
tratado como imutável — ver docs/adr/001-observabilidade-harness-control.md, Opção K.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from scripts.schema_validation import assert_write_compatible, current_version

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


# ------------------------------------------------------------------ update seguro (task 04)

# path -> (kind, conteúdo default se precisar ser criado do zero)
_EXPECTED_DIRS = VERSIONED_EMPTY_DIRS + IGNORED_EMPTY_DIRS + ["state"]
_EXPECTED_FILES = [
    "README.md",
    ".gitignore",
    "state/current-workflow.json",
    "audit/audit.jsonl",
]


def is_harness_installed(target: Path) -> bool:
    return (harness_dir(target) / "config.json").exists()


@dataclass
class MigrationItem:
    schema: str
    from_version: str
    to_version: str
    requires_confirmation: bool = True

    def as_json(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "from": self.from_version,
            "to": self.to_version,
            "requires_confirmation": self.requires_confirmation,
        }


@dataclass
class UpdatePlan:
    create_operations: list[ScaffoldOperation] = field(default_factory=list)
    migrations: list[MigrationItem] = field(default_factory=list)

    def as_json(self) -> dict[str, object]:
        return {
            "create_operations": [
                {"action": op.action, "path": op.path} for op in self.create_operations
            ],
            "migrations": [m.as_json() for m in self.migrations],
        }


def plan_harness_update(target: Path) -> UpdatePlan:
    """Plano de update para um `.harness/` já existente. Nunca inclui `runs/`, `deliveries/` ou
    qualquer arquivo já presente — só itens ausentes e migrations pendentes. Não escreve nada."""
    base = harness_dir(target)
    plan = UpdatePlan()

    for d in _EXPECTED_DIRS:
        if not (base / d).exists():
            plan.create_operations.append(ScaffoldOperation("create_directory", d))
    for f in _EXPECTED_FILES:
        if not (base / f).exists():
            plan.create_operations.append(ScaffoldOperation("create_file", f))

    config_path = base / "config.json"
    if config_path.exists():
        config = json.loads(config_path.read_text())
        installed_version = str(config.get("schema_version", "1.0"))
        latest_version = current_version("harness-config")
        if installed_version != latest_version:
            plan.migrations.append(
                MigrationItem("harness-config", installed_version, latest_version)
            )

    return plan


def _read_config_schema_version(base: Path) -> str | None:
    config_path = base / "config.json"
    if not config_path.exists():
        return None
    config = json.loads(config_path.read_text())
    version = config.get("schema_version")
    return str(version) if version is not None else None


def _default_content_for(rel_path: str, project_name: str) -> str:
    if rel_path == "README.md":
        return _readme_content(project_name)
    if rel_path == ".gitignore":
        return GITIGNORE_CONTENT
    if rel_path == "audit/audit.jsonl":
        return ""
    if rel_path == "state/current-workflow.json":
        payload: dict[str, object] = {
            "schema_version": "1.0",
            "project_id": "",
            "active_run_id": None,
            "active_writers": [],
            "updated_at": datetime.now(UTC).isoformat(),
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    raise ValueError(f"sem conteúdo default para: {rel_path}")


def apply_harness_update(
    target: Path, project_name: str, confirm_migrations: bool = False
) -> dict[str, object]:
    """Aplica só o que está no plano: cria itens ausentes; aplica migrations apenas se
    `confirm_migrations=True` (nunca implícito). Nunca toca `runs/`, `deliveries/`,
    `project_id` ou campos de config já customizados além de `schema_version`."""
    base = harness_dir(target)
    plan = plan_harness_update(target)

    pinned_version = _read_config_schema_version(base)

    created = 0
    skipped_incompatible: list[str] = []
    for op in plan.create_operations:
        path = base / op.path
        if op.action == "create_directory":
            path.mkdir(parents=True, exist_ok=True)
            created += 1
            continue

        if op.path == "state/current-workflow.json":
            # project_id precisa ser lido do project.json existente, não inventado
            project_state = json.loads((base / "state" / "project.json").read_text())
            payload: dict[str, object] = {
                "schema_version": "1.0",
                "project_id": project_state["project_id"],
                "active_run_id": None,
                "active_writers": [],
                "updated_at": datetime.now(UTC).isoformat(),
            }
            if pinned_version is not None:
                try:
                    assert_write_compatible(
                        pinned_version=pinned_version,
                        payload_version=str(payload["schema_version"]),
                    )
                except ValueError:
                    # nunca aborta o batch inteiro por causa de um arquivo — task 09 já
                    # estabeleceu esse padrão para o adapter de deliveries.
                    skipped_incompatible.append(op.path)
                    continue
            path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
        else:
            path.write_text(_default_content_for(op.path, project_name), encoding="utf-8")
        created += 1

    backups = 0
    migrations_applied = 0
    if confirm_migrations:
        for migration in plan.migrations:
            if migration.schema != "harness-config":
                continue
            config_path = base / "config.json"
            backup_dir = base / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f")
            backup_path = backup_dir / f"config.json.{stamp}.bak"
            shutil.copy2(config_path, backup_path)
            backups += 1

            config = json.loads(config_path.read_text())
            config["schema_version"] = migration.to_version
            config_path.write_text(
                json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            migrations_applied += 1

    # atualiza installed-files.json só para os arquivos tocados nesta chamada — preserva
    # entradas de arquivos preexistentes/customizados que não foram recriados.
    installed_files_path = base / "state" / "installed-files.json"
    existing_fingerprints = read_installed_files(target) if installed_files_path.exists() else {}
    touched_paths = [op.path for op in plan.create_operations]
    if confirm_migrations and migrations_applied:
        touched_paths.append("config.json")
    for rel_path in touched_paths:
        file_path = base / rel_path
        if file_path.is_file():
            existing_fingerprints[rel_path] = fingerprint_file(file_path)
    installed_files_path.write_text(
        json.dumps(
            {"schema_version": "1.0", "files": existing_fingerprints}, indent=2, ensure_ascii=False
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        "created": created,
        "migrations_applied": migrations_applied,
        "backups": backups,
        "skipped_incompatible": skipped_incompatible,
    }


# ------------------------------------------------------------------ adapter Cursor (task 11)

CURSOR_HOOKS_REL = ".cursor/hooks.json"
_HOOK_SCRIPT_COMMAND = "uv run python3 scripts/harness_hook.py"
_CURSOR_HOOK_EVENTS = ["sessionStart", "sessionEnd", "preToolUse", "postToolUse", "subagentStop"]


def generate_cursor_hooks_config() -> dict[str, object]:
    """Conteúdo de `.cursor/hooks.json` apontando pro mesmo `scripts/harness_hook.py` usado
    pelo adapter Claude Code (task 07) — sem duplicar lógica, só a camada de normalização de
    payload já cuida da diferença de formato (ver docs/adr/002-viabilidade-hooks-cursor.md)."""
    return {
        "version": 1,
        "hooks": {event: [{"command": _HOOK_SCRIPT_COMMAND}] for event in _CURSOR_HOOK_EVENTS},
    }


def write_cursor_hooks_config(target: Path) -> Path:
    path = target / CURSOR_HOOKS_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(generate_cursor_hooks_config(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path
