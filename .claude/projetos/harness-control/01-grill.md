# Harness Control — Grill & Requisitos

## Contexto (da sessão /grill-me)

### Problema

O canônico (`/home/fabiano/agent-harness-canonico`) hoje produz artefatos de framework (agents,
skills, rules, KBs) e um instalador (`/install-harness`), mas não deixa nenhum projeto instalado
**observável**: não há estado estruturado, eventos de execução, custos, entregas ou auditoria em
formato consumível por um sistema externo. Sem isso, um futuro produto — o **Harness Control** —
não tem como mostrar runs, custos ou saúde de instalação de nenhum projeto, e hoje a única fonte
de dado sobre entregas é `metrics/entregas.jsonl`, que cobre só uma fatia (task concluída), não
execução em si (tool calls, tokens, sessões).

Este projeto não constrói o Harness Control (fora de escopo, seção "Out of Scope") — constrói a
camada de contratos e instrumentação no canônico que torna qualquer projeto instalado consumível
por ele, sem acoplar código de produto/web neste repositório.

### Usuários

Persona única nesta fase: **o próprio mantenedor do harness canônico** (uso interno) — quem evolui
o canônico e vai eventualmente construir/operar o Harness Control sobre os dados que este projeto
passa a produzir. Não há usuário externo consumindo isso diretamente ainda; "outros desenvolvedores
que instalam o harness" se beneficiam indiretamente (harness-doctor, observabilidade), mas não são
o público que dirige as decisões de design desta fase.

### Objetivos (MoSCoW)

**MUST:**
- Schemas versionados (`schema_version` próprio, independente da versão do harness) para: manifest,
  config, evento, run, usage, delivery, compatibility.
- `.harness/` scaffoldado por `/install-harness` em projeto novo e existente, sem perda de dado em
  update.
- Eventos de execução (`events.jsonl`) emitidos via caminho híbrido: hooks do Claude Code para
  telemetria objetiva (tool calls, tokens, exit codes), agente para eventos de workflow
  (gate/revisor/task concluída).
- `harness-doctor` reportando `ok`/`missing`/`outdated`/`customized`/`blocked`/`unavailable` por
  capability, nunca preenchendo métrica ausente com zero silencioso.
- Redaction de PII/prompt no caminho de hook antes de qualquer escrita.
- Compatibilidade de schema N e N-1, com `config.json` fixando a versão em uso até migration
  explícita.

**SHOULD:**
- Adapter de telemetria funcionando para Cursor (além de Claude Code) já no MVP — sujeito a
  validação de viabilidade (ver Restrições).
- `harness-prune` manual com confirmação para aplicar `retention.days`.
- Fixtures de teste versionadas cobrindo os cenários da seção 7 do plano original.

**COULD:**
- Cálculo de custo em `$` (fora de escopo agora — só tokens brutos por modelo; preço fica pro
  Control).
- Adapters para Codex, Kimi e outros executores (explicitamente adiado).

### Out of Scope

- Frontend/backend web do Harness Control, login, RBAC, PostgreSQL do Control.
- Seleção visual de pastas, dashboards, execução pela web, administração multiusuário.
- Cálculo/armazenamento de preço em `$` dentro de cada projeto instalado (`pricing.json` local).
- Adapters de telemetria para Codex, Kimi e outros executores além de Claude Code + Cursor.
- Exclusão automática de dados por retenção (sempre manual e confirmada).

### Restrições

- **Técnica — multi-executor:** MVP cobre Claude Code (hooks nativos `SessionStart`/`SessionEnd`/
  `PreToolUse`/`PostToolUse`/`SubagentStop`) e Cursor. **Risco de viabilidade não resolvido:** não
  há confirmação de que o Cursor expõe hooks equivalentes — precisa de spike de validação antes de
  comprometer o adapter de Cursor no C2. Se inviável, Cursor cai para caminho "agente escreve" ou
  fica `unavailable` no doctor, sem travar o resto do plano.
- **Técnica — escrita concorrente:** subagentes rodam em paralelo dentro da mesma sessão (mesmo
  `run_id`) e podem disparar hooks concorrentes — resolvido com um arquivo de eventos por escritor
  dentro do run (nunca lock em `events.jsonl`), mesclado por reconstrução via `sequence`/
  `parent_event_id`/`correlation_id`.
