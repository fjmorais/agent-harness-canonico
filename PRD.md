# PRD — Harness Control: instrumentação observável do Agent Harness Canônico

> Slug do projeto: `harness-control`. Ver histórico completo em
> `.claude/projetos/harness-control/` (00-ideia.md, 01-grill.md).

## Problem Statement

Hoje o Agent Harness Canônico gera agents, skills, rules e KBs, e instala tudo isso em projetos
via `/install-harness` — mas nenhum projeto instalado fica **observável**. Não existe estado
estruturado, evento de execução, custo por sessão/task, ou trilha de auditoria em formato
consumível por uma ferramenta externa. A única fonte de dado sobre entregas hoje é
`metrics/entregas.jsonl`, que cobre só "task concluída" — não cobre execução em si (sessões,
tool calls, tokens, subagentes rodando em paralelo).

Sem essa camada, um futuro produto de observabilidade (o "Harness Control") não tem nenhum dado
real pra consumir, e o próprio mantenedor do canônico não tem visibilidade sobre custo, saúde de
instalação, ou o que realmente aconteceu numa sessão de trabalho além do que já é registrado
manualmente em Markdown.

## Solution

Evoluir o canônico para produzir, em cada projeto instalado, uma estrutura `.harness/` observável
e schemas versionados publicados no próprio canônico — sem que nenhum código de produto/web do
futuro Harness Control entre neste repositório. O canônico continua sendo framework: cria,
preserva e valida as estruturas operacionais; quem lê e apresenta esses dados é responsabilidade
de outro sistema, fora de escopo aqui.

A instrumentação usa uma estratégia híbrida de emissão de eventos — hooks nativos do executor
(Claude Code, e Cursor quando viável) para telemetria objetiva (tool calls, tokens, exit codes),
e os próprios agents/skills do harness para eventos de workflow de alto nível (gate verde, task
concluída, revisor aprovou) — reaproveitando o padrão que já existe hoje em `harness-build` →
`metrics/entregas.jsonl`.

Toda decisão de design nesta solução prioriza honestidade de dado (nunca preencher métrica
ausente com zero silencioso) e segurança de escrita (append-only, nunca reescrever histórico,
nunca excluir dado sem confirmação humana).

## User Stories

1. Como mantenedor do canônico, quero que `/install-harness` crie o scaffold `.harness/` completo
   num projeto novo, para que a estrutura observável exista desde o primeiro commit do projeto.
2. Como mantenedor do canônico, quero que `/install-harness` detecte um `.harness/` existente e
   crie só os itens ausentes, para que atualizar o harness nunca apague histórico já gravado.
3. Como mantenedor do canônico, quero que cada evento de execução carregue `schema_version`,
   `event_id`, `run_id`, `project_id`, `correlation_id` e `privacy`, para que qualquer consumidor
   futuro saiba interpretar e filtrar o dado sem ambiguidade.
4. Como mantenedor do canônico, quero que uma sessão inteira do Claude Code seja tratada como um
   `run_id`, com cada task/skill/comando de alto nível identificado por `correlation_id`, para que
   eu consiga reconstruir "quanto custou a task X" mesmo com run granular por sessão.
5. Como mantenedor do canônico, quero que o hook de sessão (`SessionStart`/`SessionEnd`) abra e
   feche o run, para que a captura de telemetria não dependa de cada skill lembrar de marcar
   início/fim manualmente.
6. Como mantenedor do canônico, quero que cada subagente rodando em paralelo escreva num arquivo
   de eventos próprio dentro do run, para que escritas concorrentes nunca corrompam ou percam
   evento.
7. Como mantenedor do canônico, quero um passo de reconstrução que mescle os arquivos de eventos
   de um run em uma timeline ordenada, para que eu consiga ler "o que aconteceu nesta sessão" de
   forma coerente mesmo com múltiplos escritores.
8. Como mantenedor do canônico, quero que qualquer evento emitido pelo caminho de hook passe por
   redaction antes de ser gravado, para que prompt/PII/secret nunca cheguem a `events.jsonl` sem
   máscara.
9. Como mantenedor do canônico, quero que eventos emitidos pelo caminho de agente sejam
   estruturalmente limitados a enums/booleans/contadores (sem campo de texto livre), para que essa
   via nunca precise de redaction porque não tem superfície pra vazar PII.
10. Como mantenedor do canônico, quero que `usage.json` registre tokens brutos (input, output,
    cache read/write, reasoning) quebrados por `model_id` dentro do mesmo run, para que eu veja o
    consumo real mesmo quando o roteamento de modelo está em "auto".
