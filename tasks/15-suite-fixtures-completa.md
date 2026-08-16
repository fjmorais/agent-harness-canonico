# Suíte de fixtures completa (cenários de compatibilidade)

**Status:** done
**Blocked by:** 03-scaffold-projeto-novo.md, 04-update-seguro.md, 07-adapter-hooks-claude-code.md, 12-harness-doctor.md, 14-harness-prune.md

## What to build

Consolidar e completar as fixtures parciais criadas nas tasks anteriores em
`tests/fixtures/harness/`, cobrindo todos os cenários da seção 7 do plano original que ainda não
têm teste dedicado: instalação nova (já coberto por 03), update sem `.harness/` (já coberto por
04), update com logs existentes (já coberto por 04), migration aprovada e cancelada (já coberto
por 04), preservação de customizações (já coberto por 04/12), projeto legado (versão bem antiga
de schema), eventos duplicados/fora de ordem, crash durante escrita (arquivo temporário
órfão), rebuild de índices, doctor em projeto completo/incompleto/customizado (já coberto por
12), configuração de hooks/adapters sem sobrescrever customizações, espelhamento `.claude/`/
`.cursor/`.

## Acceptance criteria

- [x] Fixture de "projeto legado" (schema mais antigo que N-1) existe e o doctor a classifica
      `outdated` — tested by: teste de integração com a fixture nova.
- [x] Fixture de "eventos duplicados/fora de ordem" existe e `rebuild_timeline()` (task 06)
      produz uma ordem consistente mesmo assim — tested by: teste de integração com a fixture
      nova.
- [x] Fixture de "crash durante escrita" (arquivo temporário deixado para trás) existe e o
      instalador/doctor detecta e recupera (ou reporta) o temporário órfão — tested by: teste
      de integração com a fixture nova.
- [x] Fixture de "espelhamento `.claude/`/`.cursor/`" existe e o checksum (task 12) cobre as
      duas árvores de forma consistente — tested by: teste de integração com a fixture nova.
- [x] Todas as fixtures da seção 7 do plano original estão listadas em
      `tests/fixtures/harness/README.md` com o cenário que cada uma cobre e a task/teste que a
      exercita — no test — é um documento de rastreabilidade, não código executável.

## Notes

Esta é a task de fechamento do critério de saída do plano original (seção 8): "um projeto novo
e um existente podem ser instalados/atualizados sem perda de dados, passam pelo doctor de
observabilidade e são consumíveis pelo Control somente através dos contratos publicados."
