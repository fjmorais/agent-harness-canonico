# Adapter de hooks — Cursor (condicional ao spike)

**Status:** not started
**Blocked by:** 07-adapter-hooks-claude-code.md, 10-spike-viabilidade-cursor.md

## What to build

**Resultado do spike (task 10, ver `docs/adr/002-viabilidade-hooks-cursor.md`): Cursor tem
hooks equivalentes — escopo é implementar o adapter de verdade, não `unavailable`.**

Cursor expõe `sessionStart`/`sessionEnd`/`preToolUse`/`postToolUse`/`subagentStart`/
`subagentStop` via `.cursor/hooks.json`, comunicando por stdin/stdout JSON — mesmo padrão do
Claude Code. Reaproveitar o núcleo de `scripts/harness_hook.py` (task 07: `_build_event`,
`find_run_dir`, `handle_session_start`/`handle_session_end`, `harness_redact.py`,
`write_event()`) e adicionar só uma camada de normalização de payload Cursor → formato interno:

- `postToolUse` do Cursor traz `tool_output` como **string JSON serializada** (não dict como o
  `tool_response` do Claude Code) — normalizar com `json.loads()` antes de extrair `is_error`.
- `subagentStart`/`subagentStop` trazem `subagent_id`/`subagent_type`/`parent_conversation_id`
  — mapear pra `writer_id = "subagent_" + subagent_type` (mesma convenção da task 07).
- `install-harness` passa a gerar `.cursor/hooks.json` apontando pros mesmos scripts
  (`scripts/harness_hook.py`), análogo ao que já faz para `.claude/settings.json`.
- `capabilities.telemetry.cursor: true` no manifest quando o adapter estiver ativo.

## Acceptance criteria

- [ ] Uma sessão real do Cursor (ou simulação fiel do payload documentado no ADR-002) gera
      `run.json`/`events/` no mesmo formato produzido pela task 07 — tested by: teste de
      integração equivalente ao da task 07, com payload no formato Cursor (`tool_output` como
      string JSON, `subagent_id`/`subagent_type`).
- [ ] `postToolUse` do Cursor com `tool_output` serializado é normalizado corretamente antes de
      redaction/escrita — tested by: teste unitário com fixture de payload Cursor real.
- [ ] `.cursor/hooks.json` gerado pelo `install-harness` referencia os mesmos scripts do adapter
      Claude Code (sem duplicar lógica) — tested by: teste de integração do instalador.
- [ ] `capabilities.telemetry.cursor: true` é declarado no manifest quando o adapter está ativo
      — tested by: teste unitário do manifest gerado.

## Notes

Ver `docs/adr/002-viabilidade-hooks-cursor.md` para a pesquisa completa (fonte:
https://cursor.com/docs/hooks, 2026-08-16) e a tabela de equivalência de eventos. O ADR também
registra um risco residual: o spike não testou hooks Cursor rodando de verdade, só leu
documentação — esta task deve validar contra uma sessão Cursor real antes de fechar, não confiar
só na simulação de payload.
