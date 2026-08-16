# Adapter `deliveries/` — derivação de `metrics/entregas.jsonl`

**Status:** done
**Blocked by:** 03-scaffold-projeto-novo.md

## What to build

Script/hook que observa novas linhas em `metrics/entregas.jsonl` (escrito pelo `harness-build`
como já acontece hoje — sem mudar esse fluxo) e traduz cada uma para o formato
`delivery-record.schema.json` (task 02), gravando em
`.harness/deliveries/deliveries.jsonl`. `metrics/entregas.jsonl` continua sendo a fonte de
verdade para `/scorecard` — este adapter só produz uma view adicional para consumo externo (ver
ADR-001).

## Acceptance criteria

- [x] Uma nova linha em `metrics/entregas.jsonl` gera a linha correspondente em
      `.harness/deliveries/deliveries.jsonl`, validada contra `delivery-record.schema.json` —
      tested by: teste de integração adicionando uma linha fixture e verificando a saída
      traduzida.
- [x] O adapter nunca modifica `metrics/entregas.jsonl` (só lê) — tested by: teste de
      integração comparando hash do arquivo antes/depois de rodar o adapter.
- [x] Rodar o adapter duas vezes sobre o mesmo `metrics/entregas.jsonl` não duplica entradas em
      `deliveries.jsonl` (idempotente) — tested by: teste unitário chamando o adapter duas
      vezes e contando linhas.
- [x] `/scorecard` continua funcionando sem nenhuma alteração no que lê — tested by: rodar o
      `/scorecard` existente antes e depois desta mudança e comparar a saída (regressão).

## Notes

Ver ADR-001: `deliveries/deliveries.jsonl` é derivado, nunca escrito em paralelo por
`harness-build`. Não alterar `harness-build` nesta task.