- **Invariante do canônico:** nenhum código de produto aqui — scripts (`harness-redact`,
  `harness-doctor`, `harness-prune`) seguem o precedente já existente de `install_harness.py`
  (ferramenta de framework, não produto).
- **Segurança:** exclusão de dados nunca automática (regra de operação destrutiva de
  `rules/seguranca.md`); `runs/**` não tem backup no Git (está no `.gitignore`), então qualquer
  prune tem que ser confirmado.
- **Performance:** sem SLA numérico formal — só a expectativa qualitativa de que hooks não
  introduzam latência perceptível na experiência de uso do Claude Code no dia a dia.

## Especificações implícitas detectadas

**2 — Concorrência:** duas ou mais sessões (ou subagentes na mesma sessão) podem escrever eventos
ao mesmo tempo. Resolvido: run = sessão (lock por run, não por projeto inteiro); dentro do run,
um arquivo de eventos por escritor (main agent / cada subagente) evita colisão sem precisar de
lock — mesclagem acontece só na leitura/reconstrução.

**3 — Idempotência:** reprocessamento de `events.jsonl` (ex.: rebuild de `indexes/`) precisa ser
idempotente — já é uma exigência textual do plano original (seção 6), mantida como invariante;
como os arquivos JSONL nunca são reescritos e a reconstrução é sempre a partir do histórico
completo, reprocessar duas vezes produz o mesmo índice.

**4 — Autenticação/Autorização:** N/A — não há multi-tenant nem multi-usuário nesta fase; o
`.harness/` de um projeto é de escopo local/single-user, sem isolamento de dados entre usuários
a resolver aqui (seria problema do Control, se algum dia existir).

**5 — Dados sensíveis não declarados:** coberto pelo SI Assessment (nível b) e pela decisão de
redaction só no caminho de hook — eventos de agente (workflow) são estruturalmente proibidos de
carregar campo de texto livre, então não têm superfície pra vazar PII não declarada.

**6 — Abuso e limites:** N/A — sistema de arquivos local, single-user, sem exposição de rede;
não há rate limiting ou quota a desenhar.

**7 — Auditoria:** coberto nativamente pelo design — `audit/audit.jsonl` é um dos artefatos
centrais do plano original (seção 2), e todo evento já carrega `event_id`, `occurred_at`,
`sequence`, `correlation_id`.

**8 — Estados de erro visíveis:** coberto pela "regra de honestidade" do `harness-doctor` — nunca
preencher métrica ausente com zero ou estimativa silenciosa; sempre reportar `unavailable`/
`blocked` com motivo explícito.

**9 — Ciclo de vida dos dados:** coberto por `retention.days` + `harness-prune` manual confirmado,
decidido para entrar já no MVP (não adiado para C3 como sugerido inicialmente).

**10 — Dependência de terceiros mudando:** coberto pela política de compatibilidade N/N-1 —
validação em dois pontos (escrita fixa a versão em `config.json`; leitura/doctor reporta
`outdated` se a versão sair da janela suportada).

**1 — Falha de dependência externa:** N/A — este projeto não depende de nenhuma API/serviço
terceiro em runtime (ao contrário do `adversarial-judge`, que depende de OpenRouter mas é uma
skill separada, não parte deste plano).

## Critérios de sucesso mensuráveis

- Um projeto **novo** instalado via `/install-harness` produz `.harness/` completo (scaffold +
  schemas + manifest v2) sem intervenção manual além da confirmação do Install Plan.
- Um projeto **existente** com `.harness/` de versão anterior é atualizado sem perda de
  `project_id`, configuração ou histórico de runs/eventos já gravados.
- `harness-doctor` roda em um projeto e reporta status honesto (nunca zero silencioso) para cada
  capability declarada no manifest.
- Uma sessão real do Claude Code (com pelo menos 1 subagente em paralelo) gera `events.jsonl`
  válidos contra o schema publicado, sem corrupção nem perda de evento por concorrência.
- `metrics/entregas.jsonl` continua sendo a fonte de verdade para `/scorecard`; nenhuma
  regressão no fluxo `harness-build` existente.

## Próximo passo

Rode `harness-design` para gerar o PRD e montar o harness.