11. Como mantenedor do canônico, quero que nenhum preço em `$` seja calculado ou armazenado
    localmente em `.harness/costs/`, para que eu nunca tenha uma estimativa de custo desatualizada
    silenciosamente — o cálculo de preço fica no consumidor externo dos dados.
12. Como mantenedor do canônico, quero rodar um `harness-doctor` que reporte, por capability,
    `ok`/`missing`/`outdated`/`customized`/`blocked`/`unavailable`, para que eu saiba exatamente o
    que está funcionando sem depender de inspeção manual de arquivos.
13. Como mantenedor do canônico, quero que `customized` seja detectado por checksum de todo
    arquivo que o instalador gerou (em `.claude/` e `.cursor/`), para que uma mudança manual minha
    nunca seja sobrescrita silenciosamente pelo instalador.
14. Como mantenedor do canônico, quero que `deliveries/deliveries.jsonl` seja derivado de
    `metrics/entregas.jsonl` (não o contrário), para que o fluxo `harness-build` → `/scorecard`
    já existente continue sendo a fonte de verdade sobre entregas.
15. Como mantenedor do canônico, quero que `project_id` seja um hash do path absoluto + timestamp
    de criação, calculado uma única vez e nunca recalculado, para que mover o projeto de pasta não
    quebre a identidade estável do projeto.
16. Como mantenedor do canônico, quero um script `harness-prune` que só remove runs além da
    retenção configurada após listagem + confirmação explícita, para que exclusão de dado sem
    backup no Git nunca aconteça automaticamente.
17. Como mantenedor do canônico, quero que o canônico valide compatibilidade de schema em dois
    pontos — na escrita (contra a versão fixada em `config.json`) e na leitura/doctor (dentro da
    janela N/N-1) —, para que uma migration de schema seja sempre explícita, nunca implícita.
18. Como mantenedor do canônico, quero fixtures estáticas versionadas cobrindo os cenários de
    instalação nova, update, migration, crash e doctor, para que cada mudança futura no instalador
    seja validada automaticamente contra esses cenários.
19. Como mantenedor do canônico, quero que o adapter de telemetria cubra Claude Code no MVP, com
    Cursor como meta condicionada a um spike de viabilidade (confirmar se o Cursor expõe hooks
    equivalentes), para que o escopo do MVP não dependa de uma suposição não validada.
20. Como mantenedor do canônico, quero que adapters para Codex, Kimi e outros executores fiquem
    explicitamente fora do MVP, para que o esforço inicial não se disperse antes de ter um adapter
    funcionando bem.
21. Como mantenedor do canônico, quero que `.harness/state/current-workflow.json` registre só
    estado de execução ativa (run/subagente em andamento), sem duplicar a fase do projeto que já
    vive em `STATUS.md`, para que as duas fontes não divirjam.
22. Como mantenedor do canônico, quero que a ordem de implementação siga as fases C0 (contratos)
    → C1 (instalador observável) → C2 (telemetria) → C3 (compatibilidade), com C0 completo antes
    de qualquer código de hook/instalador, para que decisões de schema não precisem ser refeitas
    depois de já haver código escrito contra elas.

## Implementation Decisions

### Estrutura de dados por projeto instalado

`.harness/` scaffoldado ao lado de `.claude/`, `.cursor/`, `metrics/`:
`state/` (estado de projeto e de execução ativa), `runs/YYYY/MM/run_<id>/` (um por sessão, com
subpasta de eventos por escritor), `deliveries/` (view derivada de `metrics/entregas.jsonl`),
`audit/`, `locks/` (escopo reduzido a artefatos compartilhados entre runs — `indexes/`,
`current-workflow.json` —, nunca `events.jsonl`), `runtime/`, `indexes/` (reconstruíveis).
JSON para estado/snapshot, JSONL para histórico append-only, Markdown para PRDs/ADRs/tasks
(inalterado).

### Schemas versionados

Publicados em `schemas/*.schema.json` no canônico, cada um com `schema_version` independente da
versão do harness: `harness-manifest`, `harness-config`, `project-state`, `workflow-state`, `run`,
`execution-event`, `usage`, `run-result`, `delivery-record`, `compatibility`. Removido do escopo
original: `cost-entry.schema.json` (substituído por tokens brutos dentro de `usage.schema.json`,
sem cálculo de preço local).

