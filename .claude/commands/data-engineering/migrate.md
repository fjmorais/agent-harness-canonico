---
description: >-
  Migração de ETL legado — stored procedure para dbt, script batch para PySpark. Aciona
  dbt-specialist e/ou spark-engineer. Use quando: "migra essa stored procedure pra dbt",
  "converte esse ETL legado pra PySpark".
---

# /migrate — migração de ETL legado

Aciona `dbt-specialist` (transformação SQL) e/ou `spark-engineer` (ETL pesado), com
`pipeline-architect` para orquestração se a migração incluir o scheduler.

## Uso

```
/migrate <path do ETL legado>
```

## Exemplos

```
/migrate legacy/etl_pedidos_proc.sql
/migrate "converte esse job SSIS de agregação diária pra PySpark"
```

## O que acontece

1. Lê o ETL legado e mapeia lógica de transformação, dependências e schedule
2. Stored procedure/SQL → `dbt-specialist` (model + testes); ETL pesado/batch → `spark-engineer`
3. Se havia orquestração (cron, SSIS, scheduler proprietário) → `pipeline-architect` desenha a DAG equivalente
4. `sql-optimizer` revisa a query traduzida se o dialeto mudou
