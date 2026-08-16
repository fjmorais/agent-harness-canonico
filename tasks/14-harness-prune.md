# `harness_prune.py` — retenção manual confirmada

**Status:** not started
**Blocked by:** 03-scaffold-projeto-novo.md

## What to build

Script `scripts/harness_prune.py` (CLI, `--dry-run` como padrão) que lê `retention.days` de
`config.json`, identifica runs em `runs/YYYY/MM/run_<id>/` mais velhos que a janela de
retenção, lista o que seria removido, e só remove após confirmação explícita (`--confirm`,
nunca automático — ver `rules/seguranca.md` e a decisão do grill de manter isso já no MVP,
apesar de `runs/**` não ter backup no Git).

## Acceptance criteria

- [ ] `--dry-run` (padrão) lista os runs que seriam removidos, sem apagar nada — tested by:
      teste de integração com fixture de `runs/` contendo entradas antigas e recentes,
      validando que nenhum arquivo é removido após `--dry-run`.
- [ ] Sem `--confirm`, nenhuma exclusão ocorre mesmo se o usuário rodar sem `--dry-run` — tested
      by: teste de integração verificando que a flag de confirmação é obrigatória para remover.
- [ ] Com `--confirm`, apenas os runs fora da janela de retenção são removidos; runs recentes
      permanecem intactos — tested by: teste de integração com fixture mista, validando a lista
      final de runs após execução confirmada.
- [ ] O script nunca toca `runs/**` de outro projeto (escopo restrito ao `.harness/` do projeto
      apontado) — tested by: teste de integração com dois projetos fixture, validando que só um
      é afetado.

## Notes

Ver ADR-001 seção "Riscos" — `harness-prune` entra já no MVP por decisão explícita do usuário no
grill, mesmo sem backup em Git para `runs/**`.
