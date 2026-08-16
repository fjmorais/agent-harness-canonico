#!/usr/bin/env python3
"""CLI standalone para instalar/atualizar o Agent Harness Canônico num projeto alvo.

Uso:
    python3 install_harness.py <destino> [--canonical PATH] [--dry-run] [--yes] [--json]
                                [--force-category NOME ...]

Roda sozinha, sem depender do Claude Code — Python 3 stdlib apenas, sem dependências.
Nunca sobrescreve um arquivo existente sem confirmação explícita do usuário.

Fluxo:
  1. detect_mode()          -> NOVO | SEM_HARNESS | ATUALIZACAO
  2. collect_keywords()     -> vocabulário de keywords derivado do stack_map.json (não hardcoded)
  3. detect_stack_signals() -> parse de pyproject.toml/package.json/lockfiles + fallback textual
  4. build_plan()           -> classifica cada artefato do stack_map.json (--force-category
                                inclui categoria mesmo sem stack detectada)
  5. resolve_conflicts      -> interativo (input()) ou via --decisions-file (--json)
  6. apply_plan()           -> copia/gera/scaffold, espelha .cursor/, grava manifest
"""

from __future__ import annotations

import argparse
import difflib
import filecmp
import json
import re
import shutil
import sys
import tomllib
from datetime import date
from pathlib import Path

DEFAULT_CANONICAL = "/home/fabiano/agent-harness-canonico"
MANIFEST_REL = ".claude/harness-manifest.json"
KEYWORD_FILES = [
    "pyproject.toml",
    "package.json",
]  # fallback: scan bruto se o parse estruturado falhar


def _import_harness_scaffold(canonical: Path) -> tuple[object, ...] | None:
    """Importa scripts/harness_scaffold.py a partir do `--canonical` informado (não do path
    físico deste arquivo) — mantém a mesma parametrização que o resto do script já respeita.
    Retorna None só quando o módulo de fato não existe naquele canônico (ex.: CLI copiada
    standalone para fora do repo agent-harness-canonico); qualquer outro erro de import
    (bug real no módulo) propaga, não é mascarado."""
    canonical_str = str(canonical)
    if canonical_str not in sys.path:
        sys.path.insert(0, canonical_str)
    try:
        import scripts.harness_scaffold as hs
    except ModuleNotFoundError as exc:
        if exc.name != "scripts" and exc.name != "scripts.harness_scaffold":
            raise
        return None
    return (
        hs.apply_harness_scaffold,
        hs.apply_harness_update,
        hs.harness_dir,
        hs.is_harness_installed,
        hs.plan_harness_scaffold,
        hs.plan_harness_update,
    )


# --------------------------------------------------------------------------- detecção


def read_manifest(target: Path) -> dict | None:
    manifest_path = target / MANIFEST_REL
    if not manifest_path.exists():
        return None
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def detect_mode(target: Path, manifest: dict | None) -> str:
    claude_dir = target / ".claude"
    if not claude_dir.exists() or not any(claude_dir.iterdir()):
        return "NOVO"
    if manifest is None:
        return "SEM_HARNESS"
    return "ATUALIZACAO"


def collect_keywords(stack_map: dict) -> set[str]:
    """Deriva o vocabulário de keywords do stack_map.json — nunca hardcoded em duplicata.
    Adicionar uma categoria keyword_in_files nova no stack_map já basta; nada a tocar aqui."""
    keywords: set[str] = set()
    for category in stack_map["categories"]:
        condition = category["condition"]
        if condition["type"] == "keyword_in_files":
            keywords.update(condition["keywords"])
    return keywords


def _dep_name(raw: str) -> str:
    """'fastapi[standard]>=0.100,<1.0' -> 'fastapi'. 'requests ; python_version<"3.9"' -> 'requests'."""
    return re.split(r"[<>=!\[\];~\s(]", raw.strip(), maxsplit=1)[0].strip().lower()


