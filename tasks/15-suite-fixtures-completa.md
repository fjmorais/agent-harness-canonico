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
- [x] Fixture de "espelhamento `.claude/`/`.cursor/`" existe e a consistência de conteúdo entre
      as duas árvores é testada diretamente (corpo da regra `.md` idêntico ao corpo do `.mdc`
      espelhado) — tested by: teste de integração com a fixture nova. **Escopo ajustado
      (revisor-codigo, 2026-08-16):** o checksum do `harness_doctor` (task 12) ainda não cobre
      `.claude/`/`.cursor/`, só `.harness/` — esse é um gap de escopo já documentado nas Notes
      da task 12, não resolvido aqui. O texto original deste critério afirmava que "o checksum
      cobre as duas árvores", o que não é verdade; corrigido para refletir o que foi de fato
      entregue e testado.
- [x] Todas as fixtures da seção 7 do plano original estão listadas em
      `tests/fixtures/harness/README.md` com o cenário que cada uma cobre e a task/teste que a
      exercita — no test — é um documento de rastreabilidade, não código executável.

## Notes

Esta é a task de fechamento do critério de saída do plano original (seção 8): "um projeto novo
e um existente podem ser instalados/atualizados sem perda de dados, passam pelo doctor de
observabilidade e são consumíveis pelo Control somente através dos contratos publicados."

**Bloqueante corrigido (revisor-codigo, 2026-08-16):** o critério de aceite do espelhamento
`.claude/`/`.cursor/` afirmava que "o checksum (task 12) cobre as duas árvores de forma
consistente" — falso, o `harness_doctor` só fingerprinta arquivos dentro de `.harness/`. O teste
de fato entregue (`test_claude_cursor_mirror_files_have_consistent_checksum`) prova consistência
de *conteúdo* comparando os arquivos diretamente, não via doctor. Texto do critério corrigido
para refletir o escopo real. Estender o checksum do doctor pra `.claude/`/`.cursor/` continua
como trabalho futuro (mesmo gap já citado nas Notes da task 12).
