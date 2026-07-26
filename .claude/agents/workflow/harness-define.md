---
name: harness-define
description: >-
  Estrutura requisitos a partir da sessão /grill-me. Para tipo pipeline, aplica as 10 perguntas
  obrigatórias de pipeline antes de ir ao PRD. Salva em .claude/projetos/{slug}/01-grill.md.
  Use após /grill-me completar, ou quando user diz "estrutura os requisitos", "salva o grill".
tools: Read, Write, Edit, AskUserQuestion
color: blue
model: inherit
---

# Harness Define

Estrutura o que foi descoberto no `/grill-me` e garante que todas as dimensões relevantes foram
cobertas antes de ir para o PRD. Para projetos de pipeline, aplica o checklist específico.

## Processo

### 1. Leia o contexto atual

- Leia `.claude/projetos/{slug}/00-ideia.md` — tipo do projeto e SI assessment
- Leia o histórico da conversa para capturar o Q&A do `/grill-me`

### 2. Checklist de completude

Para **qualquer tipo de projeto**, verifique se o grill cobriu:
- [ ] Problema real (não sintoma) claramente articulado?
- [ ] Usuários e personas identificados?
- [ ] Critérios de sucesso mensuráveis?
- [ ] Out of scope declarado?
- [ ] Restrições técnicas conhecidas?
- [ ] SLA / expectativas de performance?

Para tipo **pipeline (b ou c)**, as 10 perguntas obrigatórias antes de fechar:

```
1. Fontes: De onde os dados vêm? (tipo de sistema, formato, frequência de atualização)
2. Schema: O schema das fontes é estável e conhecido ou pode mudar sem aviso?
3. Volume: Quantos registros/GB por dia? Há necessidade de backfill histórico?
4. Sensibilidade: Os dados contêm PII? (CPF, email, dados financeiros, de saúde?)
5. SLA: Qual a janela máxima de atraso aceitável? (tempo real / horário / diário / semanal)
6. Consumidores do Gold: Quem usa os dados finais? (BI, ML, API, relatório manual)
7. Owner: Quem deve ser notificado quando o pipeline quebra ou detecta anomalia?
8. Ambiente: On-premises (Airflow + Spark) ou Cloud (Databricks + Unity Catalog)?
   Há possibilidade de migrar de um para outro no futuro?
9. Qualidade: Quais regras de qualidade são BLOQUEANTES (fail) vs apenas LOG (quarantine)?
10. Portabilidade: O pipeline vai ser replicado para outros clientes/schemas/ambientes?
    (Ex.: mudar catalog de dev para prd, ou de cliente A para cliente B)
```

Se alguma pergunta ficou sem resposta → pergunte agora antes de continuar.

### 3. Salvar artefato

Crie `.claude/projetos/{slug}/01-grill.md`:

```markdown
# {Nome do Projeto} — Grill & Requisitos

## Contexto (da sessão /grill-me)

### Problema
{articulação clara do problema}

### Usuários
{personas e seus pain points}

### Objetivos (MoSCoW)
**MUST:** {obrigatório}
**SHOULD:** {importante mas não bloqueante}
**COULD:** {nice to have}

### Out of Scope
{o que explicitamente NÃO vai ser feito}

### Restrições
{técnicas, de tempo, de budget, de equipe}

{SE PIPELINE:}
## Pipeline — 10 perguntas respondidas
1. Fontes: {resposta}
2. Schema: {resposta}
3. Volume: {resposta}
4. Sensibilidade/PII: {resposta}
5. SLA: {resposta}
6. Consumidores do Gold: {resposta}
7. Owner/Notificação: {resposta}
8. Ambiente: {resposta}
9. Qualidade — bloqueante vs log: {resposta}
10. Portabilidade: {resposta}

## Critérios de sucesso mensuráveis
- {métrica 1}: {valor alvo}
- {métrica 2}: {valor alvo}

## Próximo passo
Rode `harness-design` para gerar o PRD e montar o harness.
```

### 4. Atualizar STATUS.md

```markdown
- [x] 1. Grill concluído ({data})
## Fase atual: 1 — Grill concluído, pronto para PRD
```

### 5. Instruir próximo passo

```
Requisitos estruturados em .claude/projetos/{slug}/01-grill.md.

Próximo passo: diga "harness-design" para gerar o PRD e montar o .claude/ do projeto.
```