def _names_from_pyproject(path: Path) -> set[str]:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, OSError, UnicodeDecodeError):
        return set()
    names: set[str] = set()
    project = data.get("project", {})
    for dep in project.get("dependencies", []) or []:
        names.add(_dep_name(dep))
    for group in (project.get("optional-dependencies") or {}).values():
        for dep in group or []:
            names.add(_dep_name(dep))
    poetry = data.get("tool", {}).get("poetry", {})
    for key in ("dependencies", "dev-dependencies"):
        for pkg_name in poetry.get(key) or {}:
            if pkg_name.lower() != "python":
                names.add(pkg_name.lower())
    for group in (poetry.get("group") or {}).values():
        for pkg_name in group.get("dependencies") or {}:
            names.add(pkg_name.lower())
    uv_dev = data.get("tool", {}).get("uv", {}).get("dev-dependencies", []) or []
    for dep in uv_dev:
        names.add(_dep_name(dep))
    return names


def _names_from_package_json(path: Path) -> set[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return set()
    names: set[str] = set()
    for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        names.update(pkg.lower() for pkg in (data.get(key) or {}))
    return names


def _names_from_toml_lockfile(path: Path) -> set[str]:
    """uv.lock / poetry.lock — ambos TOML com [[package]] name = '...'."""
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, OSError, UnicodeDecodeError):
        return set()
    return {pkg["name"].lower() for pkg in data.get("package", []) or [] if pkg.get("name")}


