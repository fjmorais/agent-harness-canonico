# Agent Harness Canônico

Template vazio pronto para clonar e iniciar qualquer projeto com o **Agent Harness Method**.

## O que é

O **Agent Harness** é o ambiente que governa como o Claude Code age no seu projeto:
regras de comportamento, limites de segurança, agentes especializados, base de conhecimento,
gates de qualidade e fluxo de desenvolvimento. Tudo configurado antes de escrever a primeira linha de código.

Este repositório é o **ponto de partida canônico**: contém o mínimo indispensável de SI, skills
de workflow e agentes de apoio. O restante (agentes de domínio, KBs específicas, rules de stack)
é gerado automaticamente pelo `/harness-architect` durante o fluxo de criação do projeto.

## Pré-requisitos

- [Claude Code CLI](https://claude.ai/code) instalado e autenticado
- `git` disponível no PATH
- `uv` (Python) se o projeto for Python
- `gh` (GitHub CLI) se quiser `/to-issues` com GitHub
- `npx` (Node.js) para o MCP Context-7

## Início rápido

```bash
# 1. Clone este template
git clone <este-repo> meu-projeto
cd meu-projeto

# 2. Copie o .env
cp .env.example .env
# Preencha com suas credenciais reais

# 3. Abra no Claude Code e inicie o fluxo guiado
# No terminal integrado ou na IDE, diga:
/novo-projeto
```

O `/novo-projeto` vai:
1. Perguntar qual ideia você quer construir
2. Fazer um assessment de Segurança da Informação (SI)
3. Detectar o tipo de projeto (app / pipeline local / pipeline cloud / outro)
4. Criar `.claude/projetos/{slug}/` com o checklist de fases

## Fluxo de desenvolvimento

```
/novo-projeto       → captura ideia + SI assessment + tipo de projeto
/grill-me           → entrevista implacável da ideia
harness-define      → estrutura requisitos (+ 10 perguntas de pipeline se necessário)
/to-prd             → gera PRD.md
/harness-architect  → gera harness específico do projeto (agents, rules, KBs, skills)
/to-tasks           → fatia o PRD em tasks implementáveis
harness-build       → implementa task a task (gate + revisor obrigatórios)
harness-ship        → scorecard + retrospectiva + fecha projeto
```

## O que já vem configurado

### SI / Segurança (desde o clone zero)

- `settings.json` com deny list de operações destrutivas (`rm -rf`, `docker volume rm`, `dropdb`, etc.)
- `rules/seguranca.md` (carrega em TODA sessão): LGPD, PII, somente leitura em produção, sem secrets hardcoded
- Hooks automáticos: ruff format/fix a cada edição, ruff+mypy+pytest ao encerrar sessão

### Skills de workflow (8)

`grill-me`, `grill-with-docs`, `handoff`, `harness-architect`, `to-issues`, `to-prd`, `to-tasks`, `write-a-skill`

### Agentes universais (9)

| Agente | Para quê |
|---|---|
| `revisor-codigo` | Revisão soft antes de commit/PR |
| `kb-architect` | Cria/atualiza KBs usando Context-7 MCP |
| `agent-creator` | Cria novos agentes via entrevista |
| `harness-brainstorm` | Ponto de entrada: ideia + SI + tipo |
| `harness-define` | Estrutura requisitos (pipeline-aware) |
| `harness-design` | PRD + dispara /harness-architect |
| `harness-build` | Implementa tasks com gates obrigatórios |
| `harness-ship` | Encerra com scorecard + retrospectiva |
| `harness-iterate` | Atualiza fase com cascata consciente |

### MCP

- **Context-7** (`@upstash/context7-mcp`): docs oficiais de bibliotecas externas em runtime
- **Postgres** (placeholder): preencher após `/harness-architect` configurar o banco

## Suporte a pipelines de dados

Quando o tipo de projeto for **pipeline de dados** (local com PySpark+Airflow ou cloud com
Databricks), o `/harness-architect` gera automaticamente:

- KBs em `.claude/kb/pipeline/` (Medallion, data contracts, lineage, schema evolution)
- Agentes: `pipeline-architect`, `schema-guardian`
- Rules: `pipeline.md`, `schema-evolution.md`, `observability.md`
- Skills: `create-pipeline`, `schema-evolution-check`
- Config: `config/environments/` + `config/pipeline_config.py`

Ver os guias HTML em `docs/guia/07-pipeline-arquitetura.html` e `08-pipeline-praticas.html`.

## Estrutura do `.claude/`

```
.claude/
├── settings.json           ← permissões + hooks de gate (SI built-in)
├── rules/
│   ├── seguranca.md        ← SI/LGPD (carrega SEMPRE — sem paths:)
│   ├── definicao-de-pronto.md ← DoD (carrega SEMPRE)
│   ├── agente.md           ← template (ativa em backend/agent/**)
│   ├── backend.md          ← ativa em backend/app/**
│   ├── frontend.md         ← ativa em frontend/**
│   ├── estilo-codigo.md    ← ativa em **/*.py
│   ├── testes.md           ← ativa em **/tests/**
│   └── pipeline.md         ← ativa em src/pipeline/** (se pipeline)
├── agents/                 ← 9 agentes universais
├── skills/                 ← 8 skills de workflow
├── commands/               ← /validar, /scorecard, /novo-projeto
├── kb/                     ← base de conhecimento (vazia — criada pelo workflow)
└── projetos/               ← histórico de fluxos de projeto
```

## Guias HTML

Abra os guias em `docs/guia/` para aprender o método:

| Arquivo | Conteúdo |
|---|---|
| `01-conceitos.html` | Vocabulário: skills, agents, KBs, gates |
| `02-fluxo.html` | O fluxo completo de 6 fases |
| `03-harness.html` | Anatomia do `.claude/` — arquivo por arquivo |
| `04-tracking.html` | Como rastrear progresso (STATUS.md, HANDOFF, métricas) |
| `05-fluxo-guiado.html` | `/novo-projeto` — demo passo a passo |
| `06-seguranca.html` | SI/LGPD/PII — guardrails e exemplos reais |
| `07-pipeline-arquitetura.html` | Medallion, lineage, contratos, quarantine |
| `08-pipeline-praticas.html` | SOLID, config centralizada, Databricks, Airflow |
| `09-agentes-sdd.html` | Context-7, kb-architect, harness-* agents |

## Guia de personalização

Veja [COMO-USAR.md](COMO-USAR.md) para instruções passo a passo de como personalizar este template.
