# Harness Control — evolução do canônico
Slug: harness-control
Iniciado em: 2026-08-15

## SI Assessment: Nível b — dados de usuário sem PII direto (run_id, métricas, logs de execução), redaction obrigatória de prompts/secrets/PII

## Tipo: e — Outro (Framework/Infraestrutura interna — evolução do agent harness canônico)

## Fase atual: 5 — Todas as 15 tasks originais concluídas, pronto para ship

## Checklist
- [x] 0. Ideia + SI assessment (2026-08-15)
- [x] 1. Grill concluído (2026-08-15)
- [x] 2. PRD gerado (2026-08-16)
- [x] 3. Harness montado — adaptado: PRD + ADR (não /harness-architect, ver 03-harness.md) (2026-08-16)
- [x] 4. Tasks criadas (15 tasks em tasks/, 2026-08-16)
- [x] 5. Implementação concluída (tasks 01-15, 2026-08-16 — ver tasks/README.md)
- [ ] 6. Ship / retrospectiva

## Nota sobre task 16

Uma 16ª task (`tasks/16-wire-schema-guard.md`) foi criada durante a implementação como
follow-up formal de uma ressalva do revisor-codigo (guard de compatibilidade de escrita da
task 13 não está wireado nos writers reais) — não fazia parte das 15 tasks originais do
`/to-tasks`. Fica em aberto, não bloqueia o ship desta iteração.
