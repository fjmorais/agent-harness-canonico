---
domain: observabilidade
description: Observabilidade para agentes LLM e pipelines — Langfuse traces, structured logging, métricas por camada
mcp_validated: "2026-06-27"
confidence: 0.90
---

# KB: Observabilidade

Base de conhecimento para observar, medir e depurar agentes LLM e pipelines de dados.
Princípio central: **trace cada run LLM + log estruturado em cada camada** — sem isso, debugging é cego.

## Conceitos

| Arquivo | Tópico |
|---|---|
| [langfuse-traces.md](concepts/langfuse-traces.md) | Traces, spans, scores e datasets no Langfuse |
| [structured-logging.md](concepts/structured-logging.md) | Logging estruturado com structlog — campos obrigatórios por camada |
| [metrics-by-layer.md](concepts/metrics-by-layer.md) | Métricas por camada: latência, custo, taxa de erro, qualidade |

## Padrões

| Arquivo | Tópico |
|---|---|
| [trace-llm-call.md](patterns/trace-llm-call.md) | Instrumentar chamadas LLM com Langfuse SDK |
| [alert-thresholds.md](patterns/alert-thresholds.md) | Thresholds de alerta por métrica — latência, custo, qualidade |

## Quick Reference

### Stack de observabilidade

```
Agente LLM  →  Langfuse (traces + scores + datasets)
Pipeline    →  structured logging (structlog) + métricas customizadas
Infra       →  docker stats, healthcheck endpoints
```

### Campos obrigatórios em todo log

```python
log.info("evento", **{
    "session_id": session_id,
    "user_id":    user_id,
    "latency_ms": elapsed_ms,
    "component":  "chat_service",
})
```

### Níveis de log por situação

| Situação | Nível |
|---|---|
| Request recebido / processado | `info` |
| Resultado inesperado (mas não erro) | `warning` |
| Exceção capturada e tratada | `error` |
| Erro não recuperável / bug | `critical` |
| Debug de desenvolvimento | `debug` (desativar em produção) |

### Invariantes

| # | Invariante |
|---|---|
| OBS-01 | Toda chamada LLM tem trace no Langfuse (session_id, input, output, latência, custo) |
| OBS-02 | Nunca logar PII (CPF, email, dados financeiros) — mascarar antes do log |
| OBS-03 | `session_id` presente em todo log e trace — peça de rastreamento |
| OBS-04 | Scores de qualidade (grounding, relevância) gravados após avaliação humana ou automática |
| OBS-05 | Alertas configurados para: latência p95 > 10s, custo/dia > threshold, error_rate > 5% |