def _names_from_package_lock_json(path: Path) -> set[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return set()
    names: set[str] = set()
    for key in data.get("packages") or {}:
        # chaves tipo "node_modules/pkg" ou "node_modules/@scope/pkg"
        leaf = key.rsplit("node_modules/", 1)[-1]
        if leaf:
            names.add(leaf.lower())
    names.update(pkg.lower() for pkg in (data.get("dependencies") or {}))
    return names


def _names_from_requirements_txt(path: Path) -> set[str]:
    names: set[str] = set()
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return names
    for line in lines:
        line = line.strip()
        if not line or line.startswith(("#", "-")):
            continue
        names.add(_dep_name(line))
    return names


def detect_stack_signals(target: Path, keywords: set[str]) -> dict:
    """Sinais de stack do projeto-alvo. Parse estruturado (TOML/JSON) das listas de
    dependência declaradas + lockfiles (sinal mais forte que o declarado) primeiro;
    scan de texto bruto como rede de segurança para formato não-padrão/malformado."""
    signals = {
        "pyproject": (target / "pyproject.toml").exists(),
        "package_json": (target / "package.json").exists(),
        "docker_compose": (target / "docker-compose.yml").exists(),
        "keywords": set(),
    }

    dep_names: set[str] = set()
    if signals["pyproject"]:
        dep_names |= _names_from_pyproject(target / "pyproject.toml")
    if signals["package_json"]:
        dep_names |= _names_from_package_json(target / "package.json")
    if (target / "requirements.txt").exists():
        dep_names |= _names_from_requirements_txt(target / "requirements.txt")
    if (target / "uv.lock").exists():
        dep_names |= _names_from_toml_lockfile(target / "uv.lock")
    if (target / "poetry.lock").exists():
        dep_names |= _names_from_toml_lockfile(target / "poetry.lock")
    if (target / "package-lock.json").exists():
        dep_names |= _names_from_package_lock_json(target / "package-lock.json")

    for kw in keywords:
        if any(kw == name or kw in name for name in dep_names):
            signals["keywords"].add(kw)

    # rede de segurança: scan de texto bruto (pega o que o parse estruturado não cobre —
    # formato não-padrão, dependência mencionada em comentário/script, etc.)
    for fname in KEYWORD_FILES:
        fpath = target / fname
        if not fpath.exists():
            continue
        try:
            text = fpath.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        for kw in keywords:
            if kw in text:
                signals["keywords"].add(kw)

    return signals


def condition_matches(condition: dict, signals: dict) -> bool:
    ctype = condition["type"]
    if ctype == "always":
        return True
    if ctype == "file_exists":
        return any(
            (Path(f) == Path("pyproject.toml") and signals["pyproject"])
            or (Path(f) == Path("package.json") and signals["package_json"])
            or (Path(f) == Path("docker-compose.yml") and signals["docker_compose"])
            for f in condition["files"]
        )
    if ctype == "keyword_in_files":
        return any(kw in signals["keywords"] for kw in condition["keywords"])
    raise ValueError(f"condição desconhecida: {ctype}")


def load_stack_map(canonical: Path) -> dict:
    map_path = canonical / ".claude/skills/install-harness/scripts/stack_map.json"
    return json.loads(map_path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- plano


def paths_differ(a: Path, b: Path) -> bool:
    """True se a (existente) e b (canônico) têm conteúdo diferente. Compara árvore para dirs."""
    if a.is_dir() or b.is_dir():
        if not a.is_dir() or not b.is_dir():
            return True
        cmp = filecmp.dircmp(a, b)
        if cmp.left_only or cmp.right_only or cmp.diff_files or cmp.funny_files:
            return True
        for sub in cmp.common_dirs:
            if paths_differ(a / sub, b / sub):
                return True
        return False
    try:
        return a.read_bytes() != b.read_bytes()
    except OSError:
        return True


def build_plan(
    target: Path,
    canonical: Path,
    stack_map: dict,
    manifest: dict | None,
    signals: dict,
    force_categories: frozenset[str] = frozenset(),
    force_all: bool = False,
) -> list[dict]:
    artefacts = (manifest or {}).get("artefacts", {})
    plan: list[dict] = []

    for category in stack_map["categories"]:
        detected = condition_matches(category["condition"], signals)
        forced = not detected and (force_all or category["name"] in force_categories)
        matched = detected or forced
        for artefact in category["artifacts"]:
            rel = artefact["path"]
            kind = artefact["kind"]
            dest = target / rel
            src = None if kind == "generate" else canonical / rel
            item = {
                "path": rel,
                "kind": kind,
                "category": category["name"],
                "exists": dest.exists(),
            }
            if forced:
                item["forced"] = True

            if not matched:
                item["action"] = "SKIP_STACK"
                plan.append(item)
                continue

            tracked = artefacts.get(rel)

            if not dest.exists():
                item["action"] = (
                    "SCAFFOLD" if kind == "scaffold" else ("COPY" if kind == "copy" else "GENERATE")
                )
                plan.append(item)
                continue

            if kind == "scaffold":
                item["action"] = "KEEP"
                item["note"] = "pasta já existe — nunca sobrescrita"
                plan.append(item)
                continue

            if tracked is None:
                item["action"] = "CONFLICT"
                plan.append(item)
                continue

            if tracked.get("customized"):
                item["action"] = "KEEP"
                item["note"] = "manifest: customized=true"
                plan.append(item)
                continue

            # customized:false — candidato a auto-update, só se conteúdo realmente mudou
            if kind == "copy" and paths_differ(dest, src):
                item["action"] = "AUTO_UPDATE"
            else:
                item["action"] = "UP_TO_DATE"
            plan.append(item)

    return plan


# --------------------------------------------------------------------------- conflitos


def render_diff(dest: Path, src: Path) -> str:
    if dest.is_dir() or src.is_dir():
        if not dest.is_dir() or not src.is_dir():
            return "(um dos lados é arquivo, outro é diretório)"
        cmp = filecmp.dircmp(dest, src)
        lines = []
        if cmp.left_only:
            lines.append(f"  só no destino: {sorted(cmp.left_only)}")
        if cmp.right_only:
            lines.append(f"  só no canônico: {sorted(cmp.right_only)}")
        if cmp.diff_files:
            lines.append(f"  arquivos diferentes: {sorted(cmp.diff_files)}")
        return "\n".join(lines) or "(diretórios equivalentes)"
    try:
        dest_lines = dest.read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True)
        src_lines = src.read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True)
    except OSError as exc:
        return f"(não foi possível ler para diff: {exc})"
    diff = difflib.unified_diff(
        dest_lines, src_lines, fromfile="destino (atual)", tofile="canônico (novo)"
    )
    return "".join(diff) or "(sem diferenças de texto)"


