# Update seguro de `.harness/` existente

**Status:** not started
**Blocked by:** 03-scaffold-projeto-novo.md

## What to build

Estender `install_harness.py` para detectar um `.harness/` já existente (via `config.json` ou
manifest) e aplicar update em vez de scaffold do zero: criar somente itens ausentes, nunca
apagar/truncar/substituir `runs/`, `audit/`, `deliveries/` já gravados, preservar `project_id` e
configuração custom, listar migrations de schema necessárias (comparando `schema_version` do
projeto com o publicado no canônico) com `requires_confirmation: true`, aplicar migration só
após confirmação explícita, fazer backup antes de qualquer migration estrutural, atualizar
`installed-files.json` (fingerprint) sem perder entradas de arquivos preservados/customizados.

## Acceptance criteria

- [ ] Rodar o instalador contra um projeto com `.harness/` de versão anterior e `runs/` já
      populado preserva `runs/` intacto (nenhum arquivo removido ou reescrito) — tested by:
      teste de integração usando fixture `tests/fixtures/harness/v1-with-runs/`, comparando
      hash dos arquivos de `runs/` antes e depois.
- [ ] `project_id` e `config.json` custom (ex.: `retention.days` alterado manualmente) não são
      sobrescritos pelo update — tested by: teste de integração com fixture tendo config
      customizado, validando que o valor customizado sobrevive ao update.
- [ ] Uma migration de schema pendente é listada no modo `--json` com `requires_confirmation:
      true` e só é aplicada após uma segunda chamada de confirmação — tested by: teste de
      integração simulando os dois passos (plan → confirm) e validando que nada muda entre eles.
- [ ] Cancelar uma migration proposta não deixa o projeto em estado inconsistente — tested by:
      teste de integração que roda o plan, não confirma, e valida que `.harness/` permanece
      exatamente como estava antes.
- [ ] Backup é criado antes de aplicar uma migration estrutural — tested by: teste de
      integração verificando a existência do backup após uma migration simulada.

## Notes

Reaproveita a lógica de fingerprint da task 03 para decidir o que é "customizado" (protegido)
vs. "gerado pelo instalador" (atualizável).
