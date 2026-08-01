# Agent Harness Canônico — guia do agente

> Este repositório é o **framework** do Agent Harness Method.
> Não é um produto — é a fonte de verdade de agents, skills, KBs e rules
> que são propagados via `/install-harness` para projetos alvo.
>
> O template de `CLAUDE.md` para projetos-filhos está em:
> `.cursor/skills/harness-architect/references/claude-dir-templates.md`

## O que é este repositório

- **Canônico fixo:** `/home/fabiano/agent-harness-canonico`
- **Dois modos de uso:**
  1. Clonar como template de novo projeto → rodar `/harness-architect` no projeto clonado
  2. Apontar como fonte no `/install-harness` de outro projeto existente

## Comandos

- Instalar harness em projeto alvo: `/install-harness` (informa path de destino)
- Criar novo agente: `agent-creator`
- Criar nova skill: `/write-a-skill`
- Criar ou atualizar KB: `kb-architect`
- Revisar evolução do canônico: `revisor-codigo`

## Invariantes (nunca quebrar ao evoluir o canônico)

- Nenhum código de produto aqui — só artefatos de framework (agents, skills, KBs, rules)
- Agents e skills devem ser genéricos — reutilizáveis em qualquer projeto
- `/install-harness` é o único mecanismo de propagação — nunca copiar manualmente para projetos
- Ao renomear pasta: atualizar `install-harness/SKILL.md` + guias HTML relevantes
- Ao evoluir um KB: verificar se o KB está referenciado na tabela stack-layer de `install-harness/SKILL.md`
- Agents e skills devem ter `description:` claro — é o único texto que o assistente vê para decidir quando usar
- Toda edição em `.claude/{agents,skills,rules,kb,commands,guias}` deve ser espelhada em `.cursor/`
  na mesma sessão (mesma estrutura; `rules/*.md` vira `rules/*.mdc`) — nunca deixar os dois divergirem

## Onde fica o quê

| O que | Onde | Qtd |
|---|---|---|
| Agents | `.cursor/agents/` | 33 (4 categorias: `workflow/`, `architect/`, `dev/`, `data-engineering/`) |
| Skills | `.cursor/skills/` | 18 |
| Rules | `.cursor/rules/` | 11 |
| KBs | `.cursor/kb/` | 18 domínios |
| Commands | `.cursor/commands/` | 19 (5 na raiz + `data-engineering/` + `visual-explainer/`) |
| Dev Loop | `.cursor/dev/` | tasks/progress/logs/templates/examples — ver `DEV-LOOP.md` |
| Design docs | `.cursor/design/` | features/, archive/, reports/ |
| Projetos do harness | `.cursor/projetos/` | histórico de evoluções |
| Guias passo-a-passo | `.cursor/guias/` | tutoriais didáticos via `/novo-guia` — ver `GUIA-PASSO-A-PASSO.md` |
| Guias HTML | `docs/guia/` | 16 slides (01–16) |
| Template CLAUDE.md | `.cursor/skills/harness-architect/references/claude-dir-templates.md` | — |
| Schema do manifest | `.cursor/skills/install-harness/references/install-manifest-schema.md` | — |
| Guia de uso do harness | `HARNESS-GUIDE.md` | — |
| Setup de template (clone) | `COMO-USAR.md` | — |
| Guia da CLI de install (standalone) | `INSTALL-HARNESS-CLI.md` | — |
| Conceito Dev Loop (execução ágil de tarefa pontual) | `DEV-LOOP.md` | — |

## Como usar no Cursor

Todos os artefatos estão espelhados em `.cursor/` para acesso via `@`-mention:

```
@.cursor/agents/workflow/harness-brainstorm.md      → entrevista inicial de projeto
@.cursor/agents/workflow/harness-build.md           → implementar tasks com gates
@.cursor/skills/install-harness/SKILL.md   → processo de install em outro projeto
@.cursor/skills/harness-architect/SKILL.md → montar .claude/ de um projeto
@.cursor/skills/grill-me/SKILL.md          → aprofundar requisitos
@.cursor/skills/excalidraw-diagram/SKILL.md → gerar diagramas Excalidraw com argumentação visual
@.cursor/kb/fastapi/                        → KB de FastAPI
@.cursor/kb/langgraph/                      → KB de LangGraph
@.cursor/kb/rag/                            → KB de RAG e busca semântica
@.cursor/rules/                             → todas as rules como contexto adicional
```

## Referência rápida de agents e skills

Ver `HARNESS-GUIDE.md` para a lista completa com descrição de cada agent e skill.
