# Pirâmide de Testes

## A pirâmide

```
        /\
       /e2e\       ← poucos, lentos, caros (browser/Playwright)
      /------\
     /integr. \    ← moderados, DB real, sem mocks de I/O
    /----------\
   /  unidade   \  ← muitos, rápidos, isolados, mocks de I/O
  /--------------\
```

## Proporção recomendada

| Tipo | Proporção | Tempo típico | Quando roda |
|---|---|---|---|
| Unidade | 70% | < 1s cada | Todo commit (CI gate) |
| Integração | 25% | 1–10s | PR aberto, pré-deploy |
| E2E | 5% | 10–60s | Release candidate |

## Unidade — isola a lógica

```python
# Testa: lógica de negócio, transformações, validações, roteamento
# Mock: banco de dados, LLM, HTTP externo
# NÃO mock: a função/classe que está sendo testada

@pytest.mark.asyncio
async def test_classify_intent_returns_sql_for_aggregate_query():
    # Arrange
    service = IntentClassifier(llm=MockLLM(returns="sql_aggregate"))

    # Act
    intent = await service.classify("quanto vendemos no Q3?")

    # Assert
    assert intent == "sql_aggregate"
```

## Integração — testa a cola entre componentes

```python
# Testa: serviço + banco real, router + service real, service + Qdrant real
# Mock: LLM externo (caro), HTTP de terceiros
# NÃO mock: banco de dados, Qdrant local de teste

@pytest.mark.integration
@pytest.mark.asyncio
async def test_product_service_list_returns_only_tenant_products(db_pool):
    # Arrange — inserir dados de teste no banco real
    async with db_pool.acquire() as conn:
        await conn.execute("INSERT INTO produtos (tenant_id, nome) VALUES ($1, $2)",
                          TENANT_A, "Produto A")
        await conn.execute("INSERT INTO produtos (tenant_id, nome) VALUES ($1, $2)",
                          TENANT_B, "Produto B")

    # Act
    service = ProductService(db=db_pool)
    products = await service.list(tenant_id=TENANT_A)

    # Assert — Tenant A só vê seus produtos
    assert len(products) == 1
    assert products[0].nome == "Produto A"
```

## E2E — testa o fluxo completo

```typescript
// Playwright — testa UI + API + banco juntos
test("analista cria caso e vê no dashboard", async ({ page }) => {
  await page.goto("/login")
  await page.fill('[name="email"]', "analista@empresa.com")
  await page.click('[type="submit"]')

  await page.goto("/casos/novo")
  await page.fill('[name="titulo"]', "Suspeita de fraude")
  await page.click('[type="submit"]')

  await expect(page.getByText("Suspeita de fraude")).toBeVisible()
})
```

## Quando escrever cada tipo

| Situação | Tipo de teste |
|---|---|
| Nova função/método sem I/O | Unidade |
| Service com lógica de negócio | Unidade (mock DB) + Integração (DB real) |
| Router/endpoint | Integração (TestClient) |
| Isolamento de tenant | Integração (banco real com dados de múltiplos tenants) |
| Fluxo crítico de usuário | E2E |
| Bug corrigido | Teste de regressão (unidade ou integração, dependendo do bug) |
