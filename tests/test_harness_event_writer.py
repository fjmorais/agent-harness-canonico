from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from scripts.harness_event_writer import rebuild_timeline, write_event


def _event(
    *, sequence: int, writer_id: str, occurred_at: str = "2026-08-16T10:00:00-03:00"
) -> dict:
    return {
        "schema_version": "1.0",
        "event_id": f"evt_{writer_id}_{sequence}",
        "project_id": "project_01K2XYZ",
        "run_id": "run_01K2XYZ",
        "writer_id": writer_id,
        "source": "claude-code",
        "provider": "anthropic",
        "event_type": "tool.executed",
        "occurred_at": occurred_at,
        "sequence": sequence,
        "parent_event_id": None,
        "correlation_id": None,
        "payload": {"tool": "pytest", "exit_code": 0},
        "privacy": {"contains_prompt": False, "contains_pii": False},
    }


def test_write_event_valid_lands_in_writer_file(tmp_path: Path) -> None:
    path = write_event(tmp_path, "main", _event(sequence=1, writer_id="main"))
    assert path == tmp_path / "events" / "main.jsonl"
    assert path.exists()


def test_write_event_rejects_invalid_event(tmp_path: Path) -> None:
    invalid = _event(sequence=1, writer_id="main")
    del invalid["event_type"]
    with pytest.raises(ValueError):
        write_event(tmp_path, "main", invalid)


def test_write_event_appends_never_truncates(tmp_path: Path) -> None:
    write_event(tmp_path, "main", _event(sequence=1, writer_id="main"))
    write_event(tmp_path, "main", _event(sequence=2, writer_id="main"))

    lines = (tmp_path / "events" / "main.jsonl").read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["sequence"] == 1
    assert json.loads(lines[1])["sequence"] == 2


def test_concurrent_writers_never_lose_or_corrupt_events(tmp_path: Path) -> None:
    n_writers = 4
    m_events = 25

    def _write_all(writer_id: str) -> None:
        for i in range(m_events):
            write_event(tmp_path, writer_id, _event(sequence=i, writer_id=writer_id))

    threads = [threading.Thread(target=_write_all, args=(f"writer_{w}",)) for w in range(n_writers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    timeline = rebuild_timeline(tmp_path)
    assert len(timeline) == n_writers * m_events

    # nenhuma linha corrompida — todo evento parseou e tem os campos esperados
    seen = {(e["writer_id"], e["sequence"]) for e in timeline}
    expected = {(f"writer_{w}", i) for w in range(n_writers) for i in range(m_events)}
    assert seen == expected


def test_rebuild_timeline_merges_multiple_writers_in_order(tmp_path: Path) -> None:
    write_event(
        tmp_path,
        "main",
        _event(sequence=0, writer_id="main", occurred_at="2026-08-16T10:00:00-03:00"),
    )
    write_event(
        tmp_path,
        "sub_a",
        _event(sequence=0, writer_id="sub_a", occurred_at="2026-08-16T10:00:01-03:00"),
    )
    write_event(
        tmp_path,
        "main",
        _event(sequence=1, writer_id="main", occurred_at="2026-08-16T10:00:02-03:00"),
    )
    write_event(
        tmp_path,
        "sub_a",
        _event(sequence=1, writer_id="sub_a", occurred_at="2026-08-16T10:00:03-03:00"),
    )

    timeline = rebuild_timeline(tmp_path)
    order = [(e["writer_id"], e["sequence"]) for e in timeline]
    assert order == [("main", 0), ("sub_a", 0), ("main", 1), ("sub_a", 1)]


def test_rebuild_timeline_is_idempotent(tmp_path: Path) -> None:
    write_event(tmp_path, "main", _event(sequence=0, writer_id="main"))
    write_event(tmp_path, "sub_a", _event(sequence=0, writer_id="sub_a"))

    first = rebuild_timeline(tmp_path)
    second = rebuild_timeline(tmp_path)
    assert first == second


def test_rebuild_timeline_empty_run_returns_empty_list(tmp_path: Path) -> None:
    assert rebuild_timeline(tmp_path) == []
