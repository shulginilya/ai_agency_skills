# Monitors

A skill *asks* Claude to do something. A hook *makes* something happen at a
fixed point in the session. A **monitor** notices something that happens on its
own schedule and tells Claude about it.

```
monitors/
├── monitors.json           # what the plugin registers — the canonical plugin location
├── scripts/
│   └── demo_monitor.py     # the handler: stdlib Python, no dependencies
└── README.md               # this file
```

> Monitors are an **experimental** plugin component. The manifest location and
> the `experimental.monitors` override in `plugin.json` may move before they
> stabilise. Nothing else in this repo depends on the monitor, so if the format
> changes, the blast radius is this directory.

## The contract

Claude Code runs each monitor's `command` as a persistent background process in
the session working directory and turns **every line it writes to stdout into a
notification**. That is all of it: no JSON protocol, no meaningful exit code, no
stdin. Any program that prints is a monitor.

Two consequences worth internalising before writing one:

- **Flush every line.** Python buffers stdout when it is not a terminal, so a
  monitor that does not flush looks like a monitor that is dead. `print(...,
  flush=True)`, or run with `python3 -u`.
- **Every line costs attention.** A notification interrupts. A monitor that
  prints once a second is a monitor that gets uninstalled. Print state
  *changes*, not state.

## The manifest

`monitors.json` is a **JSON array**, not an object — unlike `hooks/hooks.json`,
which is keyed by event.

| Field | Required | Notes |
| --- | --- | --- |
| `name` | yes | Unique within the plugin. Stops a reload starting a second copy |
| `command` | yes | Shell command, run for the session's lifetime |
| `description` | yes | Shown in the task panel and in notification summaries |
| `when` | no | `"always"` (default), or `"on-skill-invoke:<skill-name>"` |

`command` expands `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}`,
`${CLAUDE_PROJECT_DIR}` and any `${ENV_VAR}`. Quote the placeholder — an
installed plugin path can contain spaces:

```json
{
  "name": "deploy-status",
  "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/monitors/scripts/poll.py\"",
  "description": "Deployment status changes",
  "when": "on-skill-invoke:deploy"
}
```

`templates/monitor.json` has both `when` forms to copy from.

## The demo monitor

It is registered `"when": "on-skill-invoke:demo-monitor"` rather than
`"always"`, and that choice is the point. A demo that narrates every edit in
every session forever is a demo nobody keeps installed. It starts only when
`/demo-monitor` is dispatched, and stops itself after 50 notifications.

What it watches is the JSONL log that `hooks/scripts/demo_hook.py` writes, so
the two halves of this plugin's deterministic layer are connected: the hook
records a file edit, the monitor reads the record back and reports it.

```
demo-hook: SessionStart  (startup)
demo-hook: PostToolUse  Write  skills/demo-args/SKILL.md
```

### Try it without a session

A monitor is an ordinary program. Run it and watch — the first thing to do when
one misbehaves:

```bash
python3 monitors/scripts/demo_monitor.py --check      # what it would watch, then exit
python3 monitors/scripts/demo_monitor.py --backfill   # replay the existing log too
python3 monitors/scripts/demo_monitor.py              # watch (Ctrl-C to stop)
```

### Turning it off

- Do not invoke `/demo-monitor`. It does not start on its own.
- `AI_AGENCY_DEMO_MONITOR=off` makes it exit immediately if it does start.
- `"disableAllHooks": true` in a settings file, or disabling the plugin, stops
  everything in this repo including hooks.

## What the validator checks

`python3 scripts/validate_skills.py` reads `monitors.json` and reports:

- invalid JSON, or a top-level value that is not an array
- an entry missing `name`, `command` or `description`, or with a blank one
- a duplicate `name`
- a `when` that is neither `"always"` nor `on-skill-invoke:` a skill that
  actually exists in `skills/`
- a `${CLAUDE_PLUGIN_ROOT}` path in `command` that points at a file that is not
  in this repo
- unrecognised keys (a warning — the format is experimental and may grow)

## Practices this one follows

1. **Opt in, not opt out.** Anything that generates notifications defaults to
   silent.
2. **Bounded.** It stops after a fixed number of lines. A forgotten session
   cannot accrete noise.
3. **Flushes.** Every line, immediately.
4. **Survives its own bugs.** Any unexpected exception is caught and the process
   exits 0. A broken demo must not take a session down.
5. **Reads, never writes.** It touches nothing outside the hook's own log
   directory.
6. **Handles the log moving.** Truncation, rollover to a new session's file, and
   partial final lines are all expected, not crashes.