Envelope de evento mantém os campos do plano original (`schema_version`, `event_id`, `project_id`,
`run_id`, `source`, `provider`, `event_type`, `occurred_at`, `sequence`, `parent_event_id`,
`correlation_id`, `payload`, `privacy`), com a adição de `writer_id` (identifica qual escritor —
agente principal ou qual subagente — gerou o evento, necessário para a reconstrução multi-arquivo).

`usage.schema.json` muda de um campo `model` único para `usage_by_model: [{model_id, input,
output, cache_read, cache_write, reasoning}]`, permitindo granularidade por modelo mesmo quando o
roteamento está em modo automático.

### Run = sessão

Um run corresponde a uma sessão inteira do executor, aberto pelo hook `SessionStart` e fechado por
`SessionEnd` (nunca por `Stop`, que dispara a cada turno, não a cada sessão). Dentro do run,
`correlation_id` identifica a task/skill/comando de alto nível em execução, permitindo agregar
custo/resultado por task mesmo com run granular por sessão.

### Escrita concorrente

Cada escritor (agente principal, ou cada subagente disparado via `Task`) grava num arquivo de
eventos próprio dentro do run (`runs/.../events/<writer_id>.jsonl`), nunca compartilhando arquivo
entre escritores — elimina condição de corrida sem precisar de lock em `events.jsonl`. Um passo de
reconstrução mescla os arquivos do run em uma timeline ordenada por `sequence`/`occurred_at`/
`parent_event_id`, usado para popular `indexes/`.

Lock em `.harness/locks/` é escopo reduzido a artefatos verdadeiramente compartilhados entre runs
(`indexes/summary.json`, `state/current-workflow.json`) — nunca aplicado a `events.jsonl`.

### Redaction

Aplicada só no caminho de hook (telemetria objetiva, que pode conter path/prompt), antes de
qualquer escrita — nunca depois. O caminho de agente (eventos de workflow) é estruturalmente
limitado a enums/booleans/contadores no schema, sem campo de texto livre, então não carrega
superfície de PII e não precisa de redaction adicional.

### Custo e tokens

Sem `pricing.json` local nem cálculo de custo em `$` dentro de `.harness/`. `usage.json` registra
só tokens brutos, quebrados por `model_id` (necessário porque roteamento "auto" pode variar por
turno/subagente dentro da mesma sessão). Cálculo de preço é responsabilidade do consumidor externo
(fora de escopo deste repo).

### `harness-doctor`

Script novo (`scripts/harness_doctor.py`, mesmo padrão de `install_harness.py`) que recebe o path
de um projeto e retorna um relatório de status por capability declarada no manifest:
`ok`/`missing`/`outdated`/`customized`/`blocked`/`unavailable`. Detecção de `customized` via
checksum: o instalador grava um fingerprint de todo arquivo que gera (dentro de `.harness/`,
`.claude/` e `.cursor/`, respeitando o invariante de espelhamento já existente no `CLAUDE.md`) num
registro interno (`.harness/state/installed-files.json`); o doctor recalcula e compara. Nenhuma
métrica ausente é preenchida com zero ou estimativa — status `unavailable` sempre vem com motivo
explícito (ex.: "executor sem adapter configurado").

### Multi-executor

MVP cobre Claude Code (hooks nativos completos) e Cursor (condicionado a spike de validação —
confirmar se o Cursor expõe hooks de sessão/tool-call equivalentes; se não, cai para o caminho de
agente ou fica `unavailable`). Codex, Kimi e demais executores ficam fora do MVP. O manifest
declara `capabilities.telemetry` por executor, nunca globalmente — reporta honestamente quando um
executor não tem adapter.

### `project_id`

Gerado como `hash(path absoluto + timestamp de criação)` na primeira instalação, gravado em
`state/project.json`, tratado como imutável dali em diante (nunca recalculado, só lido) — mover o
projeto de pasta não afeta o ID porque ele não é recalculado.

### Relação com artefatos existentes

`deliveries/deliveries.jsonl` é derivado de `metrics/entregas.jsonl` (não substitui, não escreve
em paralelo) — um adapter traduz cada linha nova pro formato de observabilidade. `harness-build` e
`/scorecard` continuam funcionando exatamente como hoje, sem mudança de fluxo.
`state/current-workflow.json` registra só execução ativa (run/subagente em andamento, tipo
heartbeat), sem duplicar a fase do projeto (que continua em `STATUS.md` do fluxo SDD).

### Evolução do `/install-harness`

