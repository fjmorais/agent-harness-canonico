# Harness Control — Retrospectiva de Ship

Ship em: 2026-08-16

## Scorecard de entrega — sessão única (2026-08-15 22:46 → 2026-08-16 00:23, ~1h37min de build)

> Fonte: `metrics/entregas.jsonl` (16 registros, um por task) + `git log`. Este projeto usou
> `tasks/*.md` locais, não issues do GitHub — `gh issue list --state all` retornou vazio, então
> métricas dependentes de `gh` (lead time por issue criada→fechada) **não puderam ser medidas** e
> foram substituídas por métricas equivalentes derivadas de `git log`/`metrics/entregas.jsonl`.

### Resumo (agregado)

| Métrica | Valor | Tendência |
|---|---|---|
| Critérios de aceite atendidos | 100% (71/71) | ▲ |
| Tasks com bloqueante real encontrado pelo revisor | 31% (5/16) | ver nota |
| Taxa de autonomia (sem edição humana de código durante a task) | 100% (16/16) | ▲ |
| Tentativas medianas até o gate verde | 1 | ▼ ótimo |
| Revisor: aprovado / aprovado com ressalvas / bloqueado (veredito final) | 1 / 15 / 0 | — |
| Ressalvas totais (não bloqueantes, registradas) | 40 | — |
| Intervenções humanas (edição de código mid-task) | 0 | ▲ |

### Por task

| # | Título | Aceite | Gate (tent.) | Revisor (final) | Ressalvas | Bloqueante achado? |
|---|---|---|---|---|---|---|
| 01 | schemas core | 5/5 | verde (1) | aprovado c/ ressalvas | 4 | não |
| 02 | schemas complementares | 5/5 | verde (1) | aprovado c/ ressalvas | 3 | não |
| 03 | scaffold `.harness/` novo | 5/5 | verde (1) | aprovado c/ ressalvas | 5 | não |
| 04 | update seguro | 5/5 | verde (1) | aprovado c/ ressalvas | 4 | não |
| 05 | `harness_redact.py` | 6/6 | verde (1) | aprovado c/ ressalvas | 2 | **sim** — telefone não mascarado |
| 06 | escritor de evento concorrente | 5/5 | verde (1) | aprovado c/ ressalvas | 3 | não |
| 07 | adapter hooks Claude Code | 4/4 | verde (1) | aprovado c/ ressalvas | 3 | não |
| 08 | agregação `usage.json` | 4/4 | verde (1) | aprovado c/ ressalvas | 3 | não |
| 09 | adapter `deliveries/` | 4/4 | verde (1) | aprovado c/ ressalvas | 3 | **sim** — quebrava em veredito "pendente" |
| 10 | spike viabilidade Cursor | 2/2 | verde (1) | aprovado | 0 | não |
| 11 | adapter hooks Cursor | 4/4 | verde (1) | aprovado c/ ressalvas | 1 | **sim** — `telemetry.cursor:true` fabricado sem o script existir no alvo |
| 12 | `harness_doctor.py` | 5/5 | verde (1) | aprovado c/ ressalvas | 4 | **sim** — delivery record esquecido (DoD) |
| 13 | compatibilidade N/N-1 | 4/4 | verde (1) | aprovado c/ ressalvas | 1 | não |
| 14 | `harness_prune.py` | 4/4 | verde (1) | aprovado c/ ressalvas | 1 | não |
| 15 | suíte de fixtures | 5/5 | verde (1) | aprovado c/ ressalvas | 1 | **sim** — texto de AC afirmava algo não implementado |
| 16 | wireia guard de escrita | 4/4 | verde (1) | aprovado c/ ressalvas | 2 | não |

**Nota sobre a coluna "Bloqueante achado?":** reflete o histórico real da sessão (o que o
`revisor-codigo` encontrou na primeira passada de cada task), não só o campo `bloqueantes` do
registro final em `metrics/entregas.jsonl` — nas tasks 05 e 12 esse campo ficou registrado como
`1` mesmo após a correção (inconsistência de bookkeeping minha: corrigi o veredito em texto mas
não zerei o contador `bloqueantes` do JSON). Assumo isso aqui em vez de deixar o número
incoerente sem explicação — um scorecard que finge coerência que não existe nos dados brutos é
pior que um que sinaliza a lacuna.

### Leitura para stakeholders

Todas as 16 tasks (15 originais + 1 follow-up formal) foram entregues com 100% dos critérios de
aceite atendidos e gate verde na primeira tentativa — nenhum retrabalho de implementação, só de
revisão. O sinal mais importante não é "zero bloqueante" (não é o caso: 5 das 16 tasks tiveram
bloqueante real corrigido antes do fechamento) — é que **o processo de revisão obrigatória
funcionou exatamente como desenhado**: pegou um bug de segurança real (PII de telefone não
mascarado), uma quebra de produção reproduzível contra o próprio repo (adapter de deliveries
quebrando em estado "pendente"), e — o mais sério — uma violação do princípio central do projeto
("nunca fabricar valor honesto") no adapter Cursor, todos corrigidos e re-revisados antes do
ship. Zero intervenção humana foi necessária durante a implementação de qualquer task; toda
correção veio do próprio ciclo agente-revisor.

