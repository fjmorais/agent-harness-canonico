---
domain: testing
topic: quick-reference
---

# Testing — Quick Reference

### Nomenclatura de testes

```python
# Python: test_{quando}_{espera}
def test_process_query_returns_answer(): ...
def test_process_query_with_empty_input_raises_error(): ...
def test_run_sql_with_unauthorized_table_returns_error(): ...

# TypeScript: describe(componente) → it(comportamento)
describe("CasoCard", () => {
  it("renderiza título do caso")
  it("chama onSelect ao clicar no botão")
  it("exibe badge vermelho para risco alto")
})
```

### Regra de mocking

```
O que MOCKAR: DB (unit), LLM externo, HTTP externo, clock (time.now())
O que NÃO MOCKAR: lógica de negócio pura, transformações, validações
```

### Invariantes

| # | Invariante |
|---|---|
| TE-01 | Cada teste tem **1 asserção principal** — múltiplas só se inseparáveis |
| TE-02 | Mocks apenas em I/O externo — nunca mockar a própria lógica testada |
| TE-03 | Fixtures em `conftest.py` — não duplicar setup entre arquivos |
| TE-04 | Testes de integração com DB real em `/tests/integration/` separados |
| TE-05 | CI roda `pytest -q` (unit) + `pytest tests/integration/` (integration) em etapas separadas |
