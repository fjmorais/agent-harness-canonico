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
