# Agentes — organização por categoria

Roteamento é só o campo `description:` do frontmatter de cada agente — Claude Code (ou Cursor)
faz o match sem precisar ler o corpo do arquivo. Esta pasta existe para navegação humana e para
`agent-creator` saber onde salvar um agente novo; não é lida por inteiro em runtime.

## `workflow/` — fases do ciclo de vida de um projeto (Agent Harness Method)

| Agente | Quando |
|---|---|
| `harness-brainstorm` | Captura ideia inicial, SI assessment, tipo de projeto |
| `harness-define` | Estrutura requisitos a partir do `/grill-me` |
| `harness-design` | Gera PRD e monta o `.claude/` via `/harness-architect` |
| `harness-build` | Executa tasks com gate (`/validar`) + `revisor-codigo` |
| `harness-iterate` | Atualiza artefato de fase específica com cascata consciente |
| `harness-ship` | Fecha projeto: `/scorecard`, retrospectiva, `STATUS.md` |
| `guia-brainstorm` | Captura tema, material-fonte e tipo de guia passo-a-passo (`/novo-guia`) |
| `guia-escopo` | Estrutura objetivos, pré-requisitos, glossário e jornada pedagógica |
| `guia-roteiro` | Desenha os blocos do guia (contextualização/prep/implementação/validação/apêndices) |
| `guia-etapas` | Escreve cada bloco (contexto → conceito → código → validação → critério de aceite) |
| `guia-publish` | Gera o HTML final do guia, delegando à skill `visual-explainer` |
| `guia-iterate` | Atualiza artefato de fase do guia com cascata consciente |

## `architect/` — decisão de design antes do código

| Agente | Quando |
|---|---|
| `agent-creator` | Desenha e cria novos agentes via entrevista |
| `kb-architect` | Cria/audita domínios KB em `.claude/kb/` |
| `rag-architect` | Projeta sistemas de retrieval (RAG, LEDGER, híbrido) |
| `sql-architect` | Projeta queries SQL seguras e eficientes |
| `search-strategy-advisor` | Decide vetor vs SQL vs híbrido para um dado |

## `dev/` — apoio ao dia a dia de codificação

| Agente | Quando |
|---|---|
| `codebase-explorer` | Mapeia repositório desconhecido — Executive Summary + Deep Dive |
| `meeting-analyst` | Transforma notas de reunião em decisões/action items |
| `prompt-engineer` | Projeta e otimiza prompts de produção |
| `revisor-codigo` | Revisa diff antes de commit/PR |
| `prompt-crafter` | Constrói `PROMPT.md` do Dev Loop via entrevista (ver `DEV-LOOP.md` na raiz) |
| `dev-loop-executor` | Executa `PROMPT.md` do Dev Loop com loop de verificação e recovery |

## `data-engineering/` — engenharia de dados (pipelines, schema, qualidade, SQL, lakehouse)

Vertical adicionada a partir de uma avaliação do agentspec (Luan Moreno) — adaptada ao padrão
deste harness (sem tier/kb_domains/confidence scoring), não copiada ao pé da letra. Ver
`.claude/commands/data-engineering/` para os comandos que acionam cada um.

| Agente | Quando |
|---|---|
| `pipeline-architect` | Design de DAG — Airflow/Dagster, orquestração |
| `schema-designer` | Modelagem dimensional, Data Vault, SCD |
| `lakehouse-architect` | Table format (Iceberg/Delta) e catálogo |
| `data-platform-engineer` | Comparação/custo de Snowflake, Databricks, BigQuery |
| `dbt-specialist` | Models, testes, macros dbt |
| `spark-engineer` | Jobs PySpark, otimização de performance |
| `sql-optimizer` | Otimização de query existente (query plan, dialeto) |
| `streaming-engineer` | Kafka, Flink, CDC, stream processing |
| `data-contracts-engineer` | Contratos ODCS, SLA, governança de schema |
| `data-quality-analyst` | Great Expectations, Soda, testes dbt, observabilidade |

## Adicionando um agente novo

Use `agent-creator` (ele já sabe pedir a categoria). Se nenhuma categoria existente encaixa,
crie uma nova subpasta — nunca solte um `.md` direto em `.claude/agents/` sem categoria.
Espelhe sempre em `.cursor/agents/{categoria}/{nome}.md`.
