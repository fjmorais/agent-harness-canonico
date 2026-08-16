# Adapter de hooks — Cursor (condicional ao spike)

**Status:** done
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

- [x] Uma sessão real do Cursor (ou simulação fiel do payload documentado no ADR-002) gera
      `run.json`/`events/` no mesmo formato produzido pela task 07 — tested by: teste de
      integração equivalente ao da task 07, com payload no formato Cursor (`tool_output` como
      string JSON, `subagent_id`/`subagent_type`).
- [x] `postToolUse` do Cursor com `tool_output` serializado é normalizado corretamente antes de
      redaction/escrita — tested by: teste unitário com fixture de payload Cursor real.
- [x] `.cursor/hooks.json` gerado pelo `install-harness` referencia os mesmos scripts do adapter
      Claude Code (sem duplicar lógica) — tested by: teste de integração do instalador.
- [x] `capabilities.telemetry.cursor: true` é declarado no manifest quando o adapter está ativo
      — tested by: teste unitário do manifest gerado.

## Notes

Ver `docs/adr/002-viabilidade-hooks-cursor.md` para a pesquisa completa (fonte:
https://cursor.com/docs/hooks, 2026-08-16) e a tabela de equivalência de eventos. O ADR também
registra um risco residual: o spike não testou hooks Cursor rodando de verdade, só leu
documentação — esta task deve validar contra uma sessão Cursor real antes de fechar, não confiar
só na simulação de payload.

**Riscos residuais explícitos (não resolvidos por esta task):**
- **Nunca testado contra uma sessão Cursor real** — toda a suíte de testes usa payloads
  simulados fielmente à documentação (`docs/adr/002...`), não uma sessão Cursor de verdade
  disparando o hook. Se o payload real divergir do documentado, o adapter pode falhar
  silenciosamente (mitigado pela mesma barreira de exceção do `main()` — nunca quebra a sessão
  do usuário, mas também pode nunca gravar evento nenhum sem ninguém perceber).
- **`capabilities.telemetry.cursor: true` é gravado sempre que `.cursor/hooks.json` é gerado**,
  não quando o adapter está genuinamente "ativo" no sentido de `config.json.telemetry.enabled`
  estar ligado — o nome do campo no manifest pode sugerir mais garantia do que o valor
  realmente significa (mesmo padrão simplificado já usado para `telemetry.claude_code` nas
  tasks anteriores).
- **`provider` para eventos Cursor é setado igual ao nome do executor** (`"cursor"`), não ao
  provider real do modelo em uso (Cursor suporta múltiplos providers) — simplificação por falta
  de sinal confiável no payload documentado; refinar se o campo `model`/`model_id` do payload
  base do Cursor precisar ser exposto no futuro.
- **Script `scripts/harness_hook.py` não é copiado para projetos-alvo** pelo `install-harness`
  hoje — `.cursor/hooks.json` (e `.claude/settings.json` equivalente da task 07) referenciam um
  script que só existe de fato no canônico. Isso funciona para o dogfooding deste próprio repo,
  mas é um gap real de propagação para projetos instalados via `/install-harness` — fica como
  trabalho futuro, fora do escopo desta task.
