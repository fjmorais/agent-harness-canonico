"""Validação de payloads contra os schemas publicados em schemas/*.schema.json."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"


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