def resolve_conflicts_interactive(plan: list[dict], target: Path, canonical: Path) -> None:
    keep_all = False
    overwrite_all = False
    for item in plan:
        if item["action"] != "CONFLICT":
            continue
        if keep_all:
            item["resolution"] = "keep"
            continue
        if overwrite_all:
            item["resolution"] = "overwrite"
            continue

        dest = target / item["path"]
        src = canonical / item["path"]
        while True:
            print(
                f"\n{item['path']} já existe e não está rastreado no manifest (ou difere do canônico)."
            )
            choice = input(
                "[k]eep  [o]verwrite  [d]iff  [m]erge manual (salva canônico como .harness-incoming)  "
                "[K]eep all restantes  [O]verwrite all restantes  [q] cancelar > "
            ).strip()
            if choice == "k":
                item["resolution"] = "keep"
                break
            if choice == "o":
                item["resolution"] = "overwrite"
                break
            if choice == "m":
                item["resolution"] = "merge"
                break
            if choice == "d":
                print(render_diff(dest, src))
                continue
            if choice == "K":
                item["resolution"] = "keep"
                keep_all = True
                break
            if choice == "O":
                item["resolution"] = "overwrite"
                overwrite_all = True
                break
            if choice == "q":
                print("Instalação cancelada.")
                sys.exit(1)
            print("Opção inválida.")


def resolve_conflicts_from_decisions(plan: list[dict], decisions: dict) -> None:
    for item in plan:
        if item["action"] != "CONFLICT":
            continue
        resolution = decisions.get(item["path"])
        if resolution not in ("keep", "overwrite", "merge"):
            raise ValueError(
                f"decisão ausente/inválida para conflito: {item['path']!r} -> {resolution!r}"
            )
        item["resolution"] = resolution


# --------------------------------------------------------------------------- geração de stubs


def generate_content(rel_path: str, project_name: str, stack_summary: str) -> str:
    today = date.today().isoformat()
    if rel_path == "CLAUDE.md":
        return (
            f"# {project_name}\n\n"
            f"> Gerado pelo install-harness em {today}. Stack detectada: {stack_summary or '(nenhuma detectada)'}.\n"
            "> Refine com `/grill-me` para registrar invariantes e decisões reais do projeto.\n\n"
            "## Stack\n\n"
            f"{stack_summary or '(preencher)'}\n\n"
            "## Invariantes\n\n"
            "(preencher com /grill-me)\n"
        )
    if rel_path == "AGENTS.md":
        return (
            f"# {project_name} — espelho portátil (Cursor/Windsurf/Codex)\n\n"
            f"> Gerado pelo install-harness em {today}. Sem referências a `.claude/`.\n\n"
            "## Stack\n\n"
            f"{stack_summary or '(preencher)'}\n\n"
            "## Comandos\n\n(preencher)\n\n## Invariantes\n\n(preencher)\n"
        )
    if rel_path == "CONTEXT.md":
        return (
            f"# Glossário de domínio — {project_name}\n\n"
            "> Iniciado pelo install-harness. Refinar com /grill-with-docs junto ao especialista de domínio.\n"
            "> Cada termo deve ter: definição precisa + sinônimos usados pelo time + o que NÃO é.\n\n"
            "---\n\n## Domínio\n\n(preencher com /grill-with-docs)\n\n"
            "## Termos do domínio\n\n| Termo | Definição | Sinônimos | O que NÃO é |\n|---|---|---|---|\n\n"
            "## Acrônimos e siglas\n\n| Sigla | Significado |\n|---|---|\n(nenhum informado)\n\n"
            "## Regras de negócio implícitas\n\n(preencher com /grill-with-docs)\n"
        )
    if rel_path == "HANDOFF.md":
        return (
            f"# Handoff — {project_name}\n\n"
            f"> Gerado pelo install-harness em {today}. Atualize a cada handoff de sessão.\n\n"
            "## Estado atual\n\n(preencher)\n\n## Próximos passos\n\n(preencher)\n"
        )
    if rel_path == ".claude/settings.json":
        hooks = {}
        if "python" in stack_summary.lower() or "fastapi" in stack_summary.lower():
            hooks = {
                "PostToolUse": [
                    {
                        "matcher": "Edit|Write",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "uv run ruff format . 2>/dev/null; uv run ruff check --fix . 2>/dev/null; true",
                            }
                        ],
                    }
                ],
                "Stop": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": "uv run ruff check . && uv run mypy . && uv run pytest -q || exit 2",
                            }
                        ]
                    }
                ],
            }
        elif "react" in stack_summary.lower() or "frontend" in stack_summary.lower():
            hooks = {
                "PostToolUse": [
                    {
                        "matcher": "Edit|Write",
                        "hooks": [
                            {"type": "command", "command": "npx eslint --fix . 2>/dev/null; true"}
                        ],
                    }
                ],
                "Stop": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": "npx eslint . && npx vitest run || exit 2",
                            }
                        ]
                    }
                ],
            }
        return (
            json.dumps(
                {"env": {}, "permissions": {"allow": [], "deny": []}, "hooks": hooks},
                indent=2,
                ensure_ascii=False,
            )
            + "\n"
        )
    raise ValueError(f"sem template de geração para: {rel_path}")


