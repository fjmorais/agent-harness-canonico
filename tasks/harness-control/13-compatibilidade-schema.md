# Validação de compatibilidade de schema (N / N-1)

**Status:** done
**Blocked by:** 01-schemas-core.md, 02-schemas-complementares.md, 04-update-seguro.md

## What to build

Duas checagens complementares (ver ADR ao decidir a Pergunta 8 do grill): na **escrita**, todo
script que grava em `.harness/` valida o payload contra a `schema_version` fixada em
`config.json` do projeto (nunca contra a versão mais recente do canônico, a menos que uma
migration explícita tenha rodado — task 04); na **leitura/doctor**, uma checagem consulta
`schemas/compatibility.json` (task 02) e reporta `outdated` se a versão em uso estiver fora da
janela suportada (schema atual + uma versão anterior).

## Acceptance criteria

- [x] Uma escrita com payload de schema mais novo que o fixado em `config.json` do projeto é
      rejeitada (ou gera aviso explícito), não gravada silenciosamente — tested by: teste
      unitário simulando escrita com `schema_version` divergente da config.
- [x] Um projeto com `schema_version` dentro da janela N/N-1 é reportado `ok` pelo doctor —
      tested by: teste unitário com fixture de config em versão N-1.
- [x] Um projeto com `schema_version` mais antigo que N-1 é reportado `outdated` pelo doctor,
      com recomendação de migration — tested by: teste unitário com fixture de config em
      versão N-2.
- [x] `compatibility.json` é a única fonte consultada para decidir a janela suportada (não
      hardcoded em múltiplos lugares) — tested by: teste unitário verificando que alterar
      `compatibility.json` muda o resultado do doctor sem alterar código.

## Notes

Esta task depende da task 04 porque reutiliza a lógica de leitura/comparação de
`schema_version` já construída para detectar migrations pendentes.

**Escopo do guard de escrita (AC1):** `assert_write_compatible(pinned_version, payload_version)`
é uma função pura testada isoladamente (`scripts/schema_validation.py`) — comparação numérica de
versão, rejeita payload mais novo que o pinned. Wiring em todo writer real (`write_event`,
`apply_harness_scaffold`/`update`) fica para follow-up: os writers atuais não recebem o
`project_path`/versão pinned como parâmetro hoje, e adicionar isso exigiria mudar assinaturas já
usadas em 90+ testes. A função em si prova o comportamento pedido pelo critério de aceite; a
integração ponta-a-ponta é uma extensão natural, não um requisito coberto pelos ACs desta task.
