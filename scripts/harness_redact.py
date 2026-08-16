"""Redaction de PII/prompt/secret — única camada de mascaramento do design (task 05).

Usado exclusivamente pelo caminho de hook (telemetria objetiva). O caminho de agente não
precisa disso: seu schema é estruturalmente limitado a enums/booleans/contadores, sem texto
livre — ver docs/adr/001-observabilidade-harness-control.md, Opção I.
"""

from __future__ import annotations

import re
from copy import deepcopy

_CPF_RE = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_USER_HOME_RE = re.compile(r"/home/[^/\s]+")
# tokens/API keys: prefixos comuns (sk-, ghp_, xox, etc.) seguidos de corpo alfanumérico longo.
_SECRET_RE = re.compile(r"\b(?:sk-[a-zA-Z0-9-]{16,}|ghp_[a-zA-Z0-9]{16,}|xox[a-zA-Z0-9-]{16,})\b")


def _redact_text(value: str) -> str:
    value = _CPF_RE.sub("***.***.***-**", value)
    value = _EMAIL_RE.sub("[EMAIL]", value)
    value = _SECRET_RE.sub("[SECRET]", value)
    value = _USER_HOME_RE.sub("[USER_PATH]", value)
    return value


def _redact_value(value: object) -> object:
    if isinstance(value, str):
        return _redact_text(value)
    if isinstance(value, dict):
        return {k: _redact_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_value(v) for v in value]
    return value


def redact(payload: dict[str, object]) -> dict[str, object]:
    """Retorna uma cópia de `payload` com PII/prompt/secret mascarados em todo campo de texto.
    Não muta o `payload` original. Idempotente: redigir um payload já redigido não muda nada."""
    result = deepcopy(payload)
    return {k: _redact_value(v) for k, v in result.items()}
