---
name: search-strategy-check
description: >-
  Checklist rápido para decidir a estratégia de busca correta para um dado/informação.
  Dado uma descrição de dado ou tipo de query, retorna: tabela de decisão + recomendação +
  sketch de código de 5 linhas. Use quando: "qual estratégia de busca?", "isso vai no vetor?",
  "RAG ou SQL para esse campo?", "checklist de retrieval", "devo indexar isso no Qdrant?".
---

# Search Strategy Check

Checklist rápido de estratégia de retrieval. Máximo 1 turno de resposta.

## Input esperado

O usuário descreve o dado e/ou a query. Exemplos:
- "campo `preco` da tabela de produtos"
- "e-mails de suporte ao cliente"
- "documentação do FastAPI"
- "transcrições de chamadas com reclamações sobre produto X"

## Processo (1 turno, sem perguntas)

Aplicar o checklist e entregar a resposta diretamente.

### Checklist de decisão

```
[ ] O dado tem resposta única e exata?
    → SIM: LEDGER (SQL/KV)
    Exemplos: preço, ID, CPF, saldo, status enum, data, contagem

[ ] O dado é texto narrativo de fonte privada?
    → SIM: RAG (Qdrant vetorial)
    Exemplos: manuais, políticas, e-mails, relatórios, contratos

[ ] O dado é documentação pública de biblioteca/framework?
    → SIM: MCP (Context-7) — não indexar no Qdrant
    Exemplos: docs do FastAPI, LangChain, Qdrant, Supabase

[ ] O dado mistura narrativa + dado exato?
    → HÍBRIDO: two-query (RAG encontra, LEDGER extrai o exato)
    Exemplos: "política de reembolso + percentual vigente"

[ ] A query usa termos técnicos, siglas ou códigos exatos?
    → HÍBRIDO: dense + BM25 + RRF
    Exemplos: catálogo com SKU, base técnica com siglas
```

## Formato de saída obrigatório

```markdown
## Estratégia recomendada: {ESTRATEGIA}

**Por quê:** {1-2 linhas de justificativa}

**NÃO fazer:** {armadilha mais comum para esse caso}

### Sketch de código
{5-10 linhas mostrando a abordagem}

### Próximo passo
{agent ou KB file relevante}
```

## Exemplos de outputs

### Input: "campo `preco` de produtos"
```markdown
## Estratégia recomendada: LEDGER (SQL)

**Por quê:** Preço tem resposta única e exata. "R$ 149,90" e "R$ 149,00" têm
distância semântica quase zero — o vetor retornaria o preço errado.

**NÃO fazer:** Indexar preço no Qdrant. Dado exato em banco vetorial = resposta imprecisa.

### Sketch de código
cursor.execute("SELECT preco FROM produtos WHERE produto_id = %s", (produto_id,))
preco = cursor.fetchone()["preco"]  # R$ 149,90 — exato

### Próximo passo
`.claude/kb/rag/patterns/ledger-lookup.md`
```

### Input: "manuais técnicos da empresa em PDF"
```markdown
## Estratégia recomendada: RAG (Qdrant vetorial)

**Por quê:** Texto narrativo privado — queries serão abertas ("explique o procedimento de...").
Busca por similaridade semântica é o canal certo.

**NÃO fazer:** Indexar campos estruturados (datas, versões, IDs) como conteúdo do chunk.

### Sketch de código
chunks = splitter.split_text(pdf_text)
for i, chunk in enumerate(chunks):
    qdrant.upsert(collection_name="manuais", points=[
        PointStruct(id=uuid4(), vector=embed(chunk),
                    payload={"source": "manual.pdf", "tenant_id": tenant,
                             "type": "manual", "content": chunk})
    ])

### Próximo passo
Agent `rag-architect` para design completo, ou `/create-rag-pipeline`
```

### Input: "documentação do LangChain"
```markdown
## Estratégia recomendada: MCP (Context-7)

**Por quê:** Documentação pública de biblioteca. MCP (Context-7) busca direto na fonte
oficial, sempre atualizado, sem custo de ingestão nem risco de documentação desatualizada.

**NÃO fazer:** Indexar docs públicos de libs no Qdrant — ficam obsoletos rapidamente.

### Sketch de código
# Usar ferramenta MCP em vez de busca vetorial:
mcp__upstash-context-7-mcp__resolve-library-id(libraryName="langchain")
mcp__upstash-context-7-mcp__get-library-docs(context7CompatibleLibraryId=..., topic="rag")

### Próximo passo
`.claude/agents/architect/kb-architect.md` para entender o Agreement Matrix MCP + KB
```
