# Agent Harness Canônico — guia do agente

> Este repositório é o **framework** do Agent Harness Method.
> Não é um produto — é a fonte de verdade de agents, skills, KBs e rules
> que são propagados via `/install-harness` para projetos alvo.
>
> O template de `CLAUDE.md` para projetos-filhos está em:
> `.claude/skills/harness-architect/references/claude-dir-templates.md`

## O que é este repositório

- **Canônico fixo:** `/home/fabiano/agent-harness-canonico`
- **Dois modos de uso:**
  1. Clonar como template de novo projeto → rodar `/harness-architect` no projeto clonado
  2. Apontar como fonte no `/install-harness` de outro projeto existente

## Comandos

```bash
# Instalar/atualizar harness em projeto alvo:
/install-harness    # informa path de destino no primeiro passo

# Evoluir o canônico:
agent-creator       # criar novo agente
/write-a-skill      # criar nova skill
kb-architect        # criar ou atualizar KB de domínio
revisor-codigo      # revisar diff antes de "commitar" evolução
```

## Invariantes (nunca quebrar ao evoluir o canônico)

- **Nenhum código de produto aqui** — só artefatos de framework (agents, skills, KBs, rules)
- **Agents e skills devem ser genéricos** — reutilizáveis em qualquer projeto, sem acoplamento
- **`/install-harness` é o único mecanismo de propagação** — nunca copiar manualmente para projetos
- **Ao renomear pasta:** atualizar `install-harness/SKILL.md` + guias HTML relevantes em `docs/guia/`
- **Ao evoluir um KB:** verificar se o KB está referenciado na tabela stack-layer de `install-harness/SKILL.md`
- **Agents e skills devem ter `description:` claro** — é o único texto que o agente vê para decidir quando usar

## Onde fica o quê

| O que | Onde | Qtd |
|---|---|---|
| Agents | `.claude/agents/` | 15 |
| Skills | `.claude/skills/` | 15 |
| Rules | `.claude/rules/` | 11 |
| KBs | `.claude/kb/` | 8 domínios |
| Commands | `.claude/commands/` | 3 (novo-projeto, validar, scorecard) |
| Design docs | `.claude/design/` | features/, archive/, reports/ |
| Projetos do harness | `.claude/projetos/` | histórico de evoluções |
| Guias HTML | `docs/guia/` | 16 slides (01–16) |
| Template CLAUDE.md | `.claude/skills/harness-architect/references/claude-dir-templates.md` | — |
| Schema do manifest | `.claude/skills/install-harness/references/install-manifest-schema.md` | — |
| Guia de uso do harness | `HARNESS-GUIDE.md` | — |
| Setup de template (clone) | `COMO-USAR.md` | — |
