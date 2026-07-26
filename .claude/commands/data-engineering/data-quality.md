---
description: >-
  Geração de regras de qualidade de dados — Great Expectations, Soda, testes dbt.
  Aciona data-quality-analyst. Use quando: "adiciona validação nesse pipeline",
  "monta um dashboard de qualidade para X".
---

# /data-quality — checks de qualidade

Aciona o agente `data-quality-analyst`.

## Uso

```
/data-quality <dataset ou model>
```

## Exemplos

```
/data-quality models/staging/stg_pedidos.sql
/data-quality "monta um dashboard de freshness para os models de mart"
```

## O que acontece

1. `data-quality-analyst` identifica dimensões de qualidade relevantes (completude, unicidade, freshness, volume)
2. Consulta `.claude/kb/data-quality/` (JIT) — cross-linkado com `.claude/kb/pipeline/patterns/data-quality.md` já existente
3. Gera suite (Great Expectations/Soda/testes dbt) + queries de monitoramento
4. Escala para `dbt-specialist` (testes YAML) ou `data-contracts-engineer` (SLA formal) quando aplicável