# --------------------------------------------------------------------------- aplicação


def mirror_to_cursor(target: Path, canonical: Path, rel_path: str) -> None:
    p = Path(rel_path)
    parts = p.parts
    if rel_path in ("CLAUDE.md", "AGENTS.md", "CONTEXT.md", "HANDOFF.md", "HARNESS-GUIDE.md"):
        return
    if rel_path == ".claude/settings.json":
        return
    if len(parts) < 2 or parts[0] != ".claude":
        return
    cursor_rel = Path(".cursor", *parts[1:])
    src_installed = target / rel_path

    if parts[1] == "rules" and p.suffix == ".md":
        mdc_path = target / ".cursor/rules" / (p.stem + ".mdc")
        mdc_path.parent.mkdir(parents=True, exist_ok=True)
        mdc_path.write_text(convert_rule_to_mdc(src_installed), encoding="utf-8")
        return

    if parts[1] in ("agents", "skills", "kb", "commands", "design", "projetos", "sdd", "dev"):
        cursor_dest = target / cursor_rel
        cursor_dest.parent.mkdir(parents=True, exist_ok=True)
        if src_installed.is_dir():
            if cursor_dest.exists():
                shutil.rmtree(cursor_dest)
            shutil.copytree(src_installed, cursor_dest)
        else:
            shutil.copy2(src_installed, cursor_dest)


def convert_rule_to_mdc(rule_path: Path) -> str:
    text = rule_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    description = rule_path.stem.replace("-", " ")
    globs: list[str] = []
    body_start = 0

    if lines and lines[0].strip() == "---":
        end = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end = i
                break
        if end is not None:
            header = lines[1:end]
            in_paths = False
            for hline in header:
                stripped = hline.strip()
                if stripped.startswith("#"):
                    description = stripped.lstrip("#").strip()
                elif stripped == "paths:":
                    in_paths = True
                elif in_paths and stripped.startswith("-"):
                    globs.append(stripped.lstrip("-").strip().strip('"'))
                elif stripped and not stripped.startswith("-"):
                    in_paths = False
            body_start = end + 1

    body = "\n".join(lines[body_start:]).lstrip("\n")
    always_apply = "false" if globs else "true"
    globs_json = json.dumps(globs, ensure_ascii=False)
    return f"---\ndescription: {description}\nglobs: {globs_json}\nalwaysApply: {always_apply}\n---\n\n\n{body}\n"


