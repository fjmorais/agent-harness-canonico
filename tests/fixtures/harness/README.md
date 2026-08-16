# Fixtures — `.harness/` (task 15)

Fixtures estáticas versionadas, seguindo o padrão já usado por
`.claude/skills/install-harness/scripts/stack_map.json` (mesmo espírito: dado de teste
reproduzível em disco, não construído em runtime a cada execução — decisão do grill,
Pergunta 13). Cada pasta abaixo é um `.harness/` (e, quando relevante, `.claude/`/`.cursor/`)
completo, pronto para ser apontado por `diagnose()`/`rebuild_timeline()`/etc. nos testes.

| Fixture | Cenário (seção 7 do plano original) | Task/teste que a exercita |
|---|---|---|
| `v1-fresh/` | Instalação nova (diretório vazio) | Coberto via `tmp_path` + `apply_harness_scaffold` diretamente nos testes da task 03 (`tests/test_harness_scaffold.py`, `tests/test_install_harness_scaffold_integration.py`) — esta pasta ficou como placeholder, não usada diretamente por nenhum teste hoje. |
| `v1-legacy/` | Projeto legado (`schema_version` mais antigo que N-1) | `tests/test_harness_fixtures_suite.py::test_legacy_project_is_reported_outdated` — `harness_doctor.diagnose()` (task 12/13) reporta `outdated`. |
| `v1-out-of-order-events/` | Eventos duplicados/fora de ordem | `tests/test_harness_fixtures_suite.py::test_out_of_order_events_are_reordered_consistently` — `rebuild_timeline()` (task 06) reordena corretamente mesmo com timestamps gravados fora de ordem no arquivo. |
| `v1-crash-recovery/` | Crash durante escrita (arquivo temporário órfão) | `tests/test_harness_fixtures_suite.py::test_orphaned_temp_file_from_crash_is_detected_and_reported` — `harness_doctor.detect_orphaned_temp_files()` (task 15) encontra e reporta o `.tmp` deixado para trás; nunca remove sozinho. |
| `v1-claude-cursor-mirror/` | Espelhamento `.claude/`/`.cursor/` | `tests/test_harness_fixtures_suite.py::test_claude_cursor_mirror_files_have_consistent_checksum` — prova consistência de conteúdo entre a regra `.md` e o `.mdc` espelhado. O checksum de `harness_doctor` (task 12) ainda não cobre `.claude/`/`.cursor/` (gap documentado nas Notes da task 12) — este teste valida o conteúdo diretamente, sem depender dessa extensão futura. |

## Cenários já cobertos por outras tasks (não duplicados aqui)

- **Update sem `.harness/`, update com logs existentes, migration aprovada/cancelada,
  preservação de customizações** — `tests/test_harness_update.py`, construídos via
  `apply_harness_scaffold` + `tmp_path` (não fixture estática — ver Notes da task 04).
- **Doctor em projeto completo/incompleto/customizado** — `tests/test_harness_doctor.py`,
  mesmo padrão `tmp_path`.

## Como regenerar

Estas fixtures foram geradas por um script one-off usando `apply_harness_scaffold` +
edições pontuais (não versionado como script separado — ver histórico do commit da task 15).
Se precisar recriar do zero, o padrão é: `apply_harness_scaffold(fixture_dir, "nome")`, depois
editar `config.json`/criar `runs/`/etc. conforme o cenário, e **remover o `.harness/.gitignore`
gerado** (fixtures são dados estáticos de teste — precisam de `runs/`/`audit/`/`indexes/`
versionados, ao contrário de uma instalação real).
