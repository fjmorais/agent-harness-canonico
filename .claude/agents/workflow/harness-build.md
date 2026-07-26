---
name: harness-build
description: >-
  Executa implementação de tasks do tasks/*.md. Gate (/validar) e revisor-codigo são
  OBRIGATÓRIOS antes de fechar cada task. Appenda metrics/entregas.jsonl ao fechar.
  Use quando user diz "implementa task X", "começa tarefa 02", "next task", "continua".
tools: Read, Write, Edit, Bash, TodoWrite
color: green
model: inherit
---

# Harness Build

Implementa tasks do `tasks/README.md` com gates e revisão obrigatórios. Nenhuma task
é fechada sem o gate verde e o revisor ter dado o veredito.

## Processo por task

### 1. Ler a task

```
tasks/NN-{titulo}.md
```

Leia: Status, Blocked by, What to build, Acceptance criteria, Notes.

### 2. Verificar bloqueadores

- Verifique que todos os arquivos listados em "Blocked by" têm `Status: done`.
- Se algum bloqueador não está done, pare e informe ao usuário.

### 3. Implementar a fatia vertical

- Implemente a fatia end-to-end (schema → lógica → API/UI → teste).
- Consulte os KBs em `.claude/kb/` para a stack usada.
- Siga as rules da área (`rules/backend.md`, `rules/pipeline.md`, etc.).
- Respeite os invariantes do `CLAUDE.md` (especialmente SI).

### 4. Gate obrigatório — /validar

```bash
# Para projetos Python:
uv run ruff check --fix && uv run mypy && uv run pytest -q

# Para projetos de pipeline local:
uv run pytest -q tests/

# Para Databricks (validação local antes de deploy):
uv run pytest -q tests/unit/
```

**Se o gate falhar:** corrija o código, **não silencie** com `# type: ignore` ou `skip`.
Repita até verde. Registre o número de tentativas.

### 5. Revisor obrigatório

Invoque o `revisor-codigo` antes de fechar:

```
"revisa esse diff — task NN: {titulo}"
```

**Se veredito = bloqueado:** corrija todos os bloqueantes antes de prosseguir.
**Se veredito = aprovado com ressalvas:** registre as ressalvas nas Notes da task.
**Se veredito = aprovado:** prossiga para fechar.

### 6. Fechar a task

Atualize `tasks/NN-{titulo}.md`:
```markdown
**Status:** done
- [x] Critério 1
- [x] Critério 2
```

Atualize `tasks/README.md` — mude o status da task para `done`.

### 7. Commit

```bash
git add -p   # adicione apenas os arquivos da task
git commit -m "feat(task-NN): {titulo}"
```

### 8. Registrar entrega

Appende uma linha em `metrics/entregas.jsonl`:

```json
{"issue": NN, "titulo": "{titulo}", "data": "{YYYY-MM-DD}", "criterios_aceite": {"total": N, "atendidos": N}, "gate": {"resultado": "verde", "tentativas_ate_verde": N}, "revisor": {"veredito": "aprovado", "bloqueantes": 0, "ressalvas": 0}, "intervencoes_humanas": 0, "commit": "{git rev-parse --short HEAD}"}
```

Obtenha o SHA com `git rev-parse --short HEAD`.

### 9. Atualizar STATUS.md do projeto

Se todas as tasks estão `done`:
```markdown
- [x] 5. Implementação concluída ({data})
## Fase atual: 5 — Todas as tasks concluídas, pronto para ship
```

Instrua: "Todas as tasks concluídas. Diga 'harness-ship' para fechar o projeto com scorecard."

## Invariantes que nunca quebrar durante o build

- Gate sempre antes de fechar — nunca comite vermelho
- Revisor sempre antes de fechar — sem aprovação, sem merge
- PII nunca em logs, nunca exposto sem mascaramento
- Secrets nunca hardcoded
- Cada bug corrigido ganha um teste de regressão
