# Tasks — Harness Control (observabilidade do canônico)

Instrumentar o Agent Harness Canônico com uma camada `.harness/` observável por projeto
instalado (schemas versionados, eventos, telemetria, doctor de saúde, retenção), sem introduzir
código de produto/web no repositório. Ver `PRD.md` e `docs/adr/001-observabilidade-harness-control.md`.

| # | Título | Status | Blocked by |
|---|---|---|---|
| [01](01-schemas-core.md) | Schemas core (execution-event, run, usage, project-state, workflow-state) | done | none |
| [02](02-schemas-complementares.md) | Schemas complementares (manifest, config, run-result, delivery-record, compatibility) | done | none |
| [03](03-scaffold-projeto-novo.md) | Scaffold `.harness/` para projeto novo | done | 01, 02 |
| [04](04-update-seguro.md) | Update seguro de `.harness/` existente | done | 03 |
| [05](05-harness-redact.md) | `harness_redact.py` — redaction PII/prompt/secret | done | 01 |
| [06](06-escritor-evento-concorrente.md) | Escritor de evento concorrente + reconstrução de timeline | done | 01 |
| [07](07-adapter-hooks-claude-code.md) | Adapter de hooks — Claude Code | done | 03, 05, 06 |
| [08](08-agregacao-usage.md) | Agregação `usage.json` por modelo e correlação | done | 06 |
| [09](09-adapter-deliveries.md) | Adapter `deliveries/` — derivação de `metrics/entregas.jsonl` | done | 03 |
| [10](10-spike-viabilidade-cursor.md) | Spike: viabilidade de hooks equivalentes no Cursor | done | none |
| [11](11-adapter-hooks-cursor.md) | Adapter de hooks — Cursor (viável, ver ADR-002) | not started | 07, 10 |
| [12](12-harness-doctor.md) | `harness_doctor.py` — diagnóstico honesto por capability | done | 03, 04 |
| [13](13-compatibilidade-schema.md) | Validação de compatibilidade de schema (N / N-1) | done | 01, 02, 04 |
| [14](14-harness-prune.md) | `harness_prune.py` — retenção manual confirmada | done | 03 |
| [15](15-suite-fixtures-completa.md) | Suíte de fixtures completa (cenários de compatibilidade) | not started | 03, 04, 07, 12, 14 |
| [16](16-wire-schema-guard.md) | Wireear assert_write_compatible nos writers reais | not started | 13 |

## Fases

- **C0 — Contratos:** 01, 02 (bloqueiam tudo abaixo)
- **C1 — Instalador observável:** 03, 04
- **C2 — Telemetria:** 05, 06, 07, 08, 09, 10, 11
- **C3 — Compatibilidade:** 12, 13, 14, 15