Projeto novo: cria scaffold `.harness/` completo, gera `project_id`, configura estados iniciais,
instala schemas/documentação do contrato, registra capabilities no manifest v2, configura
`.gitignore` (versiona `README.md`/`config.json`/`state/project.json`; ignora `runs/**`,
`audit/**`, `indexes/**`), grava fingerprints dos arquivos gerados, exibe tudo no Install Plan
antes de gravar. Projeto existente: detecta versão, cria só itens ausentes, nunca apaga/trunca
histórico, lista migrations de schema com `requires_confirmation`, faz backup antes de migration
estrutural, preserva customizações (via checksum).

### Retenção

`retention.days` (config por projeto) aplicado por um script `harness-prune` manual — lista o que
seria removido, pede confirmação explícita, só então apaga runs além da janela. Nunca automático
(runs não têm backup no Git).

### Compatibilidade de schema

Validação em dois pontos: na escrita, contra a versão fixada em `config.json` do projeto (que só
muda via migration explícita); na leitura (doctor, export), checando se a versão está dentro da
janela suportada (schema atual + uma versão anterior) — fora da janela, reporta `outdated`.

### Fases de entrega

C0 (contratos: ADR + todos os schemas + envelope de evento + estados de run) completo antes de
qualquer código de C1 (instalador observável), C2 (telemetria: hooks + redaction) e C3 (fixtures +
compatibilidade + `harness-prune` + `harness-doctor`).

## Testing Decisions

Bom teste aqui valida comportamento externo observável (schema válido, arquivo no lugar certo,
status reportado corretamente) — nunca detalhe de implementação interna do script.

- **Schemas**: validação pura contra fixtures (payloads válidos e inválidos por schema),
  sem I/O — roda em qualquer ambiente sem depender de sessão real do Claude Code.
- **`install_harness.py`** (extensão do script existente): testado pelo mesmo seam que já usa hoje
  (modo `--json`, entrada/saída determinística) — fixtures de projeto (`tests/fixtures/harness/
  v1-fresh/`, `v1-with-runs/`, `v1-customized/` etc.) cobrindo os cenários da seção 7 do plano
  original (instalação nova, update sem `.harness/`, update com logs existentes, migration
  aprovada/cancelada, preservação de customização).
- **`harness_doctor.py`**: testado como função pura `diagnose(project_path) -> status_report`
  contra as mesmas fixtures, cobrindo projeto completo, incompleto e customizado.
- **Escritor de evento**: testado como função pura `write_event(run_dir, writer_id, event) ->
  path`; concorrência testada simulando múltiplos escritores (threads/processos) no mesmo
  `run_dir` numa mesma execução de teste, sem depender dos hooks reais do Claude Code.
- **`harness_redact.py`**: testado com fixtures de payload contendo PII conhecida (CPF, email,
  path de usuário), validando que a saída nunca contém o valor original.
- **`harness_prune.py`**: testado com fixture de `runs/` + config de retenção, validando que
  `--dry-run` nunca apaga e que a exclusão real só ocorre após confirmação explícita simulada.
- **Prior art**: `install_harness.py` já é testável via `--json`/CLI sem TTY interativo — os
  scripts novos seguem o mesmo padrão (função pura + wrapper CLI fino).

## Out of Scope

- Frontend/backend web do Harness Control, login, RBAC, PostgreSQL do Control.
- Seleção visual de pastas, dashboards, execução pela web, administração multiusuário.
- Cálculo/armazenamento de preço em `$` (`pricing.json` local) — só tokens brutos.
- Adapters de telemetria para Codex, Kimi e outros executores além de Claude Code + Cursor.
- Exclusão automática de dados por retenção — sempre manual, sempre confirmada.
- `/harness-architect` não roda neste projeto — não há `.claude/` de projeto-filho a montar; a
  evolução acontece diretamente nos artefatos do canônico (schemas, scripts, ADR, ajustes no
  `install-harness` existente).

## Further Notes

- **Risco em aberto**: não há confirmação de que o Cursor expõe hooks de sessão/tool-call
  equivalentes ao Claude Code. Antes de comprometer o adapter de Cursor em C2, rodar um spike de
  validação; se inviável, Cursor cai para o caminho de agente ou fica `unavailable` no doctor, sem
  bloquear o resto do plano.
- **SI Assessment**: nível b (dados de usuário sem PII direto — run_id, métricas, logs de
  execução), com redaction obrigatória de prompt/secret/PII como invariante de design no caminho
  de hook. Não requer `[AVISO_LGPD]` completo nem `rules/pii.md` dedicado (isso seria nível c).
- Histórico completo da entrevista (14 decisões arquiteturais) em
  `.claude/projetos/harness-control/01-grill.md`.
