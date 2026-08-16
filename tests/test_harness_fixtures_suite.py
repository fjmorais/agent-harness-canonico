"""Suíte de fixtures completa (task 15) — cenários de compatibilidade da seção 7 do plano
original, usando fixtures estáticas versionadas em tests/fixtures/harness/."""

from __future__ import annotations

from pathlib import Path

from scripts.harness_doctor import detect_orphaned_temp_files, diagnose
from scripts.harness_event_writer import rebuild_timeline
from scripts.harness_scaffold import fingerprint_file, harness_dir

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "harness"


def test_legacy_project_is_reported_outdated() -> None:
    project = FIXTURES / "v1-legacy"
    report = diagnose(project)
    assert report["schema_compatibility"]["status"] == "outdated"
    assert report["schema_compatibility"]["installed_version"] == "0.1"


def test_out_of_order_events_are_reordered_consistently() -> None:
    project = FIXTURES / "v1-out-of-order-events"
    run_dir = harness_dir(project) / "runs" / "2026" / "08" / "run_ooo1"

    timeline = rebuild_timeline(run_dir)

    assert len(timeline) == 5
    occurred_at_values = [e["occurred_at"] for e in timeline]
    assert occurred_at_values == sorted(occurred_at_values)  # cronologicamente correto
    # sequence por escritor preservada dentro da ordem correta
    main_sequences = [e["sequence"] for e in timeline if e["writer_id"] == "main"]
    assert main_sequences == sorted(main_sequences)


def test_orphaned_temp_file_from_crash_is_detected_and_reported() -> None:
    project = FIXTURES / "v1-crash-recovery"

    orphans = detect_orphaned_temp_files(project)
    assert len(orphans) == 1
    assert orphans[0].name == "project.json.tmp"

    report = diagnose(project)
    assert any(p.endswith("project.json.tmp") for p in report["orphaned_temp_files"])


def test_claude_cursor_mirror_files_have_consistent_checksum() -> None:
    project = FIXTURES / "v1-claude-cursor-mirror"
    claude_file = project / ".claude" / "rules" / "seguranca.md"
    cursor_file = project / ".cursor" / "rules" / "seguranca.mdc"

    assert claude_file.exists()
    assert cursor_file.exists()
    # o corpo da regra (após o front-matter do .mdc) é idêntico ao .md original — o
    # checksum de todo o .harness/ em si (task 12) não cobre .claude/.cursor/ ainda (gap
    # documentado nas Notes da task 12); esta suíte prova a consistência de conteúdo
    # diretamente, sem depender dessa extensão de escopo futura.
    claude_body = claude_file.read_text()
    cursor_body = cursor_file.read_text().split("---\n\n\n", 1)[1]
    assert claude_body == cursor_body
    assert fingerprint_file(claude_file) != fingerprint_file(cursor_file)  # front-matter difere
