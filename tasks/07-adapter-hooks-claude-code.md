# Adapter de hooks — Claude Code

**Status:** not started
**Blocked by:** 03-scaffold-projeto-novo.md, 05-harness-redact.md, 06-escritor-evento-concorrente.md

## What to build

Configuração de hooks em `.claude/settings.json` (deste próprio canônico, como primeiro
consumidor real) + scripts chamados por eles:
- `SessionStart`: cria `runs/YYYY/MM/run_<id>/` (run.json com estado `created` → `running`),
  identifica `writer_id` do agente principal.
- `SessionEnd`: fecha o run (`run.json` para estado `completed`/`failed`/`cancelled` conforme o
  resultado), dispara `rebuild_timeline()` e grava `indexes/` atualizado para aquele run.
- `PreToolUse`/`PostToolUse`: monta o evento (`tool.executed`, exit code, duração), aplica
  `redact()` (task 05), grava via `write_event()` (task 06) com o `writer_id` correto.
- `SubagentStop`: identifica o `writer_id` do subagente que terminou, grava evento de conclusão
  daquele escritor.

`correlation_id` é propagado a partir do contexto disponível no hook (ex.: nome do comando/skill
em execução, se disponível) — quando não houver como determinar, registrar `null` de forma
explícita (nunca inventar um valor).

## Acceptance criteria

- [ ] Uma sessão real do Claude Code (rodada manualmente contra este canônico, com hooks
      ativos) cria `runs/YYYY/MM/run_<id>/` no `SessionStart` e fecha com estado terminal no
      `SessionEnd` — tested by: teste de integração/e2e disparando os hooks via simulação de
      evento (payload que o Claude Code passa para hooks) e verificando o `run.json` resultante.
- [ ] Tool calls durante a sessão geram eventos em `events/<writer_id>.jsonl` já redigidos
      (nenhum CPF/email/path de usuário cru no arquivo gravado) — tested by: teste de
      integração simulando um `PostToolUse` com payload contendo PII e verificando o evento
      gravado.
- [ ] Um subagente disparado durante a sessão gera seu próprio arquivo de escritor, distinto do
      arquivo do agente principal — tested by: teste de integração simulando `SubagentStop` com
      `writer_id` diferente do principal.
- [ ] `correlation_id` ausente é gravado como `null` explícito, nunca omitido silenciosamente do
      payload — tested by: teste unitário verificando a estrutura do evento quando não há
      correlação disponível.

## Notes

Esta task instrumenta o próprio canônico primeiro (dogfooding) — os hooks em
`.claude/settings.json` deste repo passam a valer também para o Dev Loop e os fluxos SDD já
existentes, conforme a decisão da Pergunta 2 do grill.
