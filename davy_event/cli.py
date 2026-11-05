"""Command-line interface for DAVYLAB Event Radar."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from typing import Any
from .core import deduplicate_events, export_events, normalize_event, verify_event
from .extraction import extract_events

def _read(path: str) -> str:
    return sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")

def _json(path: str) -> Any:
    return json.loads(_read(path))

def _write(value: Any) -> None:
    if isinstance(value, str):
        sys.stdout.write(value + ("" if value.endswith("\n") else "\n"))
    else:
        sys.stdout.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="davy-event", description="Process event records locally.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("extract", help="Extract events from supplied HTML or text.")
    p.add_argument("input"); p.add_argument("--source-url"); p.add_argument("--platform", default="user-provided")
    p = sub.add_parser("normalize", help="Normalize one event JSON object.")
    p.add_argument("input"); p.add_argument("--platform", default="unknown")
    p = sub.add_parser("verify", help="Check one event record.")
    p.add_argument("input")
    p = sub.add_parser("dedupe", help="Deduplicate a JSON array.")
    p.add_argument("input")
    p = sub.add_parser("export", help="Export a JSON array.")
    p.add_argument("input"); p.add_argument("--format", choices=("json", "jsonl"), default="json")
    return parser

def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "extract":
            result = extract_events(_read(args.input), source_url=args.source_url, source_platform=args.platform)
        elif args.command == "normalize":
            result = normalize_event(_json(args.input), args.platform)
        elif args.command == "verify":
            result = verify_event(_json(args.input))
        elif args.command in ("dedupe", "export"):
            records = _json(args.input)
            if not isinstance(records, list):
                raise ValueError("Input must be a JSON array of event objects.")
            result = deduplicate_events(records) if args.command == "dedupe" else export_events(records, args.format)
        else:
            raise ValueError("Unsupported command.")
        _write(result)
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"davy-event: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
