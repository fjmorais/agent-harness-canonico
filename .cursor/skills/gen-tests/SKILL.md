---
name: gen-tests
description: >-
  Gera testes automatizados (pytest ou vitest) para um módulo, função ou componente.
  Cria fixtures reutilizáveis, casos felizes, casos de borda e mocks cirúrgicos.
  Nunca mocka o que pode ser testado real. Use quando: "escreve testes para isso",
  "adiciona cobertura nesse módulo", "preciso de testes para esse serviço", "gera
  pytest para essa função", "testa esse componente React", "/gen-tests".
---

# Gen Tests

Gera testes automatizados com estrutura padronizada e fixtures reutilizáveis.

## Quick start

```
/gen-tests
```

## Processo

### Passo 1 — Identificar contexto

1. Ler o módulo/componente alvo
2. Identificar o framework: `pytest` (Python) ou `vitest` (TypeScript/React)
3. Listar as funções/métodos públicos a testar
4. Identificar dependências externas (DB, LLM, API) que precisam de mock

### Passo 2 — Decisão: mock vs real

| Dependência | Mockar? | Razão |
|---|---|---|
| Função pura (sem I/O) | ❌ Nunca | Testar direto |
| DB (em teste de unidade) | ✅ Sim | Isolar unidade |
| DB (em teste de integração) | ❌ Real | Detectar divergências |
| LLM externo | ✅ Sim | Caro, lento, não-determinístico |
| HTTP externo (Stripe, etc.) | ✅ Sim | Não disponível em CI |
| Qdrant (unidade) | ✅ Sim | Isolamento |

### Passo 3 — Gerar os testes

#### Python — pytest

```python
# tests/services/test_chat_service.py
import pytest
from unittest.mock import AsyncMock, patch
from app.services.chat_service import ChatService
from app.schemas.chat import ServiceResult

# --- FIXTURES ---

@pytest.fixture
def mock_graph():
    graph = AsyncMock()
    graph.ainvoke.return_value = {
        "answer": "Produto X foi o mais vendido",
        "sources": ["sql:negocio.pedidos"],
        "intent": "sql_aggregate",
        "error": None,
    }
    return graph

@pytest.fixture
def mock_recorder():
    return AsyncMock()

@pytest.fixture
def chat_service(mock_graph, mock_recorder):
    return ChatService(graph=mock_graph, recorder=mock_recorder)

# --- CASOS FELIZES ---

@pytest.mark.asyncio
async def test_process_returns_answer(chat_service, mock_graph):
    result = await chat_service.process("qual o mais vendido?", "sess-1")

    assert result.answer == "Produto X foi o mais vendido"
    assert result.error is None
    assert "sql:negocio.pedidos" in result.sources
    mock_graph.ainvoke.assert_called_once()

# --- CASOS DE BORDA ---

@pytest.mark.asyncio
async def test_process_returns_error_on_graph_failure(chat_service, mock_graph):
    mock_graph.ainvoke.side_effect = Exception("LLM timeout")

    result = await chat_service.process("...", "sess-1")

    assert result.error is not None
    assert result.answer == ""

@pytest.mark.asyncio
async def test_process_handles_domain_error(chat_service, mock_graph):
    mock_graph.ainvoke.return_value = {"answer": "", "sources": [], "error": "Tabela não autorizada"}

    result = await chat_service.process("...", "sess-1")

    assert result.error == "Tabela não autorizada"

@pytest.mark.asyncio
async def test_process_empty_query_returns_error(chat_service):
    result = await chat_service.process("", "sess-1")
    # depende da validação implementada — ajustar conforme o código
    assert result is not None
```

#### TypeScript — vitest + Testing Library

```typescript
// src/components/__tests__/CasoCard.test.tsx
import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { CasoCard } from "../CasoCard"
import type { Caso } from "../../types"

const mockCaso: Caso = {
  id: "caso-1",
  titulo: "Fraude em sinistro",
  status: "em_analise",
  risco: "alto",
  created_at: "2026-06-27T10:00:00Z",
}

describe("CasoCard", () => {
  // --- CASOS FELIZES ---
  it("renderiza título e status", () => {
    render(<CasoCard caso={mockCaso} />)
    expect(screen.getByText("Fraude em sinistro")).toBeInTheDocument()
    expect(screen.getByText("em_analise")).toBeInTheDocument()
  })

  it("chama onSelect ao clicar", async () => {
    const onSelect = vi.fn()
    render(<CasoCard caso={mockCaso} onSelect={onSelect} />)

    fireEvent.click(screen.getByRole("button", { name: /selecionar/i }))
    expect(onSelect).toHaveBeenCalledWith("caso-1")
  })

  // --- CASOS DE BORDA ---
  it("exibe badge vermelho para risco alto", () => {
    render(<CasoCard caso={mockCaso} />)
    const badge = screen.getByTestId("risco-badge")
    expect(badge).toHaveClass("bg-red-500")
  })

  it("não renderiza botão de seleção sem onSelect prop", () => {
    render(<CasoCard caso={mockCaso} />)
    expect(screen.queryByRole("button", { name: /selecionar/i })).not.toBeInTheDocument()
  })
})
```

### Passo 4 — Verificar cobertura

```bash
# Python
uv run pytest --cov=app --cov-report=term-missing tests/

# TypeScript
npx vitest run --coverage
```

### Passo 5 — conftest.py (Python) para fixtures compartilhadas

```python
# tests/conftest.py
import pytest
import asyncpg
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="session")
async def db_pool():
    """Pool real para testes de integração."""
    pool = await asyncpg.create_pool(dsn=TEST_DATABASE_URL, min_size=1, max_size=3)
    yield pool
    await pool.close()

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
```

## Checklist de qualidade de testes

- [ ] Cada teste testa UMA coisa — sem múltiplos asserts não relacionados
- [ ] Nome do teste descreve o comportamento: `test_{quando}_{espera}`
- [ ] Fixtures no `conftest.py` para reuso entre arquivos
- [ ] Mocks apenas para I/O externo — não mockar o que pode ser testado real
- [ ] Testes de borda: input vazio, None, valor fora do range, erro de dependência
- [ ] Integração com DB real em `tests/integration/` separada dos testes de unidade

## Referências

- `.claude/kb/testing/` — padrões de teste por tipo
- `.claude/rules/testes.md` — invariantes de teste do projeto