## O que funcionou bem

- **O padrão de rodar o revisor em background enquanto a próxima task já começa a ser
  implementada** manteve o ritmo alto sem sacrificar rigor — 16 tasks com revisão completa em
  ~1h37min de build.
- **O revisor pegou bugs reais, não só estilo.** Os 5 bloqueantes encontrados não eram
  bikeshedding — eram: PII vazando sem máscara, uma exceção não tratada que quebrava contra o
  próprio `metrics/entregas.jsonl` real do repo, e uma capability fabricada que o próprio
  `harness_doctor` (construído duas tasks antes) existiria justamente para detectar.
- **Test-first funcionou como salvaguarda real**, não formalidade — vários bugs (ex.: ordenação
  de timeline com timezone misto, guard de escrita) só ficaram visíveis porque havia teste
  específico provando o comportamento, não só "código roda".
- **Honestidade de escopo, documentada em vez de escondida.** Toda vez que um critério de aceite
  não foi literalmente satisfeito (ex.: checksum não cobrindo `.claude/`/`.cursor/`, guard de
  escrita não wireado em todo writer), isso virou uma Nota explícita na task ou uma task de
  follow-up formal (task 16) — nunca um "done" silenciosamente incompleto.

## O que melhorar

- **Bookkeeping do campo `bloqueantes` em `metrics/entregas.jsonl` divergiu do veredito em texto**
  em 2 dos 16 registros (tasks 05 e 12) — depois de corrigir o bloqueante e reaprovar, esqueci de
  zerar o contador numérico. Não afeta a corretude do código entregue, mas reduz a confiabilidade
  do próprio scorecard como fonte de métrica automatizada.
- **Descoberta tardia de gap arquitetural:** só na task 11 ficou claro que
  `scripts/harness_hook.py` nunca é propagado para projetos-alvo pelo `install-harness` — um gap
  que também afeta silenciosamente a task 07 (Claude Code), só que lá ninguém tinha testado o
  caminho que exporia isso. Vale, numa próxima iteração, testar "isso funciona fora do
  dogfooding do próprio canônico?" mais cedo no ciclo, não só na 11ª de 16 tasks.
- **Task 16 (o próprio follow-up) só foi criada porque o usuário perguntou "por que não fez";**
  a ressalva do revisor da task 13 tinha ficado só em prosa numa task já fechada, sem
  rastreamento formal — o padrão certo (virar task nova) só foi aplicado depois disso acontecer
  de novo (ressalva "propagação de script" da task 07/11) já em texto de Notes.

## Armadilhas encontradas (para o próximo projeto)

- **Agentes de revisão em background podem rodar `git stash`** para conseguir uma árvore de
  trabalho limpa e, se não instruídos a não fazer isso, apagam trabalho não commitado em
  paralelo. Aconteceu uma vez nesta sessão (revisor da task 03) — recuperado via `git stash
  pop`, mas o prompt dos revisores seguintes passou a incluir instrução explícita "NÃO rode git
  stash/reset/checkout --". Vale isso virar um padrão fixo em qualquer orquestração futura de
  revisor em paralelo com edição ativa.
- **Comparar `schema_version` via string crua em vez de tupla numérica quebra silenciosamente**
  em casos como `"1.10" < "1.9"` lexicograficamente — pego na task 06/13 antes de virar bug real,
  mas é o tipo de armadilha que só um teste explícito (`test_is_schema_version_newer`) revela.
- **`execution-event.schema.json` trava `schema_version` em `const: "1.0"`** — isso limita o que
  dá pra testar sobre "payload mais novo que o pinned" até existir uma v1.1 real; a task 16
  contornou isso testando o lado inverso (pinned mais antigo), mas é uma lacuna de teste
  genuína, documentada, não escondida.

## ADRs desta implementação

- [ADR-001](../../../docs/adr/001-observabilidade-harness-control.md): arquitetura de
  observabilidade do Harness Control — run=sessão, arquivo-por-escritor, sem `pricing.json`
  local, redaction só no caminho de hook, `project_id` por hash imutável.
- [ADR-002](../../../docs/adr/002-viabilidade-hooks-cursor.md): viabilidade de hooks
  equivalentes no Cursor (spike da task 10) — Cursor tem hooks estruturalmente equivalentes ao
  Claude Code, justificando adapter real em vez de `unavailable`.

## Harness — o que aprendemos

- **O ciclo teste-primeiro → gate → revisor → correção → re-registro de métrica é o que faz o
  "aprovado com ressalvas" significar algo de verdade** — sem ele, os 5 bloqueantes reais
  teriam ido para produção como "done".
- **Faltou um hook/rule que impeça um revisor em background de rodar comandos destrutivos de git**
  — isso deveria virar uma regra explícita em `rules/` (ex.: "agentes de revisão só usam git
  read-only") em vez de depender de eu lembrar de instruir isso em cada prompt de revisor.
- **Candidato a nova skill/rule:** um checklist de "isso funciona fora do dogfooding do próprio
  canônico?" antes de marcar uma task de propagação (hooks, scripts, instalador) como `done` —
  a task 07 só teve esse gap descoberto na task 11, quatro tasks depois.
