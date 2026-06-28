---
domain: langgraph
description: Grafos determinísticos com LangGraph — state, nós, tools, human-in-the-loop, multi-agent
mcp_validated: "2026-06-27"
confidence: 0.92
---

# KB: LangGraph

Base de conhecimento para construção de agentes com grafos **determinísticos** usando LangGraph.
O princípio central: o grafo decide o fluxo; o LLM decide apenas dentro dos nós — nunca o fluxo.

## Conceitos

| Arquivo | Tópico |
|---|---|
| [graph-anatomy.md](concepts/graph-anatomy.md) | StateGraph, nós, edges, entry point, compilação |
| [state-management.md](concepts/state-management.md) | TypedDict de state, reducers, schema de mensagens |
| [tool-design.md](concepts/tool-design.md) | Tools parametrizadas por coleção/tabela, contrato de retorno |
| [human-in-the-loop.md](concepts/human-in-the-loop.md) | interrupt(), checkpointers, aprovação humana |

## Padrões

| Arquivo | Tópico |
|---|---|
| [deterministic-routing.md](patterns/deterministic-routing.md) | Roteamento por intent classificado — sem loop livre do LLM |
| [run-sql-tool.md](patterns/run-sql-tool.md) | Tool somente-leitura com allowlist + LIMIT + timeout |
| [search-tool.md](patterns/search-tool.md) | Tool de busca vetorial com pre-filter de metadados |
| [interrupt-pattern.md](patterns/interrupt-pattern.md) | Pausa, coleta aprovação, retoma — com MemorySaver |

## Quick Reference

### Anatomia de um grafo mínimo

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class AgentState(TypedDict):
    query: str
    intent: str
    result: str
    sources: list[str]

graph = StateGraph(AgentState)
graph.add_node("classify", classify_node)
graph.add_node("search", search_node)
graph.add_node("generate", generate_node)

graph.set_entry_point("classify")
graph.add_conditional_edges("classify", route_by_intent, {
    "sql": "run_sql",
    "search": "search",
})
graph.add_edge("search", "generate")
graph.add_edge("generate", END)

app = graph.compile()
```

### Decision tree: grafo determinístico vs ReAct

```
O LLM precisa escolher qual ferramenta usar em loop?
    ├── SIM → ReAct (mas documente o risco: não-determinismo, custo)
    └── NÃO → Grafo determinístico (preferido)
           ├── O fluxo tem desvios baseados em dados?
           │   └── SIM → conditional_edges com função de roteamento
           └── O fluxo é linear?
               └── SIM → add_edge direto
```

### Invariantes (nunca quebrar)

| # | Invariante |
|---|---|
| LG-01 | LLM **não** escolhe tool em loop livre — nó faz a escolha com lógica determinística |
| LG-02 | State schema sempre `TypedDict` tipado — sem dicts genéricos |
| LG-03 | Tools parametrizadas por nó — mesma tool, coleção/tabela diferente por intent |
| LG-04 | Grounding obrigatório em nós geradores — `sources` no state |
| LG-05 | Human-in-the-loop via `interrupt()` — nunca via prompt "espere confirmação" |
