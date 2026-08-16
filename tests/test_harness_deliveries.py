from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.harness_deliveries import sync_deliveries
from scripts.harness_scaffold import apply_harness_scaffold, harness_dir

ENTREGA_1 = {
    "issue": 1,
    "titulo": "esqueleto andante",
    "data": "2026-06-27",
    "criterios_aceite": {"total": 3, "atendidos": 3},
    "gate": {"resultado": "verde", "tentativas_ate_verde": 1},
    "revisor": {"veredito": "aprovado", "bloqueantes": 0, "ressalvas": 0},
    "intervencoes_humanas": 0,
    "commit": "abc1234",
}

ENTREGA_2 = {**ENTREGA_1, "issue": 2, "titulo": "segunda task", "commit": "def5678"}


def _setup(tmp_path: Path, entregas: list[dict]) -> Path:
    apply_harness_scaffold(tmp_path, "meu-projeto")
    metrics_dir = tmp_path / "metrics"
    metrics_dir.mkdir()
    lines = "\n".join(json.dumps(e) for e in entregas) + "\n"
    (metrics_dir / "entregas.jsonl").write_text(lines, encoding="utf-8")
    return tmp_path


def test_new_line_generates_translated_delivery_record(tmp_path: Path) -> None:
    target = _setup(tmp_path, [ENTREGA_1])
    n = sync_deliveries(target)
    assert n == 1

    deliveries_path = harness_dir(target) / "deliveries" / "deliveries.jsonl"
    record = json.loads(deliveries_path.read_text().splitlines()[0])
    assert record["issue"] == 1
    assert record["titulo"] == "esqueleto andante"
    assert record["schema_version"] == "1.0"
    assert "project_id" in record


def test_adapter_never_modifies_entregas_jsonl(tmp_path: Path) -> None:
    target = _setup(tmp_path, [ENTREGA_1, ENTREGA_2])
    entregas_path = target / "metrics" / "entregas.jsonl"
    before = hashlib.sha256(entregas_path.read_bytes()).hexdigest()

    sync_deliveries(target)

    after = hashlib.sha256(entregas_path.read_bytes()).hexdigest()
    assert before == after


def test_running_twice_does_not_duplicate_entries(tmp_path: Path) -> None:
    target = _setup(tmp_path, [ENTREGA_1, ENTREGA_2])
    sync_deliveries(target)
    n_second_run = sync_deliveries(target)

    assert n_second_run == 0
    deliveries_path = harness_dir(target) / "deliveries" / "deliveries.jsonl"
    lines = deliveries_path.read_text().splitlines()
    assert len(lines) == 2


def test_only_new_lines_are_synced_on_subsequent_run(tmp_path: Path) -> None:
    target = _setup(tmp_path, [ENTREGA_1])
    sync_deliveries(target)

    entregas_path = target / "metrics" / "entregas.jsonl"
    with entregas_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(ENTREGA_2) + "\n")

    n = sync_deliveries(target)
    assert n == 1

    deliveries_path = harness_dir(target) / "deliveries" / "deliveries.jsonl"
    issues = {json.loads(line)["issue"] for line in deliveries_path.read_text().splitlines()}
    assert issues == {1, 2}
