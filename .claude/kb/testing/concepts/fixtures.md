# pytest Fixtures

## Scopes — vida útil da fixture

| Scope | Cria uma vez por | Usar para |
|---|---|---|
| `function` (padrão) | Cada teste | Objetos mutáveis, DB com transação rollback |
| `class` | Classe de testes | Setup compartilhado por classe |
| `module` | Arquivo de teste | Conexões caras reutilizáveis |
| `session` | Toda a execução | Pool de DB, servidor de teste |

```python
# conftest.py — fixtures compartilhadas entre arquivos
import pytest
import asyncpg
from fastapi.testclient import TestClient
from app.main import app

# Session scope — pool criado uma vez por execução de testes
@pytest.fixture(scope="session")
async def db_pool():
    pool = await asyncpg.create_pool(dsn=TEST_DATABASE_URL, min_size=1, max_size=3)
    yield pool
    await pool.close()

# Function scope — transação por teste (rollback automático = isolamento)
@pytest.fixture
async def db_conn(db_pool):
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            yield conn
            raise Exception("rollback")  # força rollback ao sair
            # alternativa: conn.transaction().rollback()

# Client do FastAPI
@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
```

## Factory fixture — dados configuráveis

```python
# Fixture factory: retorna uma função que cria dados parametrizados
@pytest.fixture
def make_caso(db_conn):
    async def _make(
        tenant_id: str = TENANT_A,
        titulo: str = "Caso de teste",
        status: str = "aberto",
        risco: str = "medio",
    ) -> dict:
        row = await db_conn.fetchrow("""
            INSERT INTO casos (tenant_id, titulo, status, risco)
            VALUES ($1, $2, $3, $4)
            RETURNING *
        """, tenant_id, titulo, status, risco)
        return dict(row)
    return _make

# Uso no teste
@pytest.mark.asyncio
async def test_service_lista_apenas_casos_do_tenant(make_caso, db_pool):
    await make_caso(tenant_id=TENANT_A, titulo="Caso A")
    await make_caso(tenant_id=TENANT_B, titulo="Caso B")

    service = CasoService(db=db_pool)
    casos = await service.list(tenant_id=TENANT_A)

    assert len(casos) == 1
    assert casos[0]["titulo"] == "Caso A"
```

## Fixtures de mock

```python
from unittest.mock import AsyncMock, MagicMock
import pytest

@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    llm.ainvoke.return_value.content = "resposta mockada"
    llm.ainvoke.return_value.usage.prompt_tokens = 100
    llm.ainvoke.return_value.usage.completion_tokens = 50
    return llm

@pytest.fixture
def mock_qdrant():
    client = MagicMock()
    client.search.return_value = [
        MagicMock(payload={"content": "chunk relevante", "source": "doc:1"}, score=0.9)
    ]
    return client

@pytest.fixture
def chat_service(mock_llm, mock_qdrant, db_conn):
    graph = AgentGraph(llm=mock_llm, qdrant=mock_qdrant, db=db_conn)
    return ChatService(graph=graph)
```

## conftest.py hierarquia

```
tests/
├── conftest.py              ← fixtures globais (db_pool, client, constantes)
├── unit/
│   ├── conftest.py          ← fixtures específicas de unidade (mocks)
│   └── test_chat_service.py
└── integration/
    ├── conftest.py          ← fixtures de integração (db real, seeds)
    └── test_product_service.py
```

```python
# tests/conftest.py
TENANT_A = "10000000-0000-0000-0000-000000000001"
TENANT_B = "20000000-0000-0000-0000-000000000002"
TEST_DATABASE_URL = "postgresql://test:test@localhost:5433/testdb"

# tests/unit/conftest.py — herda do pai
# tests/integration/conftest.py — herda do pai
```
