# Agent Harness Canônico — guia do agente

> Este repositório é o **framework** do Agent Harness Method.
> Não é um produto — é a fonte de verdade de agents, skills, KBs e rules
> que são propagados via `/install-harness` para projetos alvo.

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
- Agents e skills devem ter `description:` claro — é o único texto que o assistente vê para decidir quando usar

## Onde fica o quê

| O que | Onde | Qtd |
|---|---|---|
| Agents | `.cursor/agents/` | 15 |
| Skills | `.cursor/skills/` | 15 |
| Rules | `.cursor/rules/` | 11 |
| KBs | `.cursor/kb/` | 8 domínios |
| Commands | `.cursor/commands/` | 3 (novo-projeto, validar, scorecard) |
| Design docs | `.cursor/design/` | features/, archive/, reports/ |
| Projetos | `.cursor/projetos/` | histórico de evoluções |
| Guias HTML | `docs/guia/` | 16 slides (01–16) |
| Guia de uso | `HARNESS-GUIDE.md` | — |
| Setup de template | `COMO-USAR.md` | — |

## Como usar no Cursor

Todos os artefatos estão espelhados em `.cursor/` para acesso via `@`-mention:

```
@.cursor/agents/harness-brainstorm.md      → entrevista inicial de projeto
@.cursor/agents/harness-build.md           → implementar tasks com gates
@.cursor/skills/install-harness/SKILL.md   → processo de install em outro projeto
@.cursor/skills/harness-architect/SKILL.md → montar .claude/ de um projeto
@.cursor/skills/grill-me/SKILL.md          → aprofundar requisitos
@.cursor/kb/fastapi/                        → KB de FastAPI
@.cursor/kb/langgraph/                      → KB de LangGraph
@.cursor/kb/rag/                            → KB de RAG e busca semântica
@.cursor/rules/                             → todas as rules como contexto adicional
```

## Referência rápida de agents e skills

Ver `HARNESS-GUIDE.md` para a lista completa com descrição de cada agent e skill.
