---
domain: supabase
description: Supabase — Auth, RLS, Edge Functions, pgvector, storage e realtime para projetos full-stack
mcp_validated: "2026-06-27"
confidence: 0.91
---

# KB: Supabase

Base de conhecimento de padrões Supabase para autenticação, segurança por linha, funções serverless e busca vetorial.
Princípio central: **RLS é a última linha de defesa, não a única** — nunca expor dados sem política RLS ativa.

## Conceitos

| Arquivo | Tópico |
|---|---|
| [auth.md](concepts/auth.md) | Autenticação — magic link, OAuth, JWT, sessão no cliente |
| [rls.md](concepts/rls.md) | Row Level Security — políticas, `auth.uid()`, multi-tenant |
| [edge-functions.md](concepts/edge-functions.md) | Deno serverless — quando usar, padrões, segredos, CORS |
| [pgvector.md](concepts/pgvector.md) | RAG sobre Postgres — `vector`, HNSW index, `match_documents()` |

## Padrões

| Arquivo | Tópico |
|---|---|
| [rls-patterns.md](patterns/rls-patterns.md) | Políticas prontas para uso — owner, org, admin, public |
| [realtime-patterns.md](patterns/realtime-patterns.md) | Subscriptions Realtime — channel, filter, presença |

## Quick Reference

### Invariantes

| # | Invariante |
|---|---|
| SB-01 | RLS **habilitado em toda tabela** com dados de usuário — sem exceção |
| SB-02 | Nunca usar `service_role` key no frontend — apenas no servidor |
| SB-03 | JWT verificado antes de qualquer operação em Edge Function |
| SB-04 | pgvector com pre-filter de `user_id` antes da busca semântica |
| SB-05 | `SECURITY DEFINER` em funções SQL apenas quando documentado — risco de bypass RLS |

### Clientes: `anon` vs `service_role`

| Cliente | Onde usar | Respeita RLS |
|---|---|---|
| `anon` key | Frontend / mobile | ✅ Sim |
| `service_role` key | Backend servidor / Edge Functions com cuidado | ❌ Não (bypass total) |

### Setup mínimo no cliente

```typescript
import { createClient } from "@supabase/supabase-js"

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,  // anon key no frontend
)
```
