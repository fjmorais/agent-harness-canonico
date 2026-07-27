# Agent Harness Canônico

> O ambiente que governa como o Claude Code (e Cursor) agem no seu projeto: regras de
> comportamento, limites de segurança, agentes especializados, base de conhecimento, gates de
> qualidade e fluxo de desenvolvimento — configurado antes de escrever a primeira linha de código.

## O que é

Este repositório é o **framework** do Agent Harness Method — não um produto. É a fonte de
verdade de agents, skills, KBs e rules que são propagados para projetos alvo. Tem **dois modos
de uso**:

1. **Clonar como template** de um projeto novo → rodar `/harness-architect` no clone para
   especializar o `.claude/` ao domínio do projeto.
2. **Apontar como fonte** no `/install-harness` de um projeto já existente → o instalador
   detecta a stack e traz só os artefatos relevantes.

## Os 3 níveis de uso

Nem toda tarefa precisa do fluxo completo. O harness (via `/dev`, ver `DEV-LOOP.md`) reconhece
três níveis de estrutura, do menos ao mais formal:

| Nível | O quê | Comando | Tempo |
|---|---|---|---|
| 1 — Vibe coding | Só prompt solto, sem estrutura | (nenhum) | < 30 min |
| 2 — Dev Loop | `PROMPT.md` dirigido, verificação por exit code, recovery de sessão | `/dev` | 1-4 horas |
| 3 — Harness completo | 6 fases (ideia → retrospectiva), PRD, gate + revisor obrigatórios | `/novo-projeto` | multi-dia |

## Pré-requisitos

