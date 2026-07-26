---
description: >-
  Design interativo de schema — dimensional, Data Vault, SCD. Aciona schema-designer.
  Use quando: "desenha um star schema para X", "como rastreio histórico de Y?".
---

# /schema — design de schema

Aciona o agente `schema-designer` para modelagem de dados analítica.

## Uso

```
/schema <descrição do caso de uso>
```

## Exemplos

```
/schema "star schema para analytics de e-commerce"
/schema "como rastrear histórico de endereço do cliente?"
```

## O que acontece

1. `schema-designer` define o grão antes de qualquer coisa (o que representa uma linha?)
2. Consulta `.claude/kb/data-modeling/` (JIT)
3. Entrega DDL + documentação do grão + trade-offs
4. Escala para `dbt-specialist` (implementação) ou `sql-optimizer` (estratégia de índice) quando aplicável
