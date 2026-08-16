# Scaffold `.harness/` para projeto novo

**Status:** not started
**Blocked by:** 01-schemas-core.md, 02-schemas-complementares.md

## What to build

Estender `install_harness.py` (script já existente, mesmo padrão de CLI + modo `--json`) para
criar o scaffold `.harness/` completo quando o projeto de destino não tem `.harness/` ainda:
`state/` (com `project.json` contendo `project_id` gerado por hash(path absoluto + timestamp de
criação) e `current-workflow.json` vazio), `runs/` vazio, `deliveries/` vazio,
`audit/audit.jsonl` vazio, `locks/`, `runtime/`, `indexes/` vazios, `README.md`, `config.json`
(com `retention.days` padrão, `telemetry` desligado por padrão até C2 configurar), manifest v2
atualizado em `.claude/harness-manifest.json` com `capabilities` declaradas, `.gitignore`
configurado (versiona `README.md`/`config.json`/`state/project.json`; ignora `runs/**`,
`audit/**`, `indexes/**`). Grava também o registro de fingerprint
(`state/installed-files.json`) com checksum de cada arquivo gerado — usado depois pelo
`harness-doctor` (task 12).

Tudo isso aparece no Install Plan antes de qualquer gravação (reaproveita o fluxo de confirmação
já existente do `install-harness`).

## Acceptance criteria

- [ ] Rodar o instalador contra um diretório sem `.harness/` cria a estrutura completa listada
      acima — tested by: teste de integração usando fixture `tests/fixtures/harness/v1-fresh/`
      (diretório de entrada vazio) e comparando a árvore de saída.
- [ ] `project_id` gerado é um hash determinístico de `path + timestamp`, gravado uma vez em
      `state/project.json` — tested by: teste unitário chamando a função de geração duas vezes
      com o mesmo input e validando que produz o mesmo hash.
- [ ] `.gitignore` gerado ignora exatamente `runs/**`, `audit/**`, `indexes/**` e versiona
      `README.md`, `config.json`, `state/project.json` — tested by: teste unitário lendo o
      `.gitignore` gerado e checando os padrões.
- [ ] `state/installed-files.json` contém checksum de todo arquivo gerado pelo scaffold —
      tested by: teste de integração que recalcula o hash de um arquivo gerado e compara com o
      valor registrado.
- [ ] Install Plan exibe a estrutura completa antes de gravar qualquer arquivo — tested by:
      teste de integração no modo `--json`, verificando que a resposta de "plan" lista todas as
      operações antes de `--apply`.

## Notes

Ver ADR-001 (Opção K) para o racional de `project_id` por hash imutável. O `telemetry` desligado
por padrão no `config.json` evita que hooks tentem escrever antes de C2 estar implementado.
