---
domain: fastapi
description: Padrões FastAPI — routers finos, service layer, dependency injection, error contracts, async
mcp_validated: "2026-06-27"
confidence: 0.93
---

# KB: FastAPI

Base de conhecimento de padrões FastAPI para APIs assíncronas, modulares e seguras.
Princípio central: **rota fina + service layer** — routers não contêm lógica de negócio.

## Conceitos

| Arquivo | Tópico |
|---|---|
| [router-vs-service.md](concepts/router-vs-service.md) | Separação de responsabilidades: rota declara, service executa |
| [dependency-injection.md](concepts/dependency-injection.md) | `Depends()` para DB, auth, config — sem global state |
| [async-patterns.md](concepts/async-patterns.md) | async/await, connection pools, background tasks |
| [error-contracts.md](concepts/error-contracts.md) | HTTPException padronizada, handlers globais, schema de erro |

## Padrões

| Arquivo | Tópico |
|---|---|
| [thin-router.md](patterns/thin-router.md) | Router com validação + 1 chamada de service — nada mais |
| [service-layer.md](patterns/service-layer.md) | Service com lógica de negócio, testável sem HTTP |
| [health-check.md](patterns/health-check.md) | /health com verificação de dependências (DB, cache, LLM) |
| [openapi-contract.md](patterns/openapi-contract.md) | Schemas Pydantic, tags, summary, responses declarados |

## Quick Reference

### Layout canônico

```
backend/
├── app/
│   ├── main.py              ← FastAPI() + include_router + lifespan
│   ├── routers/
│   │   ├── chat.py          ← router.post("/chat") → service.chat()
│   │   ├── health.py        ← router.get("/health")
│   │   └── __init__.py
│   ├── services/
│   │   ├── chat_service.py  ← lógica de negócio, sem HTTP
│   │   └── __init__.py
│   ├── schemas/
│   │   ├── chat.py          ← ChatRequest, ChatResponse (Pydantic)
│   │   └── error.py         ← ErrorResponse
│   └── deps.py              ← get_db(), get_current_user(), get_config()
```

### Invariantes

| # | Invariante |
|---|---|
| FA-01 | Router não contém lógica de negócio — apenas valida input, chama service, retorna output |
| FA-02 | Toda dependência (DB, auth, config) via `Depends()` — sem import global mutável |
| FA-03 | Sem PII em URL ou query params — usar body (POST) ou headers |
| FA-04 | Toda rota tem `response_model` declarado — sem `dict` como retorno |
| FA-05 | Error responses usam `ErrorResponse` schema padronizado — sem strings brutas |
| FA-06 | Connection pool criado no lifespan — nunca a cada request |

### Decision tree: quando async vs sync

```
A operação faz I/O? (DB, HTTP externo, arquivo)
    ├── SIM → async def + await
    │         ├── DB: asyncpg ou SQLAlchemy async
    │         └── HTTP: httpx.AsyncClient
    └── NÃO (só CPU) → def síncrono
                       (FastAPI roda em thread pool automaticamente)
```
