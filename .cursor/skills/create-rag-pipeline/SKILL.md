---
name: create-rag-pipeline
description: >-
  Gera pipeline RAG completo (ingestão + query) com estrutura SOLID e código Python pronto para uso.
  Cria RAGConfig, Ingestor (chunk→embed→index), Querier (embed→filter→search→rerank→generate),
  com metadata schema obrigatório e grounding. Use quando: "criar RAG", "pipeline de busca semântica",
  "indexar documentos", "chatbot com base de conhecimento", "RAG para docs privados".
---

# Create RAG Pipeline

Gera pipeline RAG completo com estrutura SOLID, configurável por ambiente, pronto para produção.

## Quick start

```
/create-rag-pipeline
```

O agente faz 4 perguntas e gera o código.

## Processo

### Passo 1 — Coletar requisitos (4 perguntas)

1. **Nome da coleção Qdrant** (ex: `docs_privados`, `catalogo_produtos`, `politicas`)
2. **Tipo de documento** (manuais, FAQs, e-mails, artigos, contratos, misto)
3. **Multi-tenant?** (sim/não — se sim, campo `tenant_id` obrigatório no pre-filter)
4. **Busca híbrida?** (dense + BM25 para termos técnicos/siglas)

### Passo 2 — Gerar estrutura de arquivos

```
rag/
├── config.py              ← RAGConfig dataclass (from_env())
├── ingest/
│   └── pipeline.py        ← RAGIngestor (chunker + embedder + indexer)
├── query/
│   ├── pipeline.py        ← RAGQuerier (embed → filter → search → rerank)
│   └── reranker.py        ← cohere_rerank() se solicitado
└── __init__.py
```

### Passo 3 — Gerar cada arquivo

**config.py** (sempre)
```python
from dataclasses import dataclass, field
import os

@dataclass
class RAGConfig:
    qdrant_url: str = field(default_factory=lambda: os.getenv("QDRANT_URL", "http://localhost:6333"))
    collection_name: str = "{COLLECTION_NAME}"
    embedding_model: str = "text-embedding-3-large"
    embedding_dim: int = 3072
    chunk_size: int = 512
    chunk_overlap: int = 64
    top_k_retrieve: int = 20
    top_k_final: int = 3
    use_reranking: bool = {USE_RERANKING}
    use_hybrid: bool = {USE_HYBRID}
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    cohere_api_key: str = field(default_factory=lambda: os.getenv("COHERE_API_KEY", ""))

    @classmethod
    def from_env(cls) -> "RAGConfig":
        return cls()
```

**Metadata schema obrigatório** (sempre incluir no comentário do Ingestor):
```python
# Campos obrigatórios em todo chunk indexado:
# source: str       — origem do documento
# section: str      — seção/capítulo (vazio se não houver)
# date: str         — data do documento ("YYYY-MM-DD")
# type: str         — tipo ("manual" | "politica" | "faq" | "email")
# tenant_id: str    — isolamento multi-tenant (obrigatório se multi-tenant)
# content: str      — texto original do chunk (para grounding)
# chunk_index: int  — posição no documento original
```

### Passo 4 — Verificar invariantes

Antes de finalizar, checar:
- [ ] Chunk size ≤ 512 tokens
- [ ] Pre-filter por tenant_id se multi-tenant
- [ ] Metadata schema inclui `source` e `content` para grounding
- [ ] Mesmo modelo de embedding na ingestão e na query
- [ ] Payload indexes criados para campos de filtro

### Passo 5 — Gerar .env.example com variáveis necessárias

```
QDRANT_URL=http://localhost:6333
OPENAI_API_KEY=sk-...
COHERE_API_KEY=...  # se reranking habilitado
```

## Checklist de qualidade

- [ ] RAGConfig usa `from_env()` — zero hardcode
- [ ] Ingestor cria collection + payload indexes se não existirem
- [ ] Querier tem pre-filter de tenant antes do semântico
- [ ] Grounding: `content` no payload + sources retornados ao LLM
- [ ] Reranker só chamado se `use_reranking=True` e candidatos > top_k_final
- [ ] Busca híbrida: sparse vectors indexados se `use_hybrid=True`

## Referências

- `.claude/kb/rag/patterns/rag-pipeline.md` — pipeline completo com código
- `.claude/kb/rag/concepts/chunking-strategies.md` — estratégias de chunking
- `.claude/kb/rag/concepts/embedding-selection.md` — modelos disponíveis
- `.claude/kb/rag/concepts/reranking.md` — configuração do reranker
- `.claude/kb/rag/patterns/metadata-filtering.md` — pre-filter avançado
- `.claude/kb/rag/patterns/rag-with-keywords.md` — implementação híbrida
