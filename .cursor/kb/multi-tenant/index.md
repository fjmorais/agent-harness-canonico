---
domain: multi-tenant
description: Padrões de isolamento multi-tenant — RLS, tenant_id, schema separation, pre-filter vetorial
mcp_validated: "2026-06-27"
confidence: 0.90
---

# KB: Multi-Tenant

Padrões de isolamento entre tenants em sistemas compartilhados.
Princípio central: **tenant isolation é infraestrutura, não lógica de aplicação** — o banco isola, a app não precisa lembrar.

## Conceitos

| Arquivo | Tópico |
|---|---|
| [isolation-models.md](concepts/isolation-models.md) | Shared DB vs Schema separation vs DB separation — quando cada um |
| [tenant-context.md](concepts/tenant-context.md) | Propagar tenant_id via JWT, header, contextvars — sem passar como parâmetro manual |

## Padrões

| Arquivo | Tópico |
|---|---|
| [rls-multi-tenant.md](patterns/rls-multi-tenant.md) | Políticas RLS + índices compostos por tenant_id |
| [vector-tenant-isolation.md](patterns/vector-tenant-isolation.md) | Pre-filter de tenant em Qdrant e pgvector |

## Quick Reference

### Modelos de isolamento

| Modelo | Isolamento | Custo | Quando |
|---|---|---|---|
| Shared schema + `tenant_id` | Médio (RLS) | Baixo | SaaS com muitos tenants pequenos |
| Schema separation | Alto | Médio | Compliance forte, poucos tenants |
| DB separation | Total | Alto | Enterprise, dados sensíveis, SLA individual |

### Invariantes

| # | Invariante |
|---|---|
| MT-01 | `tenant_id` como **primeiro** predicado em toda query — nunca como segundo |
| MT-02 | RLS habilitado em toda tabela com dados de tenant |
| MT-03 | Isolamento vetorial via **pre-filter**, nunca via semântica |
| MT-04 | `tenant_id` extraído do JWT/sessão no request — nunca confiado no body |
| MT-05 | Índice composto `(tenant_id, campo_filtro)` em toda tabela grande |

### Hierarquia de identidade

```
Usuário (user_id) → pertence a → Organização (org_id = tenant_id)
                                       ↓
                                 Dados da org (tenant_id = org_id)
```