- [Claude Code CLI](https://claude.ai/code) instalado e autenticado (ou Cursor, via `.cursor/`)
- `git` disponível no PATH
- `python3` 3.11+ — o instalador (`install_harness.py`) usa só a standard library, sem `pip install`
- `uv` (Python) se o projeto de destino for Python
- `gh` (GitHub CLI) se quiser `/to-issues` com GitHub
- `npx` (Node.js) para o MCP Context-7

## Início rápido

### Modo 1 — clonar como template de projeto novo

```bash
git clone <este-repo> meu-projeto
cd meu-projeto

# Abra no Claude Code e inicie o fluxo guiado
/novo-projeto
```

Detalhe passo a passo em [COMO-USAR.md](COMO-USAR.md).

### Modo 2 — instalar/atualizar num projeto já existente

```bash
# a partir da raiz deste canônico, launcher guiado:
./install-harness

# ou dentro de uma sessão Claude Code, na pasta do projeto alvo:
/install-harness
```

O instalador detecta o estado do projeto (`NOVO` / `SEM_HARNESS` / `ATUALIZAÇÃO`), mapeia
artefatos pela stack detectada, mostra um Install Plan e só grava após confirmação. Guia
completo (flags, `--json`, automação) em [INSTALL-HARNESS-CLI.md](INSTALL-HARNESS-CLI.md).

## Fluxo de trabalho (nível 3 — harness completo)

```
/novo-projeto       → captura ideia + SI assessment + tipo de projeto (harness-brainstorm)
/grill-me           → entrevista implacável da ideia
harness-define      → estrutura requisitos + detecta especificações implícitas
                        (+ 10 perguntas de pipeline se necessário)
/to-prd              → gera PRD.md
harness-design       → dispara /harness-architect (gera harness específico do projeto)
/to-tasks             → fatia o PRD em tasks implementáveis
harness-build        → implementa task a task (gate `/validar` + `revisor-codigo` obrigatórios)
harness-ship          → scorecard + retrospectiva + fecha projeto
```

Guia de referência para quem já tem o harness instalado: [HARNESS-GUIDE.md](HARNESS-GUIDE.md).

## O que vem no canônico

| O que | Onde | Qtd |
|---|---|---|
| Agents | `.claude/agents/` | 27 — `workflow/` (6), `architect/` (5), `dev/` (6), `data-engineering/` (10) |
| Skills | `.claude/skills/` | 17 |
| Rules | `.claude/rules/` | 11 |
| KBs | `.claude/kb/` | 17 domínios |
| Commands | `.claude/commands/` | 18 (4 na raiz + `data-engineering/` + `visual-explainer/`) |
| Dev Loop | `.claude/dev/` | tasks/progress/logs/templates/examples — ver `DEV-LOOP.md` |

Catálogo completo com descrição por item: [`.claude/agents/README.md`](.claude/agents/README.md)
e [`.claude/commands/README.md`](.claude/commands/README.md).

## SI / Segurança (desde o clone zero)

- `.claude/settings.json` — deny list de operações destrutivas: `rm -rf`, `docker compose down -v`,
  `docker volume rm/prune`, `dropdb`, `databricks workspace/clusters delete`, `git push --force`,
  `git reset --hard`
- `.claude/rules/seguranca.md` (carrega em TODA sessão): LGPD, PII, somente leitura em produção
  por padrão, sem secrets hardcoded
- `.claude/rules/definicao-de-pronto.md` (carrega em TODA sessão): critérios de aceite testáveis,
  gate verde obrigatório, revisor aprovado, delivery record em `metrics/entregas.jsonl`
- Hooks automáticos: `ruff format/fix` a cada edição (`PostToolUse`), `ruff + mypy + pytest`
  ao encerrar sessão (`Stop`)

## MCP

Configurado em `.mcp.json`:

- **Context-7** (`@upstash/context7-mcp`): docs oficiais de bibliotecas externas em runtime
- **Postgres** (placeholder, `access-mode=restricted`): preencher a connection string após
  `/harness-architect` detectar o banco do projeto

## Estrutura do repositório

```
.
├── CLAUDE.md              ← guia do agente para evoluir este canônico
├── AGENTS.md               ← espelho de CLAUDE.md p/ ferramentas que leem esse padrão
├── HARNESS-GUIDE.md         ← guia de uso do harness já instalado
├── COMO-USAR.md              ← setup passo a passo do modo "clonar como template"
├── INSTALL-HARNESS-CLI.md     ← guia da CLI standalone de install/update
├── DEV-LOOP.md                 ← conceito do Dev Loop (nível 2)
├── install-harness               ← launcher bash do instalador
├── .mcp.json                      ← MCP servers (Context-7, Postgres)
├── docs/
│   ├── guia/                       ← 16 guias HTML do método
│   ├── adr/                         ← Architecture Decision Records
│   └── diagramas/
├── metrics/                          ← entregas.jsonl (alimenta /scorecard)
└── .claude/
    ├── settings.json                  ← permissões + hooks de gate (SI built-in)
    ├── rules/                          ← 11 rules (seguranca.md e definicao-de-pronto.md sempre carregam)
    ├── agents/                          ← 27 agents em 4 categorias
    ├── skills/                          ← 17 skills
    ├── commands/                         ← 18 commands (raiz + data-engineering/ + visual-explainer/)
    ├── kb/                                ← 17 domínios de conhecimento
    ├── dev/                                ← Dev Loop: tasks/progress/logs/templates/examples
    ├── design/                             ← features/, archive/, reports/
    └── projetos/                            ← histórico de fluxos /novo-projeto
```

`.cursor/` espelha a mesma estrutura para quem usa Cursor em vez de Claude Code.

## Guias HTML

Abra os guias em `docs/guia/` para aprender o método:

| Arquivo | Tema |
|---|---|
| `01-conceitos.html` | Vocabulário: skills, agents, KBs, gates |
| `02-fluxo.html` | O fluxo completo de fases |
| `03-harness.html` | Anatomia do `.claude/` — arquivo por arquivo |
| `04-tracking.html` | Como rastrear progresso (STATUS.md, HANDOFF, métricas) |
| `05-fluxo-guiado.html` | `/novo-projeto` — demo passo a passo |
| `06-seguranca.html` | SI/LGPD/PII — guardrails e exemplos reais |
| `07-pipeline-arquitetura.html` | Medallion, lineage, contratos, quarantine |
| `08-pipeline-praticas.html` | SOLID, config centralizada, Databricks, Airflow |
| `09-agentes-sdd.html` | Context-7, kb-architect, harness-* agents |
| `10-rag-search.html` | RAG e estratégias de busca |
| `10-workshop-harness-vs-sdd.html` | Workshop: harness vs. SDD |
| `11-langgraph.html` | LangGraph |
| `12-supabase.html` | Supabase |
| `13-observabilidade.html` | Observabilidade |
| `14-multi-tenant.html` | Multi-tenant |
| `15-testing.html` | Testing |
| `16-install-harness.html` | `/install-harness` |

## Guia de personalização

Veja [COMO-USAR.md](COMO-USAR.md) para instruções passo a passo de como personalizar este
template ao clonar, ou [INSTALL-HARNESS-CLI.md](INSTALL-HARNESS-CLI.md) para instalar/atualizar
o harness num projeto que já existe.
