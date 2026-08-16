# Spike: viabilidade de hooks equivalentes no Cursor

**Status:** not started
**Blocked by:** none

## What to build

Investigação (não é código de produção) para responder: o Cursor expõe algum mecanismo
equivalente aos hooks do Claude Code (`SessionStart`/`SessionEnd`/`PreToolUse`/`PostToolUse`/
`SubagentStop`) capaz de emitir evento de tool-call e início/fim de sessão? Documentar o
resultado (o que existe, o que não existe, quais eventos são capturáveis, quais não são) e a
recomendação resultante: seguir com adapter de hook (Opção B/C da Pergunta 7 do grill) ou cair
para o caminho de agente / `unavailable`.

Resultado vira input direto da task 11.

## Acceptance criteria

- [ ] Documento de spike (`docs/adr/002-viabilidade-hooks-cursor.md` ou seção de notas) resume
      o que foi encontrado, com fontes — no test — decisão de pesquisa/documentação, não código
      executável.
- [ ] Recomendação clara para a task 11: "implementar adapter de hook" ou "cair para caminho de
      agente/unavailable" — no test — é uma decisão registrada, não uma função testável.

## Notes

Se o resultado for "hooks não equivalentes", a task 11 deve ser reaberta/redefinida (talvez
vire "declarar Cursor como `unavailable` no manifest" em vez de "adapter de hook Cursor") —
atualizar o escopo da task 11 conforme o resultado deste spike antes de iniciá-la.
