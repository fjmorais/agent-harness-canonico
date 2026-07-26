---
description: >-
  Orientação sobre table format e catálogo — Iceberg, Delta Lake, governança de lakehouse.
  Aciona lakehouse-architect. Use quando: "monta tabelas Iceberg com X", "Delta ou Iceberg?".
---

# /lakehouse — table format e catálogo

Aciona o agente `lakehouse-architect`.

## Uso

```
/lakehouse <descrição do caso>
```

## Exemplos

```
/lakehouse "configura tabelas Iceberg com partition evolution"
/lakehouse "devo usar Delta Lake ou Iceberg?"
```

## O que acontece

1. `lakehouse-architect` avalia ecossistema existente, requisitos de engine e necessidade de governança
2. Consulta `.claude/kb/lakehouse/` (JIT)
3. Entrega matriz de decisão ou DDL/config concreta
4. Escala para `data-platform-engineer` (provisionamento) ou `spark-engineer` (leitura/escrita) quando aplicável
