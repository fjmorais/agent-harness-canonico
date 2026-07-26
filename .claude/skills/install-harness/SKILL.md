---
name: install-harness
description: >-
  Instala ou atualiza o agent harness canônico num projeto. Detecta o estado do projeto
  (zerado, existente sem harness, ou com harness incompleto), mapeia artefatos relevantes
  do canônico com base na stack detectada, mostra um Install Plan para confirmação e só
  então copia/gera os arquivos. Use quando: "instala o harness nesse projeto", "configura
  esse repo para usar o harness", "atualiza o harness desse projeto", "bootstrap do .claude/",
  "como começo a usar o agente nesse projeto". Dispare com "install-harness",
  "instala harness", "bootstrap harness", "configura harness".
tools: Read, Write, Edit, Bash
---

# Install Harness

Instala o agent harness canônico num projeto alvo — novo ou existente.
**Regra central:** mostrar o Install Plan e confirmar antes de tocar qualquer arquivo.

**Motor determinístico:** a detecção, o plano e a aplicação de arquivos rodam via
`scripts/install_harness.py` — não improvise `find`/`grep`/`cp` livres. O script também funciona
como **CLI standalone**, fora de uma sessão Claude Code — via o launcher guiado na raiz do
canônico (`install-harness` e `INSTALL-HARNESS-CLI.md` são ferramentas de instalação do próprio
canônico — **não** são propagados para o projeto de destino):

```bash
./install-harness
```

ou chamando o script direto, com flags (ver `/INSTALL-HARNESS-CLI.md`):

```bash
python3 /home/fabiano/agent-harness-canonico/.claude/skills/install-harness/scripts/install_harness.py <destino>
```

Rodado assim, ele mesmo pergunta interativamente (`input()`) por conflitos — útil para quem quer
instalar/atualizar o harness num projeto sem abrir uma conversa com o Claude. Dentro desta skill,
use o modo `--json` (Passo 1 abaixo), porque a ferramenta `Bash` do Claude não repassa um TTY
interativo ao usuário.

## Canonical path

Canônico fixo: `/home/fabiano/agent-harness-canonico`

Antes de qualquer coisa, verifique que esse path existe:
```bash
ls /home/fabiano/agent-harness-canonico/.claude/agents/ 2>/dev/null || echo "CANÔNICO NÃO ENCONTRADO"
```
Se não existir, peça o path correto ao usuário antes de prosseguir.

---

## Processo

### Passo 0 — Estabelecer pasta de destino

Antes de qualquer coisa, pergunte ao usuário onde instalar:

> "Em qual pasta devo instalar/atualizar o harness?
> (Enter para usar o diretório atual: `$(pwd)`)"

- Se o usuário confirmar o diretório atual, prossiga de onde está.
- Se informar outro path: valide que o path existe com `ls <path>`. Se não existir, pergunte se deve criar com `mkdir -p`.
- Todos os comandos do processo a seguir operam **relativos a essa pasta de destino**.

### Passo 0.5 — Coletar contexto de domínio (para CONTEXT.md)

Antes de detectar o estado do projeto, faça as 4 perguntas abaixo.
As respostas pre-populam o `CONTEXT.md` — **não invente nada**; use só o que o usuário disser.

> 1. "Qual é o domínio deste projeto?" (ex: e-commerce, detecção de fraude, quiz educacional)
> 2. "Liste os 5-10 principais termos ou entidades do domínio" (ex: pedido, produto, cliente)
> 3. "Há acrônimos ou siglas específicas do time/empresa que o agente precisa conhecer?"
> 4. "Há regras de negócio não-óbvias que parecem óbvias para o time mas que um de fora não saberia?"

Se o usuário responder "não sei ainda", "pular" ou deixar em branco: gerar `CONTEXT.md` como
esqueleto vazio (formato anterior). Se responder com conteúdo: pré-popular as seções conforme
o template de execução do Passo 4.

### Passo 1 — Rodar o motor (`--json`) e montar o Install Plan

