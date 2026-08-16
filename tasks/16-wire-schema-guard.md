# Wireear assert_write_compatible nos writers reais

**Status:** not started
**Blocked by:** 13-compatibilidade-schema.md

## What to build

A task 13 criou `assert_write_compatible()`/`is_schema_version_newer()`
(`scripts/schema_validation.py`) — função pura testada isoladamente, mas **nenhum writer real a
chama hoje**: `write_event()` (`harness_event_writer.py`), `apply_harness_scaffold()`/
`apply_harness_update()` (`harness_scaffold.py`) continuam gravando sem checar a versão pinned
do projeto. Um payload com `schema_version` mais nova que o pinned ainda é gravado
silenciosamente, exatamente como antes da task 13 — o guard existe mas não protege nada em
produção.

Esta task fecha essa lacuna: passar `project_path`/versão pinned para os writers reais e chamar
`assert_write_compatible()` antes de cada escrita, decidindo o que fazer com a exceção em cada
ponto de chamada (hook engolindo com a barreira já existente em `harness_hook.py:main()`? ou
propagando pro caller explicitamente em chamadas diretas de biblioteca?).

## Acceptance criteria

- [ ] `write_event()` rejeita um evento com `schema_version` mais nova que a versão pinned do
      projeto, sem gravar — tested by: teste de integração com fixture de projeto + evento
      divergente.
- [ ] `apply_harness_scaffold()`/`apply_harness_update()` aplicam o mesmo guard antes de gravar
      `config.json`/`state/project.json` — tested by: teste unitário equivalente.
- [ ] Assinaturas mudadas não quebram nenhum dos ~110 testes existentes que já chamam esses
      writers — tested by: suíte completa (`uv run pytest -q`) permanece verde.
- [ ] `harness_hook.py` continua nunca propagando exceção pro Claude Code (barreira do `main()`
      já existente cobre o novo caminho de erro) — tested by: teste de integração com payload de
      schema divergente via stdin, confirmando exit 0 + log em stderr.

## Notes

Levantada como ressalva pelo revisor-codigo na revisão da task 13 (2026-08-16): "a proteção
continua inexistente na prática... isso deveria ganhar rastreamento formal". Ver
`tasks/13-compatibilidade-schema.md` § Notes para o racional original de por que o wiring foi
adiado (mudar assinatura de writer usado em 90+ testes exigia planejamento, não encaixava no
ritmo da execução sequencial das tasks 01-15).
