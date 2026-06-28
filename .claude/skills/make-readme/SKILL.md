---
name: make-readme
description: >-
  Gera README.md a partir dos artefatos já existentes no repositório: CLAUDE.md,
  docker-compose.yml, docs/adr/, estrutura de pastas, pyproject.toml/package.json.
  Nunca inventa — sintetiza apenas o que está declarado. Use quando: "gera o README",
  "cria documentação pública do projeto", "o README está desatualizado", "preciso de um
  README para esse repo". Dispare com "make-readme", "cria README", "atualiza README".
---

# Make README

Gera `README.md` sintetizando o que já está declarado nos artefatos do repo.
**Regra central:** nunca inventar. Tudo que vai no README deve ter fonte rastreável.

## Fontes (lidas em ordem)

| Fonte | Extrai |
|---|---|
| `CLAUDE.md` | Stack, comandos, invariantes, layout |
| `docker-compose.yml` | Serviços, portas expostas |
| `pyproject.toml` / `package.json` | Linguagem, versão, dependências principais |
| `.env.example` | Variáveis de ambiente necessárias |
| `docs/adr/` | Decisões arquiteturais relevantes |
| `seed/schema.sql` | Modelo de dados (se existir) |
| Estrutura de pastas | Layout do projeto |

## Processo

### Passo 1 — Coletar fontes

```bash
ls -la                         # raiz do projeto
cat CLAUDE.md 2>/dev/null
cat docker-compose.yml 2>/dev/null
cat pyproject.toml 2>/dev/null || cat package.json 2>/dev/null
cat .env.example 2>/dev/null
ls docs/adr/ 2>/dev/null
```

### Passo 2 — Gerar README

Usar o template abaixo, preenchendo **apenas** o que foi encontrado nas fontes.
Seções sem fonte = omitir (não escrever "N/A" nem placeholder).

### Passo 3 — Revisão antes de salvar

Exibir o README gerado e confirmar com o usuário antes de sobrescrever o arquivo existente.

## Template

```markdown
# {nome do projeto}

> {tagline — 1 frase, extraída do CLAUDE.md ou README existente}

## O que é

{Parágrafo descrevendo o propósito. Fonte: CLAUDE.md ou README.md existente.}

## Stack

| Camada | Tecnologia |
|---|---|
{linhas extraídas do CLAUDE.md — seção Stack}

## Pré-requisitos

- Docker + Docker Compose
- {outros se declarados em CLAUDE.md ou pyproject.toml}

## Quickstart

```bash
# Subir todos os serviços
{comando extraído de CLAUDE.md — seção Comandos}

# Verificar saúde
{comando de health check se existir}
```

## Serviços

| Serviço | Porta | Descrição |
|---|---|---|
{extraído do docker-compose.yml — services e ports}

## Variáveis de ambiente

Copie `.env.example` para `.env` e preencha:

| Variável | Obrigatória | Descrição |
|---|---|---|
{extraído do .env.example}

## Estrutura do projeto

```
{tree de alto nível — extraído da estrutura de pastas, ignorando node_modules/.venv}
```

## Desenvolvimento

```bash
# Instalar dependências
{extraído de pyproject.toml / package.json}

# Rodar testes
{extraído de CLAUDE.md — seção Comandos}

# Lint / typecheck
{extraído de CLAUDE.md — seção Comandos}
```

## Decisões arquiteturais

{lista de ADRs em docs/adr/ — título e link apenas}

## Licença

{extraído de pyproject.toml / package.json / LICENSE — omitir se não encontrado}
```

## Regras

- Omitir seções sem fonte — README curto e correto > README longo com inventados
- Links para ADRs devem ser relativos (`docs/adr/001-nome.md`)
- Comandos no README devem ser os mesmos de `CLAUDE.md` — não reescrever
- Se já existe `README.md` com conteúdo, fazer merge (preservar seções únicas do original)
- Não incluir badges de CI/CD sem evidência de que o pipeline existe
