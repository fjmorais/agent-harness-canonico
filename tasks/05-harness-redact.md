# `harness_redact.py` — redaction de PII/prompt/secret

**Status:** not started
**Blocked by:** 01-schemas-core.md

## What to build

Script/módulo `scripts/harness_redact.py` com uma função pura `redact(payload: dict) -> dict`
que mascara PII (CPF, email, telefone, paths de usuário), prompts de texto livre e secrets
conhecidos (padrões de API key, token) em um payload de evento, antes de qualquer escrita em
`.harness/`. Usado exclusivamente pelo caminho de hook (não pelo caminho de agente, que é
estruturalmente limitado a campos sem texto livre — ver ADR-001, Opção I).

## Acceptance criteria

- [ ] `redact()` mascara CPF em qualquer campo de texto do payload (ex.: `123.456.789-00` vira
      `***.***.***-**`) — tested by: teste unitário com fixture de payload contendo CPF.
- [ ] `redact()` mascara email — tested by: teste unitário com fixture contendo email.
- [ ] `redact()` mascara path de usuário (ex.: `/home/<user>/...`) — tested by: teste unitário
      com fixture de path absoluto.
- [ ] `redact()` mascara padrões conhecidos de API key/token (ex.: prefixos comuns de secret) —
      tested by: teste unitário com fixture de string parecida com token.
- [ ] `redact()` preserva campos não sensíveis do payload inalterados (não mascara demais) —
      tested by: teste unitário verificando que campos como `event_type`, `tool`, `exit_code`
      permanecem idênticos após redaction.
- [ ] `redact()` é idempotente (rodar duas vezes no mesmo payload já redigido não muda o
      resultado) — tested by: teste unitário chamando `redact(redact(payload))` e comparando.

## Notes

Esta é a única camada de redaction do design (ADR-001) — o caminho de agente não passa por
aqui porque seu schema não permite texto livre. Não criar uma segunda implementação de
redaction em outro lugar.
