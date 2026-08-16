# Agregação `usage.json` por modelo e correlação

**Status:** done
**Blocked by:** 06-escritor-evento-concorrente.md

## What to build

Função `aggregate_usage(run_dir: Path) -> dict` que lê a timeline reconstruída
(`rebuild_timeline()`, task 06) de um run, agrupa os eventos de uso de token por
`(correlation_id, model_id)`, e grava `usage.json` no formato `usage_by_model: [{model_id,
correlation_id, input, output, cache_read, cache_write, reasoning}]` — permitindo responder
"quanto essa task consumiu, por modelo" mesmo com roteamento "auto" variando dentro da mesma
sessão.

## Acceptance criteria

- [x] Eventos de uso de dois modelos diferentes dentro do mesmo run são agregados em entradas
      separadas de `usage_by_model` — tested by: teste unitário com fixture de timeline
      contendo eventos de 2 `model_id` distintos.
- [x] Eventos do mesmo modelo mas `correlation_id` diferentes (duas tasks na mesma sessão) são
      agregados separadamente — tested by: teste unitário com fixture de 2 `correlation_id`.
- [x] Tokens de input/output/cache/reasoning são somados corretamente por grupo — tested by:
      teste unitário com valores conhecidos, validando a soma.
- [x] Nenhum cálculo de custo em `$` aparece no `usage.json` gerado — tested by: teste unitário
      verificando que o schema de saída não contém campo de preço (reforça ADR-001, Opção G).

## Notes

Consumir sempre via `rebuild_timeline()` (task 06), nunca ler os arquivos de escritor
diretamente — evita duplicar a lógica de mesclagem/ordenação.

**Contrato produtor/consumidor (revisor-codigo, 2026-08-16):** esta task define a convenção
`event_type == "usage.recorded"` com payload `{model_id, input, output, cache_read,
cache_write, reasoning}`, mas **nenhum código do repositório hoje emite esse evento** — o
`harness_hook.py` (task 07) só emite `tool.executed` e `subagent.completed`. `aggregate_usage()`
está correto e testado, mas em qualquer run real hoje sempre cai no bucket vazio `"model_id":
"none"`. O Claude Code expõe uso de token via hooks (`PostToolUse`/transcript) — conectar essa
ponta (emitir `usage.recorded` de fato) fica como trabalho futuro, fora do escopo das 15 tasks
originais deste projeto; registrar como item de acompanhamento antes do ship.
