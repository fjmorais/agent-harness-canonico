# Padrões pytest

## Parametrize — testar múltiplos casos de uma vez

```python
import pytest

@pytest.mark.parametrize("query,expected_intent", [
    ("quanto vendemos no Q3?",           "sql_aggregate"),
    ("top 5 produtos mais vendidos",     "sql_aggregate"),
    ("explique a política de reembolso", "doc_search"),
    ("olá, tudo bem?",                  "greeting"),
    ("como hackear o sistema",           "out_of_scope"),
    ("",                                 "out_of_scope"),  # edge case: vazio
])
@pytest.mark.asyncio
async def test_classify_intent(query, expected_intent, classifier):
    result = await classifier.classify(query)
    assert result == expected_intent
```

## Markers — categorizar e filtrar testes

```python
# pytest.ini ou pyproject.toml
# [tool.pytest.ini_options]
# markers = [
#   "integration: testes que requerem infraestrutura real",
#   "slow: testes lentos (> 5s)",
#   "llm: testes que chamam LLM real",
# ]

@pytest.mark.integration
@pytest.mark.asyncio
async def test_isolation_between_tenants(db_pool):
    ...

@pytest.mark.slow
def test_large_file_ingestion():
    ...

# Rodar apenas unit tests (CI gate rápido)
# pytest -m "not integration and not slow and not llm"

# Rodar testes de integração (CI pré-deploy)
# pytest -m "integration"
```

## asyncio — testes async

```python
# pyproject.toml
# [tool.pytest.ini_options]
# asyncio_mode = "auto"  # todos os testes async sem precisar do marker

import pytest

# Com asyncio_mode = "auto":
async def test_async_service(chat_service):
    result = await chat_service.process("query", "sess-1")
    assert result.answer

# Sem asyncio_mode = "auto":
@pytest.mark.asyncio
async def test_async_service(chat_service):
    result = await chat_service.process("query", "sess-1")
    assert result.answer
```

## Assert com mensagem clara

```python
# RUIM: assert falha sem contexto
assert result.answer

# BOM: mensagem descreve o que esperava
assert result.answer, f"Expected non-empty answer, got: {result!r}"
assert result.error is None, f"Expected no error, got: {result.error!r}"
assert len(casos) == 1, f"Expected 1 caso for tenant A, got {len(casos)}: {casos}"
```

## Teste de exceção

```python
import pytest

async def test_run_sql_raises_on_unauthorized_table(sql_tool):
    with pytest.raises(ValueError, match="Tabela não autorizada"):
        await sql_tool.run("SELECT * FROM auth.users", [], "auth.users")

async def test_service_returns_error_not_raises(chat_service, mock_graph):
    mock_graph.ainvoke.side_effect = Exception("timeout")
    result = await chat_service.process("query", "sess-1")
    # Service CAPTURA e retorna ServiceResult(error=...) — não propaga exceção
    assert result.error is not None
    assert "Falha" in result.error
```

## Coverage — garantir mínimo

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = "--cov=app --cov-fail-under=80"

[tool.coverage.report]
exclude_lines = [
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
    "pragma: no cover",
]
```

```bash
# Rodar com coverage
uv run pytest --cov=app --cov-report=term-missing -q

# Apenas testes de unidade, rápido
uv run pytest tests/unit/ -q

# Integração (requer infra)
uv run pytest tests/integration/ -q -m integration
```
