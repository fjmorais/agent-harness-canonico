---
domain: testing
description: Padrões de teste — pytest, vitest, fixtures, integração vs unidade, mocking cirúrgico
mcp_validated: "2026-06-27"
confidence: 0.92
---

# KB: Testing

Padrões de teste para projetos Python (pytest) e TypeScript/React (vitest).
Princípio central: **teste comportamento, não implementação** — mock apenas I/O externo, nunca lógica interna.

## Conceitos

| Arquivo | Tópico |
|---|---|
| [pyramid.md](concepts/pyramid.md) | Pirâmide de testes — unidade vs integração vs e2e, proporção certa |
| [fixtures.md](concepts/fixtures.md) | pytest fixtures — scope, factory pattern, conftest.py |

## Padrões

| Arquivo | Tópico |
|---|---|
| [pytest-patterns.md](patterns/pytest-patterns.md) | Padrões pytest — parametrize, asyncio, markers, coverage |
| [vitest-patterns.md](patterns/vitest-patterns.md) | Padrões vitest — Testing Library, mocking, setup |

## Quick Reference

Ver [quick-reference.md](quick-reference.md) — nomenclatura de testes, regra de mocking,
invariantes (TE-01…TE-05). Ler só se a tarefa exigir esse nível de detalhe.
