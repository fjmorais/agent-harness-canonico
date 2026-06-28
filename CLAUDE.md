# [NOME_DO_PROJETO] · guia do agente

> Responde: "o que vale para o projeto inteiro?" — carregado em toda sessão.
> Índice de fatos duráveis, não documentação. Regras por área ficam em `.claude/rules/`.
>
> **Para o mantenedor:** substitua todos os `[PLACEHOLDERS]` antes de começar.
> Após o `/harness-architect`, preencha as seções de Stack, KB Map e Invariantes com
> os valores reais. Mantenha curto — este arquivo é lido em TODA sessão.

## Projeto ativo

Projeto em andamento (se houver):

```
cat .claude/projetos/{slug}/STATUS.md
```

## Stack

> Substitua após o /harness-architect

- **Backend**: [STACK_BACKEND] (ex: FastAPI + Python 3.13 + uv)
- **Frontend**: [STACK_FRONTEND] (ex: React + Vite) ou N/A
- **Banco de dados**: [STACK_DB] (ex: Postgres schema `negocio` + `harness`)
- **IA/Agente**: [STACK_IA] (ex: LangGraph, OpenAI GPT-4o) ou N/A
- **Pipeline**: [STACK_PIPELINE] (ex: PySpark local / Databricks) ou N/A
- **Infra**: [STACK_INFRA] (ex: nginx, Docker Compose, MinIO)

## Comandos

```bash
# Subir tudo:
[COMANDO_START]     # ex: docker compose up -d

# Testar:
[COMANDO_TEST]      # ex: uv run pytest -q

# Gate de validação (rápido):
/validar            # ruff + mypy + pytest — ou rode manualmente

# Revisar antes de commit/PR (soft):
revisor-codigo      # subagente de revisão

# Medir entrega:
/scorecard
```

## Segurança da Informação (invariantes — nunca flexibilizar)

- **[SI-01]** Dados de produção: SOMENTE LEITURA. Escrita só com aprovação humana explícita + ADR documentado em `docs/adr/`.
- **[SI-02]** PII (CPF, email, nome, dados financeiros/médicos): nunca logar, nunca exibir em output sem mascaramento, nunca expor em URL query string.
- **[SI-03]** Secrets: nunca hardcoded — mesmo em desenvolvimento. Sempre via `.env` / secret manager.
- **[SI-LGPD]** Este projeto [lida / não lida] com dados pessoais. Propósito declarado: [PROPÓSITO_LGPD].
- **[SI-DESTRUIÇÃO]** `rm -rf`, `docker volume rm`, `dropdb`, `DELETE/DROP` em produção: bloqueados nos hooks. Qualquer escrita destrutiva requer ADR.

> Nível de risco SI capturado no onboarding: [a|b|c|d] — ver `.claude/projetos/{slug}/00-ideia.md`

## Invariantes de produto (nunca quebrar)

> Preencha após o /harness-architect com os invariantes reais do seu domínio.
> Exemplos abaixo — substitua pelos seus.

- [INV-01] [Ex: Toda query ao schema `negocio` é SOMENTE LEITURA — role RO, LIMIT, timeout]
- [INV-02] [Ex: Runtime puro — nenhuma ingestão/carga no backend/]
- [INV-03] [Ex: Grafo LangGraph determinístico — LLM decide só dentro de nós]
- [INV-04] [Ex: Toda prescrição amarrada a uma fonte recuperada — sem grounding = falha]

## Knowledge Base Map

> Preenchido pelo /harness-architect durante o workflow. KBs residem em `.claude/kb/`.

| Domínio / Tecnologia | KB local | MCP externo |
|---|---|---|
| [Ex: Pipeline Medallion] | `.claude/kb/pipeline/` | Context-7 |
| [Ex: Databricks] | `.claude/kb/databricks/` | Context-7 |
| [Ex: FastAPI] | `.claude/kb/fastapi/` | Context-7 |

## Onde fica o quê

- **Regras por área** (carregam só ao tocar a área): `.claude/rules/`
- **Agentes**: `.claude/agents/` — universais (harness-*) + domínio (gerados pelo /harness-architect)
- **Comandos**: `.claude/commands/` — `/validar`, `/scorecard`, `/novo-projeto`
- **Skills**: `.claude/skills/` — workflow (grill, prd, tasks) + domínio
- **KBs**: `.claude/kb/` — criados pelo `kb-architect` ou copiados durante o workflow
- **Hooks e permissões**: `.claude/settings.json`
- **MCP (infra)**: `.mcp.json` — preencher com conexões reais
- **Fluxo de projeto**: `.claude/projetos/{slug}/` — STATUS.md + fases 00→05
- **Métricas de entrega**: `metrics/entregas.jsonl` (1 linha por task) — `/scorecard` consome
- **Decisões e porquês**: `docs/adr/`
- **Handoff de sessão**: `HANDOFF.md` (criado pelo `/handoff` ao encerrar sessão)
- **Definição de Pronto**: `.claude/rules/definicao-de-pronto.md`

## Layout do código (preencher após /harness-architect)

> Descreva a estrutura de diretórios do seu produto aqui.
> Exemplo (FastAPI + LangGraph):

```
[LAYOUT_DO_CODIGO]

# Ex:
# backend/app/    → routers finos + services/
# backend/agent/  → grafo, nós, tools, state
# backend/tests/  → pytest
# frontend/       → React + Vite (se houver)
# src/pipeline/   → pipeline Medallion (se houver)
# dags/           → DAGs Airflow (se houver)
```