```bash
TARGET="/path/confirmado/pelo/usuario"
CANONICAL="/home/fabiano/agent-harness-canonico"
SCRIPT="$CANONICAL/.claude/skills/install-harness/scripts/install_harness.py"

python3 "$SCRIPT" "$TARGET" --json > /tmp/install-harness-plan.json
```

A saída é `{"mode": "NOVO|SEM_HARNESS|ATUALIZAÇÃO", "stack_signals": {...}, "items": [...]}`.
Cada item tem `path`, `kind` (`copy`/`generate`/`scaffold`) e `action`:

| `action` | Significado |
|---|---|
| `COPY` / `GENERATE` / `SCAFFOLD` | Não existe no destino — será criado |
| `AUTO_UPDATE` | Existe, `customized:false` no manifest, canônico mudou — atualiza sem perguntar |
| `UP_TO_DATE` | Existe e já é igual ao canônico — nada a fazer |
| `KEEP` | Existe e está protegido (`customized:true` ou é scaffold já existente) — nunca toca |
| `SKIP_STACK` | Stack não detectada para esse artefato |
| `CONFLICT` | Existe, **não** está rastreado no manifest — precisa perguntar ao usuário |

A tabela stack→artefatos (categorias Foundation/Dev workflow/Code quality sempre + 8 blocos
condicionais por stack) vive em `scripts/stack_map.json` — é a fonte única; não a duplique aqui.
As keywords de detecção (`langgraph`, `dbt`, `airflow`, ...) também vêm só de lá — o script deriva
o vocabulário do próprio `stack_map.json`, não há lista duplicada em nenhum lugar.

Monte e apresente o Install Plan em markdown a partir do JSON, agrupando por `action` (mesmo
espírito de antes: COPIAR / GERAR / SCAFFOLD / ATUALIZAR / PULAR / NÃO TOCAR / CONFLITOS).
**Aguarde confirmação antes de prosseguir** para o Passo 1.5.

### Passo 1.5 — Oferecer forçar categoria não detectada

Se o JSON tiver algum item com `action: "SKIP_STACK"`, colete as categorias distintas puladas:

```bash
python3 -c "
import json
d = json.load(open('/tmp/install-harness-plan.json'))
print(sorted({i['category'] for i in d['items'] if i['action'] == 'SKIP_STACK'}))
"
```

Se a lista não for vazia, pergunte via `AskUserQuestion` se o usuário quer incluir alguma delas
mesmo sem a stack ter sido detectada (ex.: projeto novo que ainda não tem
`pyproject.toml`/`package.json` com a dependência, mas já sabe que vai usar). Ofereça 3 opções:
- **Nenhuma** — segue com o plano como está
- **Escolher categorias** (multiSelect com a lista coletada acima) — re-rode o Passo 1 com
  `--force-category NOME` (repetível) por categoria escolhida
- **Todas** — re-rode o Passo 1 com `--force-all` (mais simples que listar cada uma)

Depois de re-rodar, substitua o Install Plan pelo novo resultado antes de seguir.

### Passo 2 — Resolver conflitos com o usuário

Para cada item com `action: "CONFLICT"`:
- Leia o arquivo/pasta existente no destino e o equivalente no canônico (`Read` em ambos, ou
  resuma para pastas) para dar contexto real na pergunta — não pergunte às cegas.
- Pergunte via `AskUserQuestion` (agrupe até 4 conflitos por chamada) com 3 opções:
  - **keep** — não mexe no arquivo do destino
  - **overwrite** — substitui pelo conteúdo do canônico (ou pelo stub gerado, se `kind: generate`)
  - **merge** — grava o conteúdo canônico ao lado, em `<path>.harness-incoming`, e **nunca** toca
    no arquivo original (reconciliação manual do usuário depois)

Monte `{"path": "resolution", ...}` com as respostas e grave em `/tmp/install-harness-decisions.json`.

### Passo 3 — Aplicar (somente após confirmação)

```bash
python3 "$SCRIPT" "$TARGET" --json --decisions-file /tmp/install-harness-decisions.json
```

