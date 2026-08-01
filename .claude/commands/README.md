# Comandos — catálogo

Comandos são invocados explicitamente (`/nome`) — diferente de agents/skills, que são escolhidos
por match do `description:`. Esta pasta tem comandos genéricos do harness soltos na raiz, e duas
subpastas de vertical (`data-engineering/`, `visual-explainer/`) — ver "Raiz vs subpastas" abaixo.

## Raiz — workflow genérico do harness (5)

| Comando | Fase | O que faz | Agente que aciona |
|---|---|---|---|
| `/novo-projeto` | 0 — entrada | Fluxo guiado de criação de projeto: SI assessment, detecta tipo (app/pipeline/agente), checkpoints (`salvar-grill`, `salvar-prd`, `salvar-harness`, `salvar-tasks`, `shippar`) | `harness-brainstorm` (e os demais `harness-*` via subcomandos) |
| `/novo-guia` | 0 — entrada | Fluxo guiado de criação de guia passo-a-passo didático (qualquer assunto técnico): tema → escopo → roteiro → etapas → HTML final | `guia-brainstorm` (e os demais `guia-*` conforme a fase) |
| `/dev` | Qualquer — tarefa pontual de 1-4h | Dev Loop: PROMPT.md dirigido, verificação por exit code, recovery de sessão — ver `DEV-LOOP.md` na raiz | `prompt-crafter` (craft) / `dev-loop-executor` (execução) |
| `/validar` | Qualquer, antes de commit | Gate rápido: `ruff` + `mypy` + `pytest` | — (roda o gate direto, mesmo comando do hook de `Stop`) |
| `/scorecard` | Fechamento | Scorecard de entrega: correção, aderência ao padrão, throughput, autonomia | — (lê `git`/`gh`/`metrics/entregas.jsonl` direto, nunca inventa número) |

## `data-engineering/` (7)

| Comando | O que faz | Agente que aciona |
|---|---|---|
| `/pipeline` | Scaffolding de DAG (Airflow/Dagster) | `pipeline-architect` |
| `/schema` | Design de schema dimensional/Data Vault/SCD | `schema-designer` |
| `/data-quality` | Regras de qualidade (GE, Soda, testes dbt) | `data-quality-analyst` |
| `/lakehouse` | Table format e catálogo (Iceberg/Delta) | `lakehouse-architect` |
| `/sql-review` | Revisão de código focada em SQL | `revisor-codigo` + `sql-optimizer` |
| `/data-contract` | Autoria de contrato de dados (ODCS) | `data-contracts-engineer` |
| `/migrate` | Migração de ETL legado pra dbt/PySpark | `dbt-specialist` / `spark-engineer` |

## `visual-explainer/` (7)

Gera páginas HTML autocontidas — diagramas, slides, review visual de plano/diff. Não depende de
nenhum agente (aciona a skill `visual-explainer` direto). `/share` do agentspec **não** foi
trazido — dependia de um skill `vercel-deploy` que não existe em lugar nenhum.

| Comando | O que faz |
|---|---|
| `/generate-web-diagram` | Diagrama HTML standalone para qualquer tópico |
| `/generate-slides` | Slide deck em HTML, qualidade de revista |
| `/generate-visual-plan` | Plano de implementação visual (state machine, snippets, edge cases) |
| `/diff-review` | Review visual de diff — comparação antes/depois + code review |
| `/plan-review` | Compara plano proposto vs. codebase atual, com risk assessment |
| `/project-recap` | Reconstrói modelo mental do projeto — atividade recente, decisões, cognitive debt |
| `/fact-check` | Verifica exatidão factual de um documento contra o código real |

## Raiz vs subpastas

`data-engineering/` e `visual-explainer/` têm massa crítica (7 comandos cada) — cada uma virou
subpasta seguindo o mesmo critério do agentspec (Luan Moreno): comandos de um mesmo domínio
coeso agrupados juntos. Os comandos genéricos continuam soltos na raiz porque são workflow do
harness, não amarrados a uma vertical técnica — não crie subpasta pra menos de ~5 comandos
coesos.

## Adicionando um comando novo

Frontmatter mínimo: `description:` claro (é o que decide quando o comando aparece relevante).
Não precisa `name:` — o Claude Code usa o nome do arquivo. Espelhe sempre em
`.cursor/commands/{path}.md`.
