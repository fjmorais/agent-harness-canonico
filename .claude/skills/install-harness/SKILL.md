---
name: install-harness
description: >-
  Instala ou atualiza o agent harness canônico num projeto. Detecta o estado do projeto
  (zerado, existente sem harness, ou com harness incompleto), mapeia artefatos relevantes
  do canônico com base na stack detectada, mostra um Install Plan para confirmação e só
  então copia/gera os arquivos. Use quando: "instala o harness nesse projeto", "configura
  esse repo para usar o harness", "atualiza o harness desse projeto", "bootstrap do .claude/",
  "como começo a usar o agente nesse projeto". Dispare com "install-harness",
  "instala harness", "bootstrap harness", "configura harness".
tools: Read, Write, Edit, Bash
---

# Install Harness

Instala o agent harness canônico num projeto alvo — novo ou existente.
**Regra central:** mostrar o Install Plan e confirmar antes de tocar qualquer arquivo.

## Canonical path

Canônico fixo: `/home/fabiano/agent-harness-canonico`

Antes de qualquer coisa, verifique que esse path existe:
```bash
ls /home/fabiano/agent-harness-canonico/.claude/agents/ 2>/dev/null || echo "CANÔNICO NÃO ENCONTRADO"
```
Se não existir, peça o path correto ao usuário antes de prosseguir.

---

## Processo

### Passo 1 — Detectar estado do projeto alvo

```bash
# Detecta harness existente
find .claude/ -type f 2>/dev/null | head -20
cat .claude/harness-manifest.json 2>/dev/null || echo "SEM_MANIFEST"

# Detecta stack
ls pyproject.toml package.json docker-compose.yml 2>/dev/null
grep -r "langgraph\|fastapi\|supabase\|langfuse\|qdrant\|pgvector\|airflow\|spark\|dbt" \
  pyproject.toml package.json 2>/dev/null | head -20
```

Classifique em um dos três modos:

| Modo | Critério | O que fazer |
|---|---|---|
| `NOVO` | Sem `.claude/` ou pasta vazia | Scaffolding completo do zero |
| `SEM_HARNESS` | `.claude/` existe mas sem manifest | Instala o que falta, preserva o que existe |
| `ATUALIZAÇÃO` | `harness-manifest.json` presente | Compara manifest vs canônico, atualiza não-customizados |

### Passo 2 — Mapear artefatos relevantes

Leia `references/install-manifest-schema.md` para o schema do manifest.
Use a tabela abaixo para decidir o que instalar com base na stack detectada:

| Categoria | Artefatos do canônico | Condição |
|---|---|---|
| **Foundation** (sempre) | CLAUDE.md¹, AGENTS.md¹, CONTEXT.md¹, settings.json¹, HANDOFF.md¹ | Sempre — gerar projeto-específico |
| **Dev workflow** (sempre) | skills: harness-architect, grill-me, grill-with-docs, to-prd, to-tasks, to-issues, new-adr, sync-context, make-readme, handoff, write-a-skill | Sempre — copiar do canônico |
| **Code quality** (sempre) | skills: gen-tests; rules: estilo-codigo, testes, seguranca, definicao-de-pronto; agents: codebase-explorer, revisor-codigo, meeting-analyst | Sempre — copiar do canônico |
| **Python/FastAPI** | kb/fastapi/, rules/backend.md, agents/sql-architect.md | `pyproject.toml` detectado |
| **LangGraph** | kb/langgraph/, rules/langgraph.md, agents/prompt-engineer.md, agents/rag-architect.md | `langgraph` em deps |
| **Supabase** | kb/supabase/ | `supabase` em deps |
| **React/Frontend** | rules/frontend.md, kb/testing/patterns/vitest-patterns.md | `package.json` detectado |
| **Multi-tenant** | kb/multi-tenant/, rules/multi-tenant.md | Estrutura ou deps sugerem (`rls`, `tenant`) |
| **Observabilidade** | kb/observabilidade/ | `langfuse` em deps |
| **RAG/Vetorial** | kb/rag/, rules/rag.md, agents/rag-architect.md, agents/search-strategy-advisor.md | `qdrant` ou `pgvector` em deps |
| **Pipeline/dados** | kb/pipeline/, rules/pipeline.md | `airflow`, `spark` ou `dbt` em deps |

