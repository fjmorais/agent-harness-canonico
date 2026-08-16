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
- [x] `capabilities.telemetry.cursor: true` é declarado no manifest quando (e só quando)
      `scripts/harness_hook.py` está de fato alcançável no projeto-alvo; caso contrário
      `"unavailable"`, nunca `true` incondicional — tested by: dois testes unitários, um por
      ramificação (script ausente → `unavailable`; script presente → `true`).

## Notes

Ver `docs/adr/002-viabilidade-hooks-cursor.md` para a pesquisa completa (fonte:
https://cursor.com/docs/hooks, 2026-08-16) e a tabela de equivalência de eventos. O ADR também
registra um risco residual: o spike não testou hooks Cursor rodando de verdade, só leu
documentação — esta task deve validar contra uma sessão Cursor real antes de fechar, não confiar
só na simulação de payload.

**Bloqueante corrigido (revisor-codigo, 2026-08-16):** a primeira versão gravava
`capabilities.telemetry.cursor: true` incondicionalmente, sempre que `.cursor/hooks.json` era
gerado — mesmo em projetos-alvo reais onde `scripts/harness_hook.py` **não existe** (não é
propagado pelo `install-harness`, ver abaixo). `harness_doctor.py` trata `true` como `ok` sem
verificação adicional, então isso era exatamente o tipo de "zero silencioso"/valor fabricado que
a task 12 existe para evitar — uma capability declarada ok que na prática nunca produz evento
nenhum. O revisor apontou corretamente que isso não é o mesmo tipo de dívida técnica aceitável
das ressalvas anteriores (que documentavam incompletude sem fazer o manifest mentir) — é uma
afirmação ativamente falsa para o caso de uso principal do feature.

**Correção aplicada:** `_enable_cursor_telemetry_capability()` agora checa se
`scripts/harness_hook.py` está de fato alcançável em `target/scripts/harness_hook.py` antes de
declarar `true` — caso contrário declara `"unavailable"` (formato já suportado pelo schema desde
a task 02). Na prática, hoje isso significa: `true` só quando o alvo é o próprio canônico
(dogfooding, onde o script já existe); `"unavailable"` em qualquer instalação real via
`/install-harness`, honestamente, até a propagação do script existir.

**Correção de uma alegação errada:** a nota anterior dizia "mesmo padrão simplificado já usado
para `telemetry.claude_code` nas tasks anteriores" — o revisor verificou que isso é falso:
`capabilities.telemetry.claude_code` nunca é setado por código de produção em lugar nenhum do
repositório (só aparece em fixtures/testes). Não havia precedente — esta nota estava incorreta e
foi removida.

**Riscos residuais explícitos (não resolvidos por esta task):**
- **Nunca testado contra uma sessão Cursor real** — toda a suíte de testes usa payloads
  simulados fielmente à documentação (`docs/adr/002...`), não uma sessão Cursor de verdade
  disparando o hook. Se o payload real divergir do documentado, o adapter pode falhar
  silenciosamente (mitigado pela mesma barreira de exceção do `main()` — nunca quebra a sessão
  do usuário, mas também pode nunca gravar evento nenhum sem ninguém perceber).
- **`provider` para eventos Cursor é setado igual ao nome do executor** (`"cursor"`), não ao
  provider real do modelo em uso (Cursor suporta múltiplos providers) — simplificação por falta
  de sinal confiável no payload documentado; refinar se o campo `model`/`model_id` do payload
  base do Cursor precisar ser exposto no futuro.
- **Script `scripts/harness_hook.py` não é copiado para projetos-alvo** pelo `install-harness`
  hoje — este é o gap real de propagação, agora honestamente refletido no manifest (`unavailable`
  em vez de `true` fabricado). Propagar o script (e suas dependências: `harness_event_writer.py`,
  `harness_redact.py`, `harness_scaffold.py`, `harness_deliveries.py`, `schema_validation.py`,
  `schemas/*.json`) pra projetos-alvo fica como trabalho futuro — só então `telemetry.cursor`
  (e, pela mesma lógica, `telemetry.claude_code`) poderiam legitimamente virar `true` fora do
  dogfooding deste canônico.
- `docs/adr/002-viabilidade-hooks-cursor.md` sinalizou que Cursor tem `tool_use_id`/
  `conversation_id` estáveis — mais informação de correlação do que o Claude Code expõe hoje.
  Não aproveitado aqui; `correlation_id` continua `None` fixo mesmo no caminho Cursor.
