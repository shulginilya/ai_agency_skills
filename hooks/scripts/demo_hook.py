#!/usr/bin/env python3
"""Demo hook for the ai-agency-skills plugin: a silent, side-effect-free audit log.

Claude Code runs this script on two events, wired up in ``hooks/hooks.json``:

    SessionStart              once per session, no matcher, fires every time
    PostToolUse  Write|Edit   after each successful file edit

It reads the event JSON from stdin, appends one line to a per-session JSONL log
inside the plugin's own data directory, prints nothing, and exits 0. It never
blocks a tool call and never fails a turn: every error is swallowed, so a broken
demo cannot break a session. Nothing but metadata is recorded -- no file
contents, no command strings, no environment.

Inspect what it captured:

    python3 demo_hook.py --tail        # last 20 entries of the newest log
    python3 demo_hook.py --tail 100    # ...or more
    python3 demo_hook.py --where       # print the log directory

Test it without a session, the way the troubleshooting docs suggest:

    echo '{"hook_event_name":"PostToolUse","tool_name":"Write",
           "tool_input":{"file_path":"README.md"},"session_id":"demo"}' \
        | python3 demo_hook.py; echo "exit=$?"

Environment:

    AI_AGENCY_DEMO_HOOK=off     disable it without touching any settings file
    AI_AGENCY_DEMO_HOOK_DEBUG=1 report problems on stderr instead of staying quiet
    CLAUDE_PLUGIN_DATA          set by Claude Code; where the log is written
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# A demo log is not a database. Stop appending well before it can matter.
MAX_LOG_BYTES = 256 * 1024
MAX_FIELD_CHARS = 512
OFF_VALUES = {"0", "off", "false", "no"}


def debug(msg: str) -> None:
    """Report a problem only when explicitly asked to. Hook stderr reaches Claude."""
    if os.environ.get("AI_AGENCY_DEMO_HOOK_DEBUG", "").strip().lower() not in ("", "0", "false"):
        print(f"demo_hook: {msg}", file=sys.stderr)


def log_dir() -> Path:
    """The plugin's own data directory, or a temp dir when running outside Claude Code.

    Deliberately no fall back to CLAUDE_PLUGIN_ROOT: that would drop a log inside
    the installed plugin -- or inside this checkout -- which is exactly the kind of
    scattered write a hook should never make.
    """
    base = os.environ.get("CLAUDE_PLUGIN_DATA")
    if base:
        return Path(base) / "demo-hook"
    return Path(tempfile.gettempdir()) / "ai-agency-demo-hook"


def clip(value: object) -> object:
    """Keep a single field small enough that no line can blow up the log."""
    if isinstance(value, str) and len(value) > MAX_FIELD_CHARS:
        return value[:MAX_FIELD_CHARS] + "..."
    return value


def safe_stem(session_id: object) -> str:
    """A session id is untrusted input; never let it choose a path."""
    text = str(session_id or "unknown")
    cleaned = "".join(c for c in text if c.isalnum() or c in "-_")
    return (cleaned or "unknown")[:64]


def short_path(file_path: str, cwd: str) -> str:
    """Prefer a repo-relative path; fall back to whatever came in."""
    try:
        return os.path.relpath(file_path, cwd)
    except (ValueError, TypeError):
        return file_path


def build_record(event: dict) -> dict:
    """Metadata only. Anything that could carry file or command content stays out."""
    cwd = str(event.get("cwd") or os.getcwd())
    record = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": event.get("hook_event_name") or "unknown",
        "session": safe_stem(event.get("session_id"))[:8],
        "mode": event.get("permission_mode"),
        "agent": event.get("agent_type") or "main",
    }

    tool_name = event.get("tool_name")
    if tool_name:
        record["tool"] = tool_name

    tool_input = event.get("tool_input")
    if isinstance(tool_input, dict) and tool_input.get("file_path"):
        record["path"] = short_path(str(tool_input["file_path"]), cwd)

    # SessionStart carries how the session began: startup, resume, clear, compact, fork.
    if event.get("source"):
        record["source"] = event["source"]

    return {k: clip(v) for k, v in record.items() if v is not None}


def append(record: dict, directory: Path, stem: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{stem}.jsonl"
    if path.exists() and path.stat().st_size >= MAX_LOG_BYTES:
        debug(f"{path} is at the {MAX_LOG_BYTES} byte cap; not appending")
        return
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def newest_log(directory: Path) -> Path | None:
    logs = sorted(directory.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    return logs[0] if logs else None


def tail(count: int) -> int:
    directory = log_dir()
    path = newest_log(directory) if directory.is_dir() else None
    if path is None:
        print(f"No demo-hook log yet in {directory}")
        print("Ask Claude to edit a file in a session with the plugin enabled, then look again.")
        return 0
    lines = path.read_text(encoding="utf-8").splitlines()
    print(f"{path}  ({len(lines)} entries, showing last {min(count, len(lines))})\n")
    for line in lines[-count:]:
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            print(line)
            continue
        head = f"{entry.get('ts', '?')}  {entry.get('event', '?'):<12}"
        rest = " ".join(
            f"{k}={v}" for k, v in entry.items() if k not in ("ts", "event")
        )
        print(f"{head}  {rest}")
    return 0


def run_hook() -> int:
    """The hook path proper. Always returns 0: this demo has no opinion to enforce."""
    if os.environ.get("AI_AGENCY_DEMO_HOOK", "").strip().lower() in OFF_VALUES:
        return 0

    raw = sys.stdin.read()
    if not raw.strip():
        debug("no event JSON on stdin")
        return 0

    try:
        event = json.loads(raw)
    except json.JSONDecodeError as exc:
        debug(f"stdin was not JSON: {exc}")
        return 0
    if not isinstance(event, dict):
        debug("event JSON was not an object")
        return 0

    record = build_record(event)
    append(record, log_dir(), safe_stem(event.get("session_id")))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--tail", nargs="?", type=int, const=20, metavar="N",
        help="print the last N entries (default 20) of the newest log and exit",
    )
    parser.add_argument(
        "--where", action="store_true", help="print the log directory and exit"
    )
    args = parser.parse_args()

    if args.where:
        print(log_dir())
        return 0
    if args.tail is not None:
        return tail(max(1, args.tail))

    try:
        return run_hook()
    except Exception as exc:  # noqa: BLE001 - a demo must never break a session
        debug(f"unexpected error, ignoring: {exc!r}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
