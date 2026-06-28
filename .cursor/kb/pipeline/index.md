---
domain: pipeline
description: Conceitos e padrões de engenharia de dados — Medallion, contratos, lineage, schema evolution
mcp_validated: "2026-06-27"
confidence: 0.95
---

# KB: Pipeline de Dados

Base de conhecimento de engenharia de dados para projetos Medallion com boas práticas de
qualidade, lineagem, contratos e observabilidade.

## Conceitos

| Arquivo | Tópico |
|---|---|
| [medallion.md](concepts/medallion.md) | Arquitetura Raw→Bronze→Silver→Gold |
| [data-contracts.md](concepts/data-contracts.md) | ODCS-style YAML: schema + SLA + producer/consumer |
| [schema-evolution.md](concepts/schema-evolution.md) | mergeSchema vs quarantine vs fail |
| [data-lineage.md](concepts/data-lineage.md) | Colunas de lineage por camada, Unity Catalog lineage |
| [quarantine.md](concepts/quarantine.md) | Padrão de quarentena: tabela + notificação do owner |
| [observability.md](concepts/observability.md) | Structured logging, métricas por layer, alertas |

## Padrões

| Arquivo | Tópico |
|---|---|
| [solid-pipeline.md](patterns/solid-pipeline.md) | SOLID aplicado a pipelines de dados |
| [centralized-config.md](patterns/centralized-config.md) | PipelineConfig + environments/*.yaml |
| [notification.md](patterns/notification.md) | Webhook Slack/Teams/email para anomalias |
| [data-quality.md](patterns/data-quality.md) | DLT expectations vs Great Expectations vs dbt tests |

## Quick Reference

### Colunas obrigatórias por camada

| Camada | Colunas obrigatórias |
|---|---|
| Raw | `_source_file`, `_ingest_ts` |
| Bronze | `_ingested_at`, `_source`, `_run_id`, `_batch_id` |
| Silver | `_processed_at`, `_pipeline_version` |
| Gold | `_updated_at` |

### Estratégias de schema evolution

| Situação | Estratégia |
|---|---|
| Nova coluna opcional (não-breaking) | `mergeSchema` |
| Tipo mudou / coluna removida | `quarantine` + notificar owner |
| Violação de contrato de dados | `fail` |

### Decision tree: schema evolution

```
Schema detectado ≠ esperado?
    ├── Diferença é ADITIVA (nova coluna nullable)?
    │   └── strategy=merge? → mergeSchema → processa normalmente
    │   └── strategy=quarantine? → quarantine + notify
    ├── Diferença é POTENCIALMENTE BREAKING (tipo mudou, coluna sumiu)?
    │   └── quarantine + notify owner (sempre)
    └── Violação de contrato declarado?
        └── fail (lança exceção + log estruturado)
```
