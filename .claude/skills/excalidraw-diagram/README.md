# excalidraw-diagram

Skill que dá ao agente a capacidade de gerar arquivos `.excalidraw` bonitos e práticos a partir de descrições em linguagem natural. Não são apenas caixas e setas — são diagramas que **argumentam visualmente**.

Fonte original: [coleam00/excalidraw-diagram-skill](https://github.com/coleam00/excalidraw-diagram-skill)

---

## O que torna esta skill diferente

- **Diagramas que argumentam, não apenas exibem.** Cada forma/grupo espelha o conceito que representa — fan-outs para um-para-muitos, timelines para sequências, convergência para agregação.
- **Artefatos de evidência.** Diagramas técnicos incluem snippets de código reais e payloads JSON concretos.
- **Validação visual embutida.** Pipeline de renderização via Playwright — o agente vê o próprio output, corrige overlaps, arrows desalinhadas e espaçamento antes de entregar.
- **Paleta customizável.** Todas as cores vivem em `references/color-palette.md`. Edite ali para aplicar seu brand.

---

## Estrutura

```
excalidraw-diagram/
├── SKILL.md                      # Instruções completas de design + workflow
├── README.md                     # Este arquivo
└── references/
    ├── color-palette.md          # Paleta de cores (edite para customizar)
    ├── element-templates.md      # Templates JSON por tipo de elemento
    ├── json-schema.md            # Referência do formato JSON do Excalidraw
    ├── render_excalidraw.py      # Script de renderização .excalidraw → PNG
    ├── render_template.html      # Template HTML para o renderer
    └── pyproject.toml            # Dependências Python (playwright)
```

---

## Configuração (primeira vez)

```bash
cd .claude/skills/excalidraw-diagram/references
uv sync
uv run playwright install chromium
```

Ou peça ao agente: *"Configure a skill excalidraw-diagram seguindo as instruções do README."*

---

## Como usar

Invoque a skill pedindo um diagrama ao agente:

```
/excalidraw-diagram
```

Ou simplesmente descreva o que quer visualizar:

> "Crie um diagrama Excalidraw mostrando o fluxo do pipeline de ingestão de dados"

O agente vai:
1. Avaliar se o diagrama é simples/conceitual ou técnico/abrangente
2. Para diagramas técnicos: pesquisar specs reais antes de desenhar
3. Mapear cada conceito para o padrão visual correto (fan-out, timeline, convergência, etc.)
4. Gerar o JSON seção por seção (nunca em um único passe)
5. Renderizar para PNG e revisar visualmente em loop até estar correto
6. Entregar o arquivo `.excalidraw` pronto para abrir no [excalidraw.com](https://excalidraw.com) ou no plugin VS Code

---

## Customizar cores

Edite `references/color-palette.md` para aplicar seu brand. O restante da skill é metodologia universal de design — não precisa tocar.

---

## Renderizar manualmente

```bash
cd .claude/skills/excalidraw-diagram/references
uv run python render_excalidraw.py caminho/para/arquivo.excalidraw

# Opções:
# --output path.png   → caminho de saída (padrão: mesmo nome com .png)
# --scale 2           → fator de escala do device (padrão: 2)
# --width 1920        → largura máxima do viewport (padrão: 1920)
```

---

## Padrões visuais suportados

| Padrão | Quando usar |
|--------|-------------|
| Fan-out | Um-para-muitos: hubs, fontes, causas raiz |
| Convergência | Muitos-para-um: agregação, funis |
| Árvore | Hierarquia: file systems, org charts |
| Timeline | Sequência de passos com marcadores |
| Ciclo/Espiral | Loops, processos iterativos |
| Nuvem | Estado abstrato, contexto, memória |
| Assembly Line | Transformação input → processo → output |
| Side-by-Side | Comparação, before/after, trade-offs |

---

## Filosofia central

**O Teste do Isomorfismo**: Se você remover todo o texto, a estrutura sozinha comunica o conceito? Se não, redesenhe.

**O Teste Educacional**: Alguém consegue aprender algo concreto com este diagrama, ou ele apenas rotula caixas?