¹ Arquivo gerado (não copiado) — usa a stack e nome do projeto detectados.

### Passo 3 — Montar e apresentar o Install Plan

Apresente ANTES de qualquer escrita:

```
# Install Plan — [nome do projeto detectado]

## Modo: NOVO | SEM_HARNESS | ATUALIZAÇÃO

## COPIAR do canônico (framework)
- .claude/agents/codebase-explorer.md          [NOVO]
- .claude/skills/harness-architect/            [NOVO]
- .claude/kb/fastapi/                          [NOVO] ← pyproject.toml + fastapi detectados
- .claude/rules/langgraph.md                   [NOVO] ← langgraph em deps

## GERAR (projeto-específico)
- CLAUDE.md                                    [GERAR com stack detectada]
- AGENTS.md                                    [GERAR espelho portátil]
- CONTEXT.md                                   [SKELETON — preencher via /grill-with-docs]
- settings.json                                [GERAR com hooks da stack]
- HANDOFF.md                                   [TEMPLATE]

## PULAR (stack não detectada)
- .claude/kb/pipeline/                         (sem airflow/spark/dbt)
- .claude/rules/pipeline.md

## NÃO TOCAR (já existe ou customizado)
- CLAUDE.md                                    [MANTÉM — já existe com conteúdo]
- .claude/agents/revisor-codigo.md             [MANTÉM — manifest: customized=true]

Confirma este plano? (s/n)
```

**Aguarde confirmação antes de prosseguir.**

### Passo 4 — Executar (somente após confirmação)

**Para arquivos COPIAR:** copie do canônico para o projeto. Se o arquivo já existe e não está no manifest (modo `SEM_HARNESS`), skip sem sobrescrever — liste como `[SKIPPED — já existe]`.

**Para arquivos GERAR:** use os templates de `.claude/skills/harness-architect/references/claude-dir-templates.md`. Preencha com:
- Nome do projeto: `basename $(pwd)`
- Stack detectada: resumo de 1 linha
- Hooks no settings.json: adaptados à stack (Python → ruff + mypy + pytest; JS → eslint + vitest)

**Para modo `ATUALIZAÇÃO`:** só atualiza artefatos com `"customized": false` no manifest onde o arquivo do canônico é mais novo que o instalado.

### Passo 5 — Gravar manifest

Ao final, grave/atualize `.claude/harness-manifest.json`:

```json
{
  "canonical_path": "/home/fabiano/agent-harness-canonico",
  "installed_at": "YYYY-MM-DD",
  "mode": "NOVO|SEM_HARNESS|ATUALIZAÇÃO",
  "artefacts": {
    ".claude/agents/codebase-explorer.md": {
      "source": "canonical",
      "customized": false
    },
    "CLAUDE.md": {
      "source": "generated",
      "customized": true
    }
  }
}
```

Feche listando os próximos passos obrigatórios:
1. `/grill-with-docs` — preencher CONTEXT.md com terminologia real do domínio
2. `/grill-me` — refinar CLAUDE.md com invariantes específicos do projeto
3. Revisar hooks em `settings.json` (comandos corretos para a stack)
4. `/validar` — confirmar gate verde antes da primeira sessão de build

---

## Regras de qualidade

- **Nunca sobrescreve** arquivo com `"customized": true` no manifest
- **Nunca inventa** stack ou nome de projeto — usa só o que detectou nos arquivos
- **Nunca executa sem aprovação** do Install Plan
- **Começa mínimo** — Foundation + workflow sempre; stack-specific só se detectado
- **CONTEXT.md vem vazio** — nunca preenche com terminologia inventada; isso é papel do `/grill-with-docs`
- **Manifest é sagrado** — qualquer arquivo sem entrada no manifest é tratado como `customized: true` em futuras atualizações

## Referências

- `references/install-manifest-schema.md` — schema completo do harness-manifest.json
- `.claude/skills/harness-architect/references/stack-layer-map.md` — mapa stack → artefatos
- `.claude/skills/harness-architect/references/claude-dir-templates.md` — templates para gerar Foundation
- `.claude/skills/grill-with-docs/SKILL.md` — preenchimento do CONTEXT.md após install