def apply_plan(
    plan: list[dict],
    target: Path,
    canonical: Path,
    project_name: str,
    stack_summary: str,
    mode: str,
    manifest: dict | None,
) -> dict:
    artefacts = dict((manifest or {}).get("artefacts", {}))
    counts = {
        "copied": 0,
        "generated": 0,
        "scaffolded": 0,
        "auto_updated": 0,
        "kept": 0,
        "overwritten": 0,
        "merged_manual": 0,
        "skipped_stack": 0,
    }

    for item in plan:
        rel = item["path"]
        dest = target / rel
        src = None if item["kind"] == "generate" else canonical / rel
        action = item.get("resolution") or item["action"]

        if action == "SKIP_STACK":
            counts["skipped_stack"] += 1
            continue

        if action == "UP_TO_DATE":
            continue

        if action == "KEEP":
            counts["kept"] += 1
            continue

        if action == "SCAFFOLD":
            dest.mkdir(parents=True, exist_ok=True)
            if rel in (".claude/design", ".claude/sdd"):
                for sub in ("features", "archive", "reports"):
                    (dest / sub).mkdir(exist_ok=True)
            if rel in (".claude/projetos", ".claude/guias"):
                readme_src = canonical / rel / "README.md"
                if readme_src.exists():
                    shutil.copy2(readme_src, dest / "README.md")
            artefacts[rel] = {"source": "generated", "customized": True}
            mirror_to_cursor(target, canonical, rel)
            counts["scaffolded"] += 1
            continue

        if action == "COPY":
            dest.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                shutil.copytree(src, dest)
            else:
                shutil.copy2(src, dest)
            artefacts[rel] = {"source": "canonical", "customized": False}
            mirror_to_cursor(target, canonical, rel)
            counts["copied"] += 1
            continue

        if action == "GENERATE":
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(generate_content(rel, project_name, stack_summary), encoding="utf-8")
            artefacts[rel] = {"source": "generated", "customized": True}
            counts["generated"] += 1
            continue

        if action == "AUTO_UPDATE":
            if src.is_dir():
                shutil.rmtree(dest)
                shutil.copytree(src, dest)
            else:
                shutil.copy2(src, dest)
            artefacts[rel] = {"source": "canonical", "customized": False}
            mirror_to_cursor(target, canonical, rel)
            counts["auto_updated"] += 1
            continue

        if action == "overwrite":
            if item["kind"] == "generate":
                dest.write_text(
                    generate_content(rel, project_name, stack_summary), encoding="utf-8"
                )
            elif src.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(src, dest)
            else:
                shutil.copy2(src, dest)
            artefacts[rel] = {
                "source": "canonical" if item["kind"] == "copy" else "generated",
                "customized": False,
            }
            mirror_to_cursor(target, canonical, rel)
            counts["overwritten"] += 1
            continue

        if action == "keep":
            artefacts[rel] = {
                "source": artefacts.get(rel, {}).get("source", "unknown"),
                "customized": True,
            }
            counts["kept"] += 1
            continue

        if action == "merge":
            incoming = Path(str(dest) + ".harness-incoming")
            if incoming.exists():
                shutil.rmtree(incoming) if incoming.is_dir() else incoming.unlink()
            if item["kind"] == "generate":
                incoming.write_text(
                    generate_content(rel, project_name, stack_summary), encoding="utf-8"
                )
            elif src.is_dir():
                shutil.copytree(src, incoming)
            else:
                shutil.copy2(src, incoming)
            artefacts[rel] = {
                "source": artefacts.get(rel, {}).get("source", "unknown"),
                "customized": True,
            }
            counts["merged_manual"] += 1
            continue

    write_manifest(target, canonical, mode, artefacts)
    return counts


HARNESS_VERSION = "0.1.0"


