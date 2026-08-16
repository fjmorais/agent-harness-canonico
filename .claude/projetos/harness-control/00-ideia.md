# Harness Control — evolução do canônico

## Ideia

> Fonte: `sketch/agent-harness-canonico/plan.md`. Resumo confirmado pelo usuário como fiel ao
> plano, sem ajustes.

O canônico (`/home/fabiano/agent-harness-canonico`) deverá evoluir para criar, preservar e validar
as estruturas operacionais de cada projeto instalado, de forma que um futuro produto web — o
**Harness Control** — consiga consumi-las sem depender de código do Control neste repositório. O
canônico continua sendo framework, não aplicação web; o Control é fora de escopo aqui.

Áreas cobertas pelo plano:

- Estado estruturado por projeto (`.harness/state/`).
- Runs e eventos de agentes (`.harness/runs/YYYY/MM/run_<id>/` com `run.json`, `events.jsonl`,
  `usage.json`, `result.json`, `artifacts.json`).
- Tokens e custos (`.harness/costs/pricing.json` + `ledger.jsonl`).
- Entregas, gates e reviews (`.harness/deliveries/deliveries.jsonl`).
- Auditoria e estado de instalação (`.harness/audit/audit.jsonl`).
- Schemas versionados publicados no canônico (`schemas/*.schema.json`), todos com
  `schema_version` independente da versão do harness.
- Índices reconstruíveis (`.harness/indexes/`).
- Compatibilidade entre versões (política: schema atual + uma versão anterior).

Estrutura de alto nível:

```text
/home/fabiano/agent-harness-canonico
  agents + skills + rules + KBs + schemas + instalador
                         │ ./install-harness <projeto>
                         ▼
/filesystem/workspace/<usuario>/<projeto>
  código + harness + .harness/ + documentos + logs
```

O Control poderá chamar o instalador por subprocesso e mostrar o Install Plan, mas nunca copia
artefatos diretamente — `/install-harness` continua sendo o único mecanismo de propagação
(invariante já declarado no `CLAUDE.md` do canônico).

O resultado esperado é uma instalação **observável**: os fluxos SDD, Dev Loop, agents, subagents,
skills, gates, reviews e comandos precisam ter pontos de emissão de eventos e consolidação de uso.
Não basta criar pastas vazias — o projeto instalado deve estar configurado para produzir os dados
que o Control exibirá.

### Evolução do `/install-harness`

- **Projeto novo:** criar scaffold `.harness/`, gerar `project_id` estável, criar configuração e
  estados iniciais, JSONL vazio quando necessário, instalar schemas/documentação do contrato,
  registrar capabilities/versões no manifest, configurar `.gitignore` sem apagar arquivos,
  preparar hooks/adapters de telemetria, exibir tudo no Install Plan antes de gravar.
- **Projeto existente/update:** detectar `.harness/` e versão, criar somente itens ausentes,
  preservar `project_id`/config/histórico, nunca apagar/truncar/substituir logs, listar migrations
  de schema, backup antes de migration estrutural, aplicar só após confirmação, proteger arquivos
  customizados, atualizar manifest sem perder capabilities.
- **Modo `--json`:** representa create/keep/migrate_schema com `requires_confirmation`.
- **`harness-doctor`:** diagnostica cada capability como `ok`, `missing`, `outdated`,
  `customized` ou `blocked`. Regra de honestidade: nunca preencher métrica ausente com zero ou
  estimativa silenciosa — registrar a lacuna explicitamente (`unavailable`, motivo).

### Escrita segura, retenção e Git

Lock em `.harness/locks/`, arquivo temporário no mesmo filesystem, validação contra schema,
flush/fsync, rename atômico, recuperação de temporários após crash, checksum/fingerprint,
JSONL histórico nunca reescrito, reprocessamento idempotente. Versionar `README.md`,
`config.json`, `state/project.json`; ignorar `runs/**`, `audit/**`, `indexes/**`,
`costs/ledger.jsonl`.

### Fases do plano

- **C0 — contratos:** ADR de `.harness/`, schemas v1, eventos, estados, Git e retenção.
- **C1 — instalador observável:** scaffold projeto novo, update seguro, `--json`, manifest,
  `.gitignore`, hooks, adapters, doctor de instalação.
- **C2 — telemetria:** adapters/hooks para gerar eventos e usage, sem depender de interface web.
- **C3 — compatibilidade:** fixtures, migrations, validação, exportação, rebuild, testes
  automatizados.

**Critério de saída:** um projeto novo e um existente podem ser instalados/atualizados sem perda
de dados, passam pelo doctor de observabilidade e são consumíveis pelo Control somente através dos
contratos publicados.

### Fora de escopo

Frontend/backend web do Control, login/RBAC/PostgreSQL do Control, seleção visual de pastas,
dashboards, execução pela web, administração multiusuário.

## SI Assessment

Nível: **b) Sim — dados de usuários mas não PII direto** (run_id, project_id, métricas de
execução, logs de tool calls, exit codes, custos).

Confirmado pelo usuário. Racional: o envelope de evento (`schema` do plano, seção 3.3) já traz
`privacy: {contains_prompt, contains_pii}` e o plano exige redaction de prompts/secrets/PII por
padrão nos logs detalhados — ou seja, o design assume que dado sensível pode transitar pelos
adapters (prompts de usuário, paths de projeto), mas nunca deve ser persistido sem mascaramento.

Implicações para o harness a evoluir:
- `rules/seguranca.md` já cobre "PII nunca aparece em logs" — este projeto tem que fazer isso
  valer também nos novos artefatos (`events.jsonl`, `usage.json`, `audit.jsonl`), não só nos logs
  de aplicação tradicionais.
- Qualquer schema de evento (`execution-event.schema.json`) deve tornar o campo `privacy`
  obrigatório e os adapters devem aplicar redaction antes de escrever, nunca depois.
- Não é necessário `[AVISO_LGPD]` completo nem `rules/pii.md` dedicado (isso é para nível c) — mas
  o comportamento de redaction descrito no plano (seção 5, "redaction de prompts, secrets e PII")
  deve ser tratado como invariante de design, não como nice-to-have.

## Tipo de Projeto

**e) Outro — Framework/Infraestrutura interna** (evolução do próprio agent harness canônico).

Nenhuma das opções padrão (app/API/agente, pipeline local, pipeline cloud, dashboard) descreve
bem este projeto: não há aplicação rodando nem pipeline de dados de negócio — é a evolução da
própria ferramenta de framework (agents, skills, schemas, instalador) que outros projetos
consomem via `/install-harness`.

Stack prevista: Markdown (agents/skills/rules/KB), JSON Schema (contratos), Bash (instalador e
`harness-doctor`), JSONL como formato de log append-only. Sem frontend, sem banco de dados, sem
deploy de aplicação — tudo roda como arquivos dentro do próprio repositório canônico e dos
projetos instalados.

## Próximos passos

1. Rode `/grill-me` para aprofundar a ideia (especialmente o contrato de eventos, o protocolo de
   escrita segura e o design do `harness-doctor`).
2. Ao terminar, use `harness-define` para estruturar os requisitos.
3. Depois: `harness-design` → PRD + `harness-architect` (aqui, adaptado: o "harness" gerado é a
   evolução do próprio canônico, não um `.claude/` de projeto-filho).