Isso copia/gera/scaffolda, espelha `.claude/` → `.cursor/` (rules convertidas para `.mdc`), grava
os `.harness-incoming` pendentes e atualiza `.claude/harness-manifest.json` — tudo dentro do
script (ver `references/install-manifest-schema.md` para o schema do manifest). **Nunca** escreva
esses arquivos via `Write`/`Edit` direto; é o script quem garante o invariante de não sobrescrever
sem decisão.

Se o usuário respondeu as perguntas de domínio do Passo 0.5, depois de aplicar sobrescreva
`CONTEXT.md` (via `Write`, já que é um arquivo `customized: true` que só você, dentro desta
conversa, deve tocar) com o conteúdo pré-populado abaixo. Se o script já criou um `.harness-incoming`
para `CONTEXT.md` (conflito resolvido como `merge`), popule esse arquivo em vez do original.

```markdown
# Glossário de domínio — [nome do projeto]

> Iniciado pelo /install-harness. Refinar com /grill-with-docs junto ao especialista de domínio.
> Cada termo deve ter: definição precisa + sinônimos usados pelo time + o que NÃO é.

---

## Domínio
[resposta da pergunta 1 — ex: "Quiz educacional para formação em IA"]

## Termos do domínio

| Termo | Definição | Sinônimos | O que NÃO é |
|---|---|---|---|
| [termo 1] | (preencher com /grill-with-docs) | — | — |

(um stub por termo listado na resposta da pergunta 2)

## Acrônimos e siglas

| Sigla | Significado |
|---|---|
(respostas da pergunta 3, ou "(nenhum informado)")

## Regras de negócio implícitas

(respostas da pergunta 4, ou "(preencher com /grill-with-docs)")
```

Feche listando os próximos passos obrigatórios (o script já imprime isso no modo interativo; no
modo `--json` reproduza a mesma lista):
1. `/grill-with-docs` — preencher CONTEXT.md com terminologia real do domínio
2. `/grill-me` — refinar CLAUDE.md com invariantes específicos do projeto
3. Revisar hooks em `.claude/settings.json` (comandos corretos para a stack)
4. `/validar` — confirmar gate verde antes da primeira sessão de build

---

## Regras de qualidade

- **Nunca sobrescreve** arquivo com `"customized": true` no manifest
- **Nunca inventa** stack ou nome de projeto — usa só o que detectou nos arquivos
- **Nunca executa sem aprovação** do Install Plan
- **Começa mínimo** — Foundation + workflow sempre; stack-specific só se detectado
- **CONTEXT.md vem vazio** — nunca preenche com terminologia inventada; isso é papel do `/grill-with-docs`
- **Manifest é sagrado** — qualquer arquivo sem entrada no manifest é tratado como `customized: true` em futuras atualizações
- **Escrita só via o script** — detecção, plano, cópia/geração e gravação do manifest passam por
  `scripts/install_harness.py`; a skill não improvisa `cp`/`Write` para os artefatos que o script
  já cobre (exceção: `CONTEXT.md` pré-populado no Passo 3, que é conteúdo só desta conversa)

## Referências

- `scripts/install_harness.py` — motor determinístico (detect/plan/apply); também roda como CLI
  standalone fora do Claude Code (`python3 install_harness.py <destino>`, sem `--json`)
- `scripts/stack_map.json` — fonte única da tabela stack → artefatos usada pelo script
- `/INSTALL-HARNESS-CLI.md` (raiz do canônico) — guia passo a passo para rodar a CLI standalone no
  terminal. **Não** é propagado para o projeto de destino — é documentação sobre como instalar o
  harness a partir daqui, não conteúdo do harness em si
- `/install-harness` (raiz do canônico) — launcher guiado (`./install-harness`). Mesma lógica: fica
  só no canônico, não é copiado para o destino
- `references/install-manifest-schema.md` — schema completo do harness-manifest.json
- `.claude/skills/harness-architect/references/stack-layer-map.md` — mapa stack → artefatos
  (tabela irmã, usada no fluxo de entrevista do `harness-architect`, não pelo install)
- `.claude/skills/harness-architect/references/claude-dir-templates.md` — templates de referência
  para os stubs gerados pelo script (`generate_content()`)
- `.claude/skills/grill-with-docs/SKILL.md` — preenchimento do CONTEXT.md após install
