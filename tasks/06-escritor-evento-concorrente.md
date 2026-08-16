# Escritor de evento concorrente + reconstrução de timeline

**Status:** not started
**Blocked by:** 01-schemas-core.md

## What to build

Função pura `write_event(run_dir: Path, writer_id: str, event: dict) -> Path` que grava um
evento validado contra `execution-event.schema.json` em
`runs/YYYY/MM/run_<id>/events/<writer_id>.jsonl` (append-only, um arquivo por escritor — nunca
compartilhado entre agente principal e subagentes, eliminando condição de corrida sem lock —
ver ADR-001, Opção E). Inclui também a função de reconstrução `rebuild_timeline(run_dir) ->
list[dict]` que lê todos os arquivos `events/*.jsonl` de um run e retorna a lista de eventos
ordenada por `sequence`/`occurred_at`/`parent_event_id`, usada para popular `indexes/`.

## Acceptance criteria

- [ ] `write_event()` grava um evento válido no arquivo correto (`events/<writer_id>.jsonl`) e
      rejeita (levanta erro) um evento que falha a validação de schema — tested by: teste
      unitário com evento válido e um inválido.
- [ ] `write_event()` nunca reescreve/trunca o arquivo, só append — tested by: teste unitário
      chamando `write_event()` duas vezes e validando que ambas as linhas estão presentes.
- [ ] Múltiplos escritores (simulados via threads ou processos) gravando eventos
      simultaneamente no mesmo `run_dir` mas `writer_id` diferentes não corrompem nem perdem
      evento — tested by: teste de integração com N threads/processos concorrentes, cada um
      escrevendo M eventos, validando que todos os N*M eventos aparecem intactos no fim.
- [ ] `rebuild_timeline()` mescla eventos de múltiplos arquivos de escritor numa ordem
      consistente — tested by: teste unitário com fixture de 2+ arquivos de escritor com
      eventos intercalados, validando a ordem de saída.
- [ ] `rebuild_timeline()` é idempotente (rodar duas vezes no mesmo run_dir produz o mesmo
      resultado, sem reprocessar duplicado) — tested by: teste unitário chamando duas vezes e
      comparando a saída.

## Notes

Este é o teste que valida diretamente a decisão da Pergunta 9b do grill (concorrência de
subagentes) — worth a simulação realista com pelo menos 3-4 "escritores" concorrentes no teste
de integração, não só 2.
