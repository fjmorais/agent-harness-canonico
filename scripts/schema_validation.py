"""Validação de payloads contra os schemas publicados em schemas/*.schema.json."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"
COMPATIBILITY_PATH = SCHEMAS_DIR / "compatibility.json"


def _load_schema(schema_name: str) -> dict[str, object]:
    schema_path = SCHEMAS_DIR / f"{schema_name}.schema.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"schema não encontrado: {schema_path}")
    schema: dict[str, object] = json.loads(schema_path.read_text())
    return schema


def validate(payload: dict[str, object], schema_name: str) -> tuple[bool, list[str]]:
    """Valida `payload` contra `schemas/<schema_name>.schema.json`.

    Retorna (True, []) se válido, ou (False, [mensagens de erro]) se inválido.
    """
    schema = _load_schema(schema_name)
    validator = jsonschema.Draft202012Validator(schema)
    errors = [error.message for error in validator.iter_errors(payload)]
    return (len(errors) == 0, errors)


def load_compatibility() -> dict[str, object]:
    """Lê schemas/compatibility.json — política de versões suportadas por schema."""
    data: dict[str, object] = json.loads(COMPATIBILITY_PATH.read_text())
    return data


def current_version(schema_name: str) -> str:
    """Retorna a versão atual (mais recente) publicada para `schema_name`."""
    compatibility = load_compatibility()
    schemas = compatibility["schemas"]
    assert isinstance(schemas, dict)
    entry = schemas[schema_name]
    assert isinstance(entry, dict)
    return str(entry["current"])


def supported_versions(schema_name: str) -> list[str]:
    """Retorna a lista de versões suportadas (schema atual + N-1) para `schema_name`."""
    compatibility = load_compatibility()
    schemas = compatibility["schemas"]
    assert isinstance(schemas, dict)
    entry = schemas[schema_name]
    assert isinstance(entry, dict)
    supported = entry["supported"]
    assert isinstance(supported, list)
    return [str(version) for version in supported]


def _version_parts(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def is_schema_version_newer(a: str, b: str) -> bool:
    """True se a versão `a` for mais nova que `b` (comparação numérica: '1.10' > '1.9')."""
    return _version_parts(a) > _version_parts(b)


def assert_write_compatible(pinned_version: str, payload_version: str) -> None:
    """Rejeita escrita cujo payload declara uma `schema_version` mais nova que a versão fixada
    no projeto — nunca grava silenciosamente algo à frente do que o projeto sabe interpretar.
    Migration explícita (task 04) é o único jeito de avançar a versão fixada."""
    if is_schema_version_newer(payload_version, pinned_version):
        raise ValueError(
            f"escrita rejeitada: schema_version do payload ({payload_version}) é mais nova que "
            f"a versão fixada no projeto ({pinned_version}) — rode uma migration antes de escrever"
        )
