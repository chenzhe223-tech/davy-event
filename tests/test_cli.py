import json
from davy_event.cli import main

def test_cli_extract_file(tmp_path, capsys):
    source = tmp_path / "event.txt"
    source.write_text("城市创意市集\n活动时间：2026年12月20日 10:00", encoding="utf-8")
    code = main(["extract", str(source), "--source-url", "https://example.test/event"])
    result = json.loads(capsys.readouterr().out)
    assert code == 0
    assert result[0]["start_datetime"] == "2026-12-20T10:00:00"
    assert result[0]["source_url"] == "https://example.test/event"

def test_cli_dedupe_rejects_non_array(tmp_path, capsys):
    source = tmp_path / "event.json"
    source.write_text(json.dumps({"title": "not a list"}), encoding="utf-8")
    assert main(["dedupe", str(source)]) == 2
    assert "JSON array" in capsys.readouterr().err

def test_cli_export_jsonl(tmp_path, capsys):
    source = tmp_path / "events.json"
    source.write_text(json.dumps([{"title": "A"}, {"title": "B"}]), encoding="utf-8")
    assert main(["export", str(source), "--format", "jsonl"]) == 0
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["title"] == "A"
