# Schema do harness-manifest.json

O `harness-manifest.json` é a memória da instalação. Fica em `.claude/harness-manifest.json`
no projeto alvo. Escrito e lido exclusivamente pelo `/install-harness`.

## Schema

```json
{
  "canonical_path": "/home/fabiano/agent-harness-canonico",
  "installed_at": "2026-06-27",
  "mode": "NOVO",
  "artefacts": {
    ".claude/agents/dev/codebase-explorer.md": {
      "source": "canonical",
      "customized": false
    },
    ".claude/skills/harness-architect/SKILL.md": {
      "source": "canonical",
      "customized": false
    },
    ".claude/kb/fastapi/index.md": {
      "source": "canonical",
      "customized": false
    },
    "CLAUDE.md": {
      "source": "generated",
      "customized": true
    },
    "AGENTS.md": {
      "source": "generated",
      "customized": true
    },
    "CONTEXT.md": {
      "source": "generated",
      "customized": false
    },
    "settings.json": {
      "source": "generated",
      "customized": false
    }
  }
}
```

## Campos

| Campo | Tipo | Descrição |
|---|---|---|
| `canonical_path` | string | Path absoluto do canônico no momento da instalação |
| `installed_at` | string (YYYY-MM-DD) | Data da última instalação/atualização |
| `mode` | enum | `NOVO`, `SEM_HARNESS` ou `ATUALIZAÇÃO` |
| `artefacts` | object | Mapa path→metadata para cada arquivo instalado |
| `artefacts[].source` | enum | `canonical` (copiado) ou `generated` (gerado projeto-específico) |
| `artefacts[].customized` | bool | `true` = não atualizar automaticamente; `false` = atualizável |

## Regras de uso

### Quando `customized: false`
O arquivo veio do canônico e não foi editado no projeto. Em futuras atualizações
(`/install-harness` em modo `ATUALIZAÇÃO`), pode ser sobrescrito se o canônico evoluiu.

### Quando `customized: true`
O arquivo foi gerado especificamente para o projeto (CLAUDE.md, AGENTS.md) ou o usuário
editou um arquivo do canônico. **Nunca sobrescrever** — listar como `[MANTÉM]` no Install Plan.

### Como marcar como customizado
O usuário pode editar o manifest manualmente:
```json
".claude/agents/dev/revisor-codigo.md": {
  "source": "canonical",
  "customized": true
}
```
Isso protege o arquivo de atualizações futuras.

### Arquivo sem entrada no manifest
Tratado como `customized: true` por segurança — o install nunca toca o que não instalou.

## Ciclo de vida

```
install (NOVO)      → cria manifest com todos os artefatos
install (ATUALIZAÇÃO) → atualiza artefacts[] + installed_at
usuário edita arquivo → atualiza manualmente customized: true
sync-context        → pode ler canonical_path para checar deriva
```
