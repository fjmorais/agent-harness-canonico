# Schemas complementares (manifest, config, run-result, delivery-record, compatibility)

**Status:** not started
**Blocked by:** none

## What to build

Os 5 schemas restantes do plano: `harness-manifest` v2 (com `capabilities` granular por
executor — `telemetry.claude_code`, `telemetry.cursor`, não um booleano global — refletindo a
decisão do grill de reportar honestamente por executor), `harness-config` (inclui
`retention.days`, `telemetry.capture_prompts`, `telemetry.capture_tool_details`), `run-result`
(exit code, tasks, gate, review, intervenções, erro resumido), `delivery-record` (schema de
tradução de `metrics/entregas.jsonl`, não formato paralelo — ver ADR-001), `compatibility` (janela
de versões suportadas, N e N-1).

## Acceptance criteria

- [ ] `schemas/harness-manifest.schema.json` v2 aceita `capabilities` com granularidade por
      executor (ex.: `{"telemetry": {"claude_code": true, "cursor": "unavailable"}}`) — tested
      by: teste unitário com fixture de manifest multi-executor.
- [ ] `schemas/harness-config.schema.json` valida `retention.days` como inteiro positivo e
      `telemetry.capture_prompts`/`capture_tool_details` como booleanos — tested by: teste
      unitário com payload válido e um com tipo errado.
- [ ] `schemas/run-result.schema.json` publicado e validado contra um payload de exemplo —
      tested by: teste unitário.
- [ ] `schemas/delivery-record.schema.json` mapeia 1:1 os campos já existentes em
      `metrics/entregas.jsonl` (ver `metrics/README.md`) mais os campos de correlação
      (`project_id`, `run_id`) — tested by: teste unitário que valida uma linha real de
      `metrics/entregas.jsonl` (se existir) ou uma fixture equivalente contra o schema.
- [ ] `schemas/compatibility.json` declara a política N/N-1 de forma que um script consiga ler
      programaticamente "quais versões são suportadas para o schema X" — tested by: teste
      unitário que consulta o compatibility.json para 2+ schemas.

## Notes

`cost-entry.schema.json`, previsto no plano original, foi removido do escopo — ver ADR-001,
Opção G. Não criar esse arquivo.
