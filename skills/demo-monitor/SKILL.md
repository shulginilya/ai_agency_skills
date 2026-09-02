---
name: demo-monitor
description: Start and explain this repo's demo monitor, which reports new entries from the demo hook's audit log as notifications. Use when someone asks what a monitor is, how monitors differ from hooks, how to watch a log or a background process from a session, or asks to see the demo monitor run.
metadata:
  version: 0.1.0
  author: Ilya Shulgin
  tags: [monitors, hooks, demo, plugin]
---

# Demo monitor

Invoking this skill is what starts the monitor. `monitors/monitors.json` declares
it with `"when": "on-skill-invoke:demo-monitor"`, so it is not running in an
ordinary session and it is running now because you were dispatched.

## What just happened

A **monitor** is a long-running command registered by a plugin. Claude Code
starts it in the background and turns every line it writes to stdout into a
notification. That is the whole contract — no JSON protocol, no exit-code
meaning, no stdin. A program that prints is a monitor.

That makes it the opposite half of a hook:

| | Hook | Monitor |
| --- | --- | --- |
| Runs | at a fixed lifecycle event | continuously, for the session |
| Triggered by | Claude Code, synchronously | itself — the outside world |
| Talks back via | exit code and stdout JSON | one notification per stdout line |
| Can block a turn | yes (`PreToolUse` can deny) | no |

Use a hook to enforce something at a known moment. Use a monitor to notice
something that happens on its own schedule: a log line, a build finishing, a
file changing, a queue draining.

## What this one does

`monitors/scripts/demo_monitor.py` watches the JSONL log that
`hooks/scripts/demo_hook.py` appends to, and prints one line per new entry:

```
demo-hook: PostToolUse  Write  skills/demo-args/SKILL.md
```

So the two deterministic mechanisms in this plugin are wired to each other: the
hook records a file edit, the monitor notices the record and tells you about it.
It stops on its own after 50 notifications, and honours
`AI_AGENCY_DEMO_MONITOR=off`.

## What to do now

1. Tell the user the monitor is running and what it is watching.
2. Offer to demonstrate it: edit any file in the repo, and within a couple of
   seconds a notification should arrive naming the tool and the path — the hook
   wrote the entry, the monitor read it back.
3. If nothing arrives, say so rather than pretending it worked, and check by
   hand:

   ```bash
   python3 monitors/scripts/demo_monitor.py --check
   python3 hooks/scripts/demo_hook.py --tail
   ```

   An empty log means the hook is not firing, which is a hook problem, not a
   monitor one — [`hooks/README.md`](../../hooks/README.md) covers that side.

Do not offer to change what the monitor watches or to register new monitors
unless asked. [`monitors/README.md`](../../monitors/README.md) is the reference
for writing one.
