# Wireear assert_write_compatible nos writers reais

**Status:** done
**Blocked by:** 13-compatibilidade-schema.md

## What to build

A task 13 criou `assert_write_compatible()`/`is_schema_version_newer()`
(`scripts/schema_validation.py`) — função pura testada isoladamente, mas **nenhum writer real a
chama hoje**: `write_event()` (`harness_event_writer.py`), `apply_harness_scaffold()`/
`apply_harness_update()` (`harness_scaffold.py`) continuam gravando sem checar a versão pinned
do projeto. Um payload com `schema_version` mais nova que o pinned ainda é gravado
silenciosamente, exatamente como antes da task 13 — o guard existe mas não protege nada em
produção.

Esta task fecha essa lacuna: passar `project_path`/versão pinned para os writers reais e chamar
`assert_write_compatible()` antes de cada escrita, decidindo o que fazer com a exceção em cada
ponto de chamada (hook engolindo com a barreira já existente em `harness_hook.py:main()`? ou
propagando pro caller explicitamente em chamadas diretas de biblioteca?).

## Acceptance criteria

- [x] `write_event()` rejeita um evento com `schema_version` mais nova que a versão pinned do
      projeto, sem gravar — tested by: teste de integração com fixture de projeto + evento
      divergente.
- [x] `apply_harness_update()` aplica o mesmo guard antes de recriar `state/current-workflow.json`
      (único arquivo recriável com `schema_version` embutido) — tested by: teste unitário com
      config pinned mais antigo, confirmando que o arquivo é pulado (não abortando o batch
      inteiro, mesmo padrão da task 09) e reportado em `skipped_incompatible`. **Escopo ajustado
      em relação ao texto original:** `apply_harness_scaffold()` não foi guardado — na primeira
      instalação não existe pin pré-existente pra violar (é o próprio scaffold que estabelece o
      baseline); `config.json`/`state/project.json` não são "recriáveis" pelo update (são
      assumidos presentes sempre que `is_harness_installed()` é true), então o guard nesta task
      se aplica ao único arquivo do update que de fato carrega `schema_version` e pode ser
      recriado: `state/current-workflow.json`.
- [x] Assinaturas mudadas não quebram nenhum dos ~110 testes existentes que já chamam esses
      writers — tested by: suíte completa (`uv run pytest -q`) permanece verde.
- [x] `harness_hook.py` continua nunca propagando exceção pro Claude Code (barreira do `main()`
      já existente cobre o novo caminho de erro) — tested by: teste de integração com payload de
      schema divergente via stdin, confirmando exit 0 + log em stderr.

## Notes

Levantada como ressalva pelo revisor-codigo na revisão da task 13 (2026-08-16): "a proteção
continua inexistente na prática... isso deveria ganhar rastreamento formal". Ver
`tasks/13-compatibilidade-schema.md` § Notes para o racional original de por que o wiring foi
adiado (mudar assinatura de writer usado em 90+ testes exigia planejamento, não encaixava no
ritmo da execução sequencial das tasks 01-15).

**Como o wiring foi feito, sem quebrar assinatura de nenhum caller existente:**
`write_event(run_dir, writer_id, event)` manteve a mesma assinatura — em vez de receber
`project_path`/versão pinned como parâmetro novo (que exigiria mudar toda chamada existente),
`_find_pinned_schema_version()` sobe a árvore a partir de `run_dir` procurando um `.harness/
config.json` ancestral. Quando não encontra (testes que chamam `write_event` com um `run_dir`
solto, ex.: `tmp_path` direto), o guard fica desligado — comportamento idêntico ao pré-task-16,
satisfazendo o AC3 sem exigir migrar os ~110 testes existentes.

**Limitação conhecida do teste de "schema mais novo":** `execution-event.schema.json` trava
`schema_version` em `const: "1.0"` (só existe uma versão publicada hoje) — não é possível
construir um evento genuinamente "mais novo" que passe na validação de schema básica. Os testes
desta task simulam a divergência rebaixando o **pinned** do projeto (`config.json.schema_version
= "0.9"`) em vez de subir o do evento, o que exercita exatamente a mesma comparação
(`is_schema_version_newer`) e o mesmo caminho de código — só inverte qual lado do teste é
manipulado. Quando um schema v1.1 real existir um dia, valeria revisitar com um teste mais
direto.
