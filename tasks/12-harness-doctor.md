# `harness_doctor.py` — diagnóstico honesto por capability

**Status:** not started
**Blocked by:** 03-scaffold-projeto-novo.md, 04-update-seguro.md

## What to build

Script `scripts/harness_doctor.py` com função pura `diagnose(project_path: Path) -> dict` que
recalcula checksum de todo arquivo registrado em `state/installed-files.json` (tasks 03/04),
compara com o valor gravado, e reporta por capability declarada no manifest:
`ok` (checksum bate), `missing` (arquivo esperado não existe), `outdated` (versão de schema fora
da janela N/N-1 — ver task 13), `customized` (checksum diferente do registrado), `blocked`
(pré-condição não satisfeita, ex.: `.harness/` corrompido), `unavailable` (capability não
suportada pelo executor, com motivo). Nunca preenche métrica ausente com zero ou estimativa —
lacuna sempre explícita.

## Acceptance criteria

- [ ] Projeto com todos os arquivos intactos reporta `ok` para todas as capabilities — tested
      by: teste de integração com fixture `tests/fixtures/harness/v1-fresh/` pós-instalação.
- [ ] Projeto com um arquivo do harness editado manualmente reporta `customized` só para aquele
      arquivo/capability, não para o projeto inteiro — tested by: teste de integração usando
      fixture `tests/fixtures/harness/v1-customized/`.
- [ ] Projeto com um diretório esperado ausente (ex.: `.harness/audit/` nunca criado) reporta
      `missing` para a capability correspondente — tested by: teste de integração com fixture
      incompleta.
- [ ] Capability de um executor sem adapter (ex.: Cursor, se a task 11 concluir inviável)
      reporta `unavailable` com motivo, nunca `missing` — tested by: teste unitário com manifest
      declarando `unavailable` explicitamente.
- [ ] Nenhuma chamada a `diagnose()` retorna um valor numérico (ex.: contagem de eventos) como
      `0` quando o dado real é "não sei" — tested by: teste unitário verificando que ausência de
      dado produz `null`/`"unavailable"`, nunca `0`.

## Notes

Reforça a "regra de honestidade" da seção 5 do plano original e da Pergunta 6 do grill.
