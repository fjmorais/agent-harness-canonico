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

## Mapa de escalação

Não existe um arquivo central de "router" — cada agente já declara, na própria seção
"O que NÃO faz — encaminhe para" (ou equivalente), pra quem escalar quando o pedido sai do
próprio escopo. Isto aqui é a **visão consolidada** dessas declarações, pra navegação humana
e pra `agent-creator` checar sobreposição antes de criar um agente novo (ver "Adicionando um
agente novo" abaixo). Se editar a tabela de escalação de um agente, atualize aqui também.

### Dentro de `data-engineering/`

```text
schema-designer     <-> dbt-specialist        modelagem dimensional <-> implementação em dbt
schema-designer     <-> spark-engineer        modelagem <-> transformação PySpark
schema-designer     <-> sql-optimizer         design de schema <-> otimização de query
schema-designer     <-> lakehouse-architect   modelagem lógica <-> formato físico de tabela
dbt-specialist      <-> spark-engineer        model SQL vs job PySpark
dbt-specialist      <-> pipeline-architect    model dbt <-> orquestração/DAG
dbt-specialist      <-> data-quality-analyst  model <-> suite Great Expectations/Soda
dbt-specialist      <-> data-contracts-engineer  teste dbt gerado a partir de um contrato
pipeline-architect  <-> streaming-engineer    orquestração batch <-> streaming
spark-engineer      <-> lakehouse-architect   job PySpark <-> decisão de table format
streaming-engineer  <-> lakehouse-architect   sink de streaming <-> table format
lakehouse-architect <-> data-platform-engineer  table format <-> infra/custo cloud
data-contracts-engineer <-> data-quality-analyst  contrato <-> implementação do check
data-contracts-engineer <-> schema-designer   contrato <-> design de schema do zero
data-quality-analyst <-> sql-optimizer        qualidade <-> query lenta
```

### `data-engineering/` <-> `architect/`

```text
sql-optimizer      -> sql-architect      otimizar query existente vs desenhar query nova
streaming-engineer -> rag-architect      embeddings/RAG em tempo real
```

### `architect/` <-> `architect/`

```text
search-strategy-advisor -> rag-architect   decisão rápida de canal (vetor/SQL/híbrido) vs
                                            design completo de retrieval do zero
```

### `dev/` <-> qualquer categoria

```text
dev-loop-executor  -> qualquer agente   via Task(subagent_type: ...), ver DEV-LOOP.md —
                                          é o orquestrador do nível 2 do espectro
                                          (vibe coding / Dev Loop / harness completo)
prompt-crafter     -> qualquer agente   mesmo mecanismo, na fase de craft do PROMPT.md
revisor-codigo     -> sql-optimizer      revisão de diff SQL-pesado, ver /sql-review
```

### `workflow/` <-> qualquer categoria

```text
harness-build       -> revisor-codigo    obrigatório antes de fechar qualquer task
harness-brainstorm  -> codebase-explorer opcional — só se o repo já tem código (passo 1),
                                          decisão sempre do usuário
harness-define      -> adversarial-judge opcional — segunda opinião via OpenRouter sobre o
harness-design      -> adversarial-judge grill/PRD, sempre consultivo, nunca bloqueia
```

`harness-design` (via `/harness-architect`) decide quais agentes de `data-engineering/` ou
`architect/` nascem no projeto **alvo** olhando o PRD por camada — essa decisão é caso a caso,
não uma relação fixa como as tabelas acima. Ver
`.claude/skills/harness-architect/references/stack-layer-map.md`.

## Adicionando um agente novo

Use `agent-creator` (ele já sabe pedir a categoria). Se nenhuma categoria existente encaixa,
crie uma nova subpasta — nunca solte um `.md` direto em `.claude/agents/` sem categoria.
Espelhe sempre em `.cursor/agents/{categoria}/{nome}.md`.