def write_manifest(target: Path, canonical: Path, mode: str, artefacts: dict) -> None:
    manifest_path = target / MANIFEST_REL
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    previous = read_manifest(target) or {}
    manifest = {
        "manifest_schema_version": "2.0",
        "harness_version": HARNESS_VERSION,
        "canonical_path": str(canonical),
        "installed_at": date.today().isoformat(),
        "mode": mode,
        "capabilities": previous.get("capabilities")
        or {
            "workflow": True,
            "dev_loop": True,
            "delivery_metrics": True,
            "telemetry": {},
        },
        "artefacts": artefacts,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


# --------------------------------------------------------------------------- apresentação

BUCKET_LABELS = {
    "COPY": "COPIAR do canônico",
    "GENERATE": "GERAR (projeto-específico)",
    "SCAFFOLD": "SCAFFOLD (pastas)",
    "AUTO_UPDATE": "ATUALIZAR (canônico evoluiu, customized=false)",
    "SKIP_STACK": "PULAR (stack não detectada)",
    "KEEP": "NÃO TOCAR (já existe ou customizado)",
    "UP_TO_DATE": "NÃO TOCAR (já atualizado)",
    "CONFLICT": "CONFLITOS — precisa decidir",
}


def print_plan_human(plan: list[dict], mode: str, signals: dict) -> None:
    print(f"\n# Install Plan\n\n## Modo: {mode}")
    kw = ", ".join(sorted(signals["keywords"])) or "(nenhuma)"
    print(
        f"## Stack detectada: keywords={kw} pyproject={signals['pyproject']} package.json={signals['package_json']}\n"
    )
    for bucket, label in BUCKET_LABELS.items():
        items = [i for i in plan if i["action"] == bucket]
        if not items:
            continue
        print(f"## {label}")
        for i in items:
            note = f" ← {i['note']}" if i.get("note") else ""
            forced = " [forçado — sem stack detectada]" if i.get("forced") else ""
            print(f"- {i['path']}{note}{forced}")
        print()
    skipped_categories = sorted({i["category"] for i in plan if i["action"] == "SKIP_STACK"})
    if skipped_categories:
        print(f"Categorias puladas por falta de stack detectada: {', '.join(skipped_categories)}")
        print("Para incluir mesmo assim: --force-category NOME (repetível)\n")


def plan_to_json(plan: list[dict], mode: str, signals: dict) -> dict:
    return {
        "mode": mode,
        "stack_signals": {
            **{k: v for k, v in signals.items() if k != "keywords"},
            "keywords": sorted(signals["keywords"]),
        },
        "items": plan,
    }


def summarize(counts: dict) -> str:
    parts = [f"{v} {k}" for k, v in counts.items() if v]
    return ", ".join(parts) if parts else "nada a fazer"


# --------------------------------------------------------------------------- main


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("destino", nargs="?", help="pasta alvo onde instalar/atualizar o harness")
    parser.add_argument(
        "--canonical", default=DEFAULT_CANONICAL, help="path do canônico (default: %(default)s)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="só mostra o plano, não escreve nada"
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="modo não-interativo: mantém tudo que já existe (nunca sobrescreve)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="imprime o plano em JSON; usa --decisions-file para aplicar",
    )
    parser.add_argument(
        "--decisions-file",
        help="JSON {path: keep|overwrite|merge} para resolver conflitos sem prompt",
    )
    parser.add_argument(
        "--force-category",
        action="append",
        default=[],
        metavar="NOME",
        help="inclui a categoria mesmo sem stack detectada (repetível, ex.: "
        "--force-category langgraph --force-category rag_vetorial)",
    )
    parser.add_argument(
        "--force-all",
        action="store_true",
        help="inclui TODAS as categorias mesmo sem stack detectada (sobrepõe --force-category)",
    )
    args = parser.parse_args()

    canonical = Path(args.canonical).resolve()
    if not (canonical / ".claude/agents").exists():
        print(f"CANÔNICO NÃO ENCONTRADO em {canonical}", file=sys.stderr)
        sys.exit(1)

    destino = args.destino
    if destino is None:
        if args.json:
            print("--json requer <destino> explícito", file=sys.stderr)
            sys.exit(1)
        destino = input(
            f"Em qual pasta devo instalar/atualizar o harness? (Enter para {Path.cwd()}) "
        ).strip() or str(Path.cwd())

    target = Path(destino).resolve()
    if not target.exists():
        if (
            args.yes
            or args.json
            or input(f"{target} não existe. Criar? [S/n] ").strip().lower() != "n"
        ):
            target.mkdir(parents=True)
        else:
            print("Cancelado.")
            sys.exit(1)

    manifest = read_manifest(target)
    mode = detect_mode(target, manifest)
    stack_map = load_stack_map(canonical)
    keywords = collect_keywords(stack_map)
    signals = detect_stack_signals(target, keywords)
    force_categories = frozenset(args.force_category)
    plan = build_plan(
        target, canonical, stack_map, manifest, signals, force_categories, args.force_all
    )

    # .harness/ scaffold (projeto novo) ou update seguro (task 03/04) — importado a partir do
    # --canonical informado, não do path físico deste arquivo.
    harness_fns = _import_harness_scaffold(canonical)
    apply_harness_scaffold = apply_harness_update = None
    harness_dir_fn = is_harness_installed = plan_harness_scaffold = plan_harness_update = None
    harness_plan = None
    harness_update_plan = None
    if harness_fns is None:
        if not args.json:
            print(
                "(scaffold .harness/ não disponível — rodando fora do repo agent-harness-canonico)"
            )
    else:
        (
            apply_harness_scaffold,
            apply_harness_update,
            harness_dir_fn,
            is_harness_installed,
            plan_harness_scaffold,
            plan_harness_update,
        ) = harness_fns
        if not harness_dir_fn(target).exists():
            harness_plan = plan_harness_scaffold(target)
        elif is_harness_installed(target):
            harness_update_plan = plan_harness_update(target)

    if args.json:
        plan_json = plan_to_json(plan, mode, signals)
        if harness_plan is not None:
            plan_json["harness_scaffold"] = harness_plan.as_json()
        if harness_update_plan is not None:
            plan_json["harness_update"] = harness_update_plan.as_json()
        print(json.dumps(plan_json, indent=2, ensure_ascii=False))
        if args.dry_run or not args.decisions_file:
            return
        decisions = json.loads(Path(args.decisions_file).read_text(encoding="utf-8"))
        resolve_conflicts_from_decisions(plan, decisions)
        project_name = target.name
        stack_summary = ", ".join(sorted(signals["keywords"])) or "(genérica)"
        counts = apply_plan(plan, target, canonical, project_name, stack_summary, mode, manifest)
        applied = {"applied": counts}
        if harness_plan is not None and apply_harness_scaffold is not None:
            applied["harness_scaffold"] = apply_harness_scaffold(target, project_name)
        if harness_update_plan is not None and apply_harness_update is not None:
            confirm_migrations = bool(decisions.get("confirm_harness_migrations", False))
            applied["harness_update"] = apply_harness_update(
                target, project_name, confirm_migrations=confirm_migrations
            )
        print(json.dumps(applied, indent=2, ensure_ascii=False))
        return

    print_plan_human(plan, mode, signals)
    if harness_plan is not None:
        print("## .harness/ — scaffold (projeto novo)")
        for op in harness_plan.operations:
            print(f"- {op.action}: .harness/{op.path}")
        print()
    if harness_update_plan is not None:
        print("## .harness/ — update seguro (projeto existente)")
        for op in harness_update_plan.create_operations:
            print(f"- {op.action}: .harness/{op.path}")
        for migration in harness_update_plan.migrations:
            print(
                f"- MIGRATION: {migration.schema} {migration.from_version} -> "
                f"{migration.to_version} (requires_confirmation={migration.requires_confirmation})"
            )
        print()
    if args.dry_run:
        return

    harness_extra = (len(harness_plan.operations) if harness_plan is not None else 0) + (
        len(harness_update_plan.create_operations) if harness_update_plan is not None else 0
    )

    if args.yes:
        for item in plan:
            if item["action"] == "CONFLICT":
                item["resolution"] = "keep"
        confirm_migrations = False  # nunca aplica migration automaticamente em modo não-interativo
    else:
        resolve_conflicts_interactive(plan, target, canonical)
        n_actionable = (
            sum(1 for i in plan if i["action"] not in ("SKIP_STACK", "KEEP", "UP_TO_DATE"))
            + harness_extra
        )
        if n_actionable == 0 and not (harness_update_plan and harness_update_plan.migrations):
            print("Nada a fazer — harness já está atualizado.")
            return
        if n_actionable > 0:
            confirm = (
                input(f"\n{n_actionable} artefatos serão tocados. Confirma? [s/N] ").strip().lower()
            )
            if confirm != "s":
                print("Cancelado — nada foi escrito.")
                return
        confirm_migrations = False
        if harness_update_plan is not None and harness_update_plan.migrations:
            migration_confirm = (
                input(
                    f"\n{len(harness_update_plan.migrations)} migration(ões) de schema pendente(s) "
                    "— aplicar agora? [s/N] "
                )
                .strip()
                .lower()
            )
            confirm_migrations = migration_confirm == "s"

    project_name = target.name
    stack_summary = ", ".join(sorted(signals["keywords"])) or "(genérica)"
    counts = apply_plan(plan, target, canonical, project_name, stack_summary, mode, manifest)
    if harness_plan is not None and apply_harness_scaffold is not None:
        apply_harness_scaffold(target, project_name)
        print(".harness/ criado.")
    if harness_update_plan is not None and apply_harness_update is not None:
        update_result = apply_harness_update(
            target, project_name, confirm_migrations=confirm_migrations
        )
        print(f".harness/ atualizado: {update_result}.")
    print(f"\nFeito: {summarize(counts)}.")
    print("\nPróximos passos:")
    print("  1. /grill-with-docs — preencher CONTEXT.md com terminologia real do domínio")
    print("  2. /grill-me — refinar CLAUDE.md com invariantes específicos do projeto")
    print("  3. Revisar hooks em .claude/settings.json")
    print("  4. /validar — confirmar gate verde antes da primeira sessão de build")


if __name__ == "__main__":
    main()
