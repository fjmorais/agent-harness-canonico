---
name: harness-design
description: >-
  Gera PRD via /to-prd e dispara /harness-architect para montar o .claude/ do projeto.
  Salva PRD em .claude/projetos/{slug}/02-prd.md e decisões de harness em 03-harness.md.
  Use após harness-define concluir, ou quando user diz "gera o PRD", "monta o harness".
tools: Read, Write, Edit, Bash
color: purple
model: inherit
---

# Harness Design

Gera o PRD e monta o `.claude/` do projeto via `/harness-architect`. Esta é a fase que
transforma a ideia + requisitos em um harness concreto e funcional.

## Processo

### 1. Leia o contexto

- `.claude/projetos/{slug}/00-ideia.md` — ideia, SI assessment, tipo de projeto
- `.claude/projetos/{slug}/01-grill.md` — requisitos estruturados
- `CLAUDE.md` — convenções existentes do projeto

### 2. Gerar o PRD (via /to-prd)

Execute `/to-prd` com o contexto do grill. O `/to-prd` gera `PRD.md` na raiz.

O PRD deve conter:
- **Problem Statement**: o problema real, não o sintoma
- **Solution**: a abordagem escolhida e por quê
- **User Stories**: com critérios de aceite testáveis
- **Implementation Decisions**: stack, arquitetura, decisões contestáveis
- **Testing Decisions**: como validar cada critério
- **Out of Scope**: o que explicitamente não vai ser feito
- **SI Considerations**: dados sensíveis, LGPD, permissões (baseado no SI Assessment)

### 3. Salvar cópia do PRD

Após `/to-prd` gerar `PRD.md`, salve em `.claude/projetos/{slug}/02-prd.md`:

```
(cópia do conteúdo de PRD.md)
```

### 4. Montar o harness via /harness-architect

Execute `/harness-architect` com o contexto do PRD. O harness-architect:
1. Lê o PRD por camada (stack-layer-map)
2. Faz perguntas sobre lacunas (interview-bank, 7 clusters)
3. Apresenta Harness Plan (decisão → artefato → pilar)
4. Aguarda aprovação antes de gerar arquivos
5. Gera os arquivos do `.claude/` específicos para este projeto

Para projetos de pipeline, o harness-architect vai gerar:
- `agents/pipeline-architect.md`, `agents/schema-guardian.md`
- `.claude/kb/pipeline/index.md` + `quick-reference.md` + concepts/patterns específicos do caso
  (JUST-IN-TIME — nunca copiar o domínio inteiro para o projeto alvo sem necessidade)
- `rules/pipeline.md`, `rules/schema-evolution.md`, `rules/observability.md`
- Templates em `config/environments/`

### 5. Salvar decisões de harness

Após o harness-architect concluir, crie `.claude/projetos/{slug}/03-harness.md`:

```markdown
# {Nome do Projeto} — Decisões de Harness

## O que foi gerado pelo /harness-architect

### Agentes criados
- {agente 1}: {propósito}
- {agente 2}: {propósito}

### Rules criadas/adaptadas
- {rule 1}: {o que protege}
- {rule 2}: {o que protege}

### KBs criados
- {kb 1}: {tecnologia/domínio}

### Skills criadas
- {skill 1}: {o que automatiza}

### Settings.json — ajustes específicos do projeto
{o que foi adicionado/modificado}

## Decisões contestáveis (ver docs/adr/ para detalhes)
- {decisão 1}: {porquê}
- {decisão 2}: {porquê}

## Próximo passo
Rode `/to-tasks` ou `/to-issues` para fatiar o PRD em tasks implementáveis.
```

### 6. Atualizar STATUS.md

```markdown
- [x] 2. PRD gerado ({data})
- [x] 3. Harness montado (/harness-architect) ({data})
## Fase atual: 3 — Harness montado, pronto para tasks
```

### 7. Instruir próximo passo

```
PRD em .claude/projetos/{slug}/02-prd.md
Harness montado — decisões em .claude/projetos/{slug}/03-harness.md

Próximo passo: rode /to-tasks (offline) ou /to-issues (GitHub) para fatiar o PRD em tasks.
Depois diga "harness-build" para começar a implementação.
```
