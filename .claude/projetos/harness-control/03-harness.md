# Harness Control — Decisões de Harness

> Nota: `/harness-architect` não rodou neste projeto — não há `.claude/` de projeto-filho a
> montar. Este é o próprio canônico evoluindo, então "harness montado" aqui significa: PRD
> publicado + ADR registrada, prontos para virar tasks de implementação nos artefatos do
> canônico (schemas, scripts, ajustes no `install-harness` existente).

## O que foi produzido nesta fase

### PRD
`PRD.md` (raiz) + cópia em `.claude/projetos/harness-control/02-prd.md` — 22 user stories,
decisões de implementação e teste cobrindo as 14 decisões arquiteturais do grill.

### ADR
`docs/adr/001-observabilidade-harness-control.md` — registra as decisões que divergem do
plano original (`sketch/agent-harness-canonico/plan.md`): run=sessão em vez de run=turno,
arquivo-por-escritor em vez de lock único, sem `pricing.json` local, redaction só no caminho
de hook, `project_id` por hash imutável.

### Artefatos que serão criados na fase de implementação (não ainda)
- `schemas/*.schema.json` (manifest, config, project-state, workflow-state, run,
  execution-event, usage, run-result, delivery-record, compatibility)
- `scripts/harness_doctor.py`, `scripts/harness_redact.py`, `scripts/harness_prune.py`
  (mesmo padrão de `.claude/skills/install-harness/scripts/install_harness.py`)
- Extensão de `install_harness.py` para scaffold `.harness/`
- Hooks em `.claude/settings.json` (novos, específicos deste projeto de evolução — não
  confundir com os hooks que `install-harness` propaga para projetos-filhos)
- `tests/scripts/fixtures/harness/` (v1-fresh, v1-with-runs, v1-customized, etc.)

## Decisões contestáveis (ver docs/adr/001 para detalhes)
- Run = sessão inteira (não turno, não task individual)
- Sem cálculo de custo em `$` local — só tokens brutos por modelo
- Redaction só no caminho de hook, não no caminho de agente
- `harness-doctor` com checksum de `.claude/` + `.cursor/` completos, não só `.harness/`
- Cursor entra no MVP condicionado a spike de viabilidade (hooks equivalentes não confirmados)

## Próximo passo
Rode `/to-tasks` para fatiar o PRD em tasks implementáveis, seguindo a ordem de fases
C0 (contratos) → C1 (instalador observável) → C2 (telemetria) → C3 (compatibilidade).
