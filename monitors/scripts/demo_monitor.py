#!/usr/bin/env python3
"""Demo monitor for the ai-agency-skills plugin: surface the demo hook's log.

A monitor is a long-running command whose every stdout line reaches Claude as a
notification. This one watches the JSONL log written by ``hooks/scripts/demo_hook.py``
and prints one short line per new entry, so the two deterministic halves of this
plugin can be seen working together: the hook records a file edit, the monitor
tells Claude it happened.

It is registered in ``monitors/monitors.json`` with::

    "when": "on-skill-invoke:demo-monitor"

so it does not run in ordinary sessions. Monitors generate notifications, and a
demo that narrates every edit in every session forever is a demo nobody keeps
installed. It starts the first time ``/demo-monitor`` is dispatched, and stops
on its own after MAX_NOTIFICATIONS lines so a forgotten session cannot accrete
noise indefinitely.

Run it by hand -- a monitor is an ordinary program, which is the first thing to
try when one misbehaves::

    python3 demo_monitor.py --check      # report what it would watch, then exit
    python3 demo_monitor.py --backfill   # also replay entries already in the log
    python3 demo_monitor.py              # watch (Ctrl-C to stop)

Environment:

    AI_AGENCY_DEMO_MONITOR=off  exit immediately without watching anything
    CLAUDE_PLUGIN_DATA          set by Claude Code; where the hook's log lives
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path

POLL_SECONDS = 2.0
MAX_NOTIFICATIONS = 50
MAX_LINE_CHARS = 200
OFF_VALUES = {"0", "off", "false", "no"}


def log_dir() -> Path:
    """Where demo_hook.py writes. Kept deliberately identical to that script."""
    base = os.environ.get("CLAUDE_PLUGIN_DATA")
    if base:
        return Path(base) / "demo-hook"
    return Path(tempfile.gettempdir()) / "ai-agency-demo-hook"


def emit(text: str) -> None:
    """One notification. Flush every line: a buffered monitor looks like a dead one."""
    print(text[:MAX_LINE_CHARS], flush=True)


def describe(line: str) -> str | None:
    """Render one JSONL record as a single readable line, or None to skip it."""
    try:
        entry = json.loads(line)
    except json.JSONDecodeError:
        return None
    if not isinstance(entry, dict):
        return None
    event = entry.get("event", "?")
    parts = [f"demo-hook: {event}"]
    if entry.get("tool"):
        parts.append(str(entry["tool"]))
    if entry.get("path"):
        parts.append(str(entry["path"]))
    if event == "SessionStart" and entry.get("source"):
        parts.append(f"({entry['source']})")
    return "  ".join(parts)


def newest_log(directory: Path) -> Path | None:
    if not directory.is_dir():
        return None
    logs = sorted(directory.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    return logs[0] if logs else None


def watch(backfill: bool) -> int:
    directory = log_dir()
    emitted = 0
    current: Path | None = None
    offset = 0

    while emitted < MAX_NOTIFICATIONS:
        latest = newest_log(directory)

        # First sighting, or the hook rolled over to a new session's log.
        if latest is not None and latest != current:
            current = latest
            offset = 0 if backfill else current.stat().st_size

        if current is not None:
            try:
                size = current.stat().st_size
            except OSError:
                current, offset = None, 0
                time.sleep(POLL_SECONDS)
                continue

            # Truncated or replaced underneath us: start over rather than emit garbage.
            if size < offset:
                offset = 0

            if size > offset:
                with current.open("r", encoding="utf-8", errors="replace") as fh:
                    fh.seek(offset)
                    for line in fh:
                        if not line.endswith("\n"):  # partial write; pick it up next poll
                            break
                        offset += len(line.encode("utf-8"))
                        rendered = describe(line)
                        if rendered is None:
                            continue
                        emit(rendered)
                        emitted += 1
                        if emitted >= MAX_NOTIFICATIONS:
                            break

        time.sleep(POLL_SECONDS)

    emit(f"demo-hook: stopping after {MAX_NOTIFICATIONS} notifications")
    return 0


def check() -> int:
    directory = log_dir()
    latest = newest_log(directory)
    print(f"log directory : {directory}")
    print(f"exists        : {directory.is_dir()}")
    print(f"newest log    : {latest if latest else '(none yet)'}")
    if latest is not None:
        lines = latest.read_text(encoding="utf-8", errors="replace").splitlines()
        print(f"entries       : {len(lines)}")
        if lines:
            print(f"last rendered : {describe(lines[-1])}")
    else:
        print("Edit a file in a session with the plugin enabled, then look again.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--check", action="store_true", help="report what would be watched and exit"
    )
    parser.add_argument(
        "--backfill", action="store_true",
        help="also replay entries already in the log (default: only new ones)",
    )
    args = parser.parse_args()

    if os.environ.get("AI_AGENCY_DEMO_MONITOR", "").strip().lower() in OFF_VALUES:
        return 0
    if args.check:
        return check()

    try:
        return watch(backfill=args.backfill)
    except KeyboardInterrupt:
        return 0
    except Exception as exc:  # noqa: BLE001 - a demo must never take a session down
        print(f"demo_monitor: stopping after unexpected error: {exc!r}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
