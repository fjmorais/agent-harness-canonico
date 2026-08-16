# Schemas core (execution-event, run, usage, project-state, workflow-state)

**Status:** done
**Blocked by:** none

## What to build

Os 5 schemas JSON Schema que formam a espinha dorsal da observabilidade: envelope de evento
(`execution-event`, incluindo `writer_id` para suportar reconstrução multi-arquivo), `run`
(estados `created → queued → running → waiting_approval → completed`, com ramificações
`paused`/`failed`/`cancelled`/`interrupted`/`recovering`), `usage` (`usage_by_model` como lista,
não campo único — necessário porque roteamento "auto" pode variar por turno/subagente),
`project-state` e `workflow-state`. Cada schema tem `schema_version` próprio, independente da
versão do harness. Publicados em `schemas/*.schema.json` na raiz do canônico.

Inclui também uma função de validação pura (ex.: `scripts/validate_schema.py` ou módulo
compartilhado) que recebe um payload + nome do schema e retorna válido/erros — usada tanto pelos
testes quanto, futuramente, pelo escritor de evento (task 06).

## Acceptance criteria

- [x] `schemas/execution-event.schema.json` valida o envelope completo (todos os campos do PRD,
      incluindo `writer_id`, `privacy`, `correlation_id`) — tested by: teste unitário com fixture
      de payload válido e inválido (campo faltando, tipo errado).
- [x] `schemas/run.schema.json` valida as transições de estado documentadas e rejeita transição
      inválida — tested by: teste unitário parametrizado com lista de transições válidas/inválidas.
- [x] `schemas/usage.schema.json` aceita `usage_by_model` com múltiplas entradas de modelo
      diferentes dentro do mesmo objeto de usage — tested by: teste unitário com fixture de 2+
      modelos no mesmo run.
- [x] `schemas/project-state.schema.json` e `schemas/workflow-state.schema.json` publicados e
      validados contra pelo menos um payload de exemplo cada — tested by: teste unitário por
      schema.
- [x] Todos os 5 schemas têm campo `schema_version` obrigatório — tested by: teste unitário que
      falha a validação se `schema_version` estiver ausente.

## Notes

Ver `docs/adr/001-observabilidade-harness-control.md` para o racional de `run` = sessão inteira
(não turno) e `usage_by_model` como lista. Este schema de `usage` já reflete a decisão do grill
(Pergunta 5): sem campo de preço em `$`, só tokens brutos.

**Decisão de escopo (revisor-codigo, 2026-08-16):** "transição de estado" neste critério de
aceite significa "o valor de `status` pertence ao enum documentado" (validação de snapshot),
não uma máquina de estados com histórico (`from_status -> to_status`). O PRD/ADR não define uma
tabela de transições explícita — só a lista de estados válidos e as ramificações possíveis. Uma
FSM completa (rejeitar `completed -> running`, por exemplo) fica fora do escopo desta task; se
for necessária, é uma extensão futura a registrar como nova task, não uma lacuna silenciosa
desta.
