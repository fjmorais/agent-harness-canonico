from __future__ import annotations

from scripts.harness_redact import redact


def test_redact_masks_cpf_with_dots_and_dash() -> None:
    payload = {"payload": {"message": "meu CPF é 123.456.789-00, guarde"}}
    out = redact(payload)
    assert "123.456.789-00" not in out["payload"]["message"]
    assert "***.***.***-**" in out["payload"]["message"]


def test_redact_masks_email() -> None:
    payload = {"payload": {"message": "contato: fulano.silva@example.com por favor"}}
    out = redact(payload)
    assert "fulano.silva@example.com" not in out["payload"]["message"]
    assert "[EMAIL]" in out["payload"]["message"]


def test_redact_masks_user_home_path() -> None:
    payload = {"payload": {"cwd": "/home/fabiano/agent-harness-canonico/tests"}}
    out = redact(payload)
    assert "/home/fabiano" not in out["payload"]["cwd"]
    assert "[USER_PATH]/agent-harness-canonico/tests" == out["payload"]["cwd"]


def test_redact_masks_api_key_like_token() -> None:
    payload = {"payload": {"log": "usando token sk-ant-api03-abcdEFGH12345678901234567890"}}
    out = redact(payload)
    assert "sk-ant-api03-abcdEFGH12345678901234567890" not in out["payload"]["log"]
    assert "[SECRET]" in out["payload"]["log"]


def test_redact_preserves_non_sensitive_fields() -> None:
    payload = {
        "event_type": "tool.executed",
        "payload": {"tool": "pytest", "exit_code": 0, "duration_ms": 120},
    }
    out = redact(payload)
    assert out["event_type"] == "tool.executed"
    assert out["payload"]["tool"] == "pytest"
    assert out["payload"]["exit_code"] == 0
    assert out["payload"]["duration_ms"] == 120


def test_redact_is_idempotent() -> None:
    payload = {
        "payload": {
            "message": "CPF 123.456.789-00, email a@b.com, path /home/fabiano/x, "
            "token sk-ant-api03-abcdEFGH12345678901234567890"
        }
    }
    once = redact(payload)
    twice = redact(once)
    assert once == twice


def test_redact_does_not_mutate_input_payload() -> None:
    payload = {"payload": {"message": "CPF 123.456.789-00"}}
    redact(payload)
    assert payload["payload"]["message"] == "CPF 123.456.789-00"
