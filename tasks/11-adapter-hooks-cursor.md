# Adapter de hooks — Cursor (condicional ao spike)

**Status:** not started
**Blocked by:** 07-adapter-hooks-claude-code.md, 10-spike-viabilidade-cursor.md

## What to build

**Escopo definido pelo resultado da task 10.** Se o spike confirmar hooks equivalentes: replicar
o adapter da task 07 usando o mecanismo do Cursor, reaproveitando `harness_redact.py` (task 05)
e `write_event()` (task 06) sem duplicar lógica de negócio — só a camada de integração com o
Cursor muda. Se o spike concluir que não há hooks equivalentes: esta task se reduz a declarar
`capabilities.telemetry.cursor: "unavailable"` no manifest (task 03), com motivo registrado, e
não implementar adapter nenhum.

## Acceptance criteria

- [ ] Se viável: uma sessão real do Cursor gera `run.json`/`events/` no mesmo formato produzido
      pela task 07 — tested by: teste de integração equivalente ao da task 07, adaptado ao
      mecanismo do Cursor.
- [ ] Se inviável: `harness_doctor.py` (task 12) reporta `unavailable` para
      `telemetry.cursor` com motivo explícito, nunca `missing` nem zero silencioso — tested by:
      teste unitário do doctor contra um manifest com Cursor declarado `unavailable`.

## Notes

Não iniciar esta task sem o resultado da task 10 registrado. O escopo real só é conhecido depois
do spike.
