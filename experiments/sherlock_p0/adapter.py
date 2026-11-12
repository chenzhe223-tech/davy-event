"""P0 isolated Sherlock CLI adapter. No production API routes are modified."""
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

USERNAME = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")

def validate_username(username: str) -> str:
    if not isinstance(username, str) or not USERNAME.fullmatch(username):
        raise ValueError("Username must contain 1-64 letters, digits, _, . or -")
    return username

def build_command(username: str, sites: list[str] | None = None) -> list[str]:
    username = validate_username(username)
    command = [sys.executable, "-m", "sherlock_project", "--print-found", "--no-color", "--timeout", "8"]
    for site in sites or []:
        if not isinstance(site, str) or not re.fullmatch(r"[A-Za-z0-9_. -]{1,80}", site):
            raise ValueError("Invalid site name")
        command.extend(["--site", site])
    return command + [username]

def parse_found(output: str) -> list[dict]:
    """Parse Sherlock [+] lines; results remain unverified account candidates."""
    matches = []
    seen = set()
    for line in output.splitlines():
        match = re.match(r"^\[\+\]\s+(.+?):\s+(https?://\S+)", line.strip())
        if match:
            site, url = match.groups()
            if url not in seen:
                matches.append({"site": site, "url": url, "status": "candidate_unverified"})
                seen.add(url)
    return matches

def run(username: str, sites: list[str] | None = None, timeout_seconds: int = 90) -> dict:
    command = build_command(username, sites)
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout_seconds, check=False)
    except subprocess.TimeoutExpired:
        return {"username": username, "status": "timeout", "accounts": []}
    except OSError as exc:
        return {"username": username, "status": "execution_error", "error": str(exc), "accounts": []}
    return {
        "username": username,
        "status": "completed" if proc.returncode == 0 else "failed",
        "exit_code": proc.returncode,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "accounts": parse_found(proc.stdout),
        "stderr_tail": proc.stderr[-500:] if proc.returncode else "",
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    parser.add_argument("--site", action="append", default=[])
    args = parser.parse_args()
    print(json.dumps(run(args.username, args.site), ensure_ascii=False, indent=2))
