---
name: harness-ship
description: >-
  Encerra projeto: roda /scorecard, escreve retrospectiva em 05-retro.md, fecha STATUS.md.
  Use quando todas as tasks estão marcadas "done" e o usuário quer fechar o projeto.
  Dispare com "ship", "fechar projeto", "retrospectiva", "encerrar implementação".
tools: Read, Write, Edit, Bash
color: orange
model: inherit
---

# Harness Ship

Encerra o projeto com métricas reais, aprendizados registrados e STATUS.md arquivado.

## Processo

### 1. Verificar estado antes de shippar

- Leia `tasks/README.md` — todas as tasks têm `Status: done`?
- Leia `metrics/entregas.jsonl` — todas as tasks têm registro?
- Leia `docs/adr/` — todas as decisões contestáveis foram documentadas?

Se qualquer item faltar, informe ao usuário antes de continuar.

### 2. Rodar /scorecard

Execute `/scorecard` para gerar as métricas de entrega:

```bash
# Coleta dados de git, gh (se disponível) e metrics/entregas.jsonl
/scorecard
```

Salve o output — vai para a retrospectiva.

### 3. Escrever retrospectiva

Crie `.claude/projetos/{slug}/05-retro.md`:

```markdown
# {Nome do Projeto} — Retrospectiva de Ship

Ship em: {data}

## Métricas de entrega (via /scorecard)

| Métrica | Valor |
|---|---|
| Tasks entregues | N |
| Critérios de aceite atendidos | X% (N/N) |
| Tentativas medianas até gate verde | N |
| Veredito do revisor: aprovado/ressalvas/bloqueado | N/N/N |
| Intervenções humanas | N |
| Taxa de autonomia | X% |

## O que funcionou bem

- {o que o agente fez bem — manter nas próximas sprints}

## O que melhorar

- {onde teve mais tentativas? mais intervenções humanas?}

## Armadilhas encontradas (para o próximo projeto)

- {contexto não óbvio que causou friction}

## ADRs desta implementação

- [ADR-NNNN](../../../docs/adr/NNNN-{titulo}.md): {decisão}

## Harness — o que aprendemos

- {o que o harness capturou certo? o que faltou como rule/hook/skill?}
- {se algum invariante foi quase violado, registre como candidato a deny rule}
```

### 4. Fechar STATUS.md

Atualize `.claude/projetos/{slug}/STATUS.md`:

```markdown
- [x] 6. Ship / retrospectiva ({data})

## Fase atual: CONCLUÍDO — Projeto arquivado

## Resultado final
{resumo de 2–3 linhas do que foi entregue}
```

### 5. Commit de fechamento

```bash
git add .claude/projetos/{slug}/05-retro.md
git add .claude/projetos/{slug}/STATUS.md
git add metrics/entregas.jsonl
git commit -m "chore: ship {slug} — projeto encerrado com retrospectiva"
```

### 6. Mensagem de encerramento

```
Projeto "{nome}" encerrado.

📋 Retrospectiva: .claude/projetos/{slug}/05-retro.md
📊 Métricas:      metrics/entregas.jsonl
📖 ADRs:          docs/adr/

Para iniciar um novo projeto: diga "harness-brainstorm" ou rode /novo-projeto.
```
