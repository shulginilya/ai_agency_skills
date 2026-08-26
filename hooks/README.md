# Hooks

Hooks are the deterministic half of this repo. A skill *asks* Claude to do
something; a hook *makes* something happen at a fixed point in the session
lifecycle, whether Claude cooperates or not. This directory ships one working
demonstration and the rules behind it.

```
hooks/
├── hooks.json              # what the plugin registers — the canonical plugin location
├── scripts/
│   └── demo_hook.py        # the handler: stdlib Python, no jq, runs anywhere python3 does
└── README.md               # this file
```

## The demo hook

`hooks.json` registers one handler on two events:

| Event | Matcher | When it fires |
| --- | --- | --- |
| `SessionStart` | *(none — fires every time)* | a session starts, resumes, clears, compacts or forks |
| `PostToolUse` | `Write\|Edit` | after each successful file edit |

The handler appends one JSON line per event to a per-session log under the
plugin's own data directory and exits 0. That is the whole behaviour. It
prints nothing, blocks nothing, touches no file you own, and records metadata
only — event, tool, repo-relative path, permission mode — never file contents,
command strings, or environment.

That restraint is the point: a hook that ships with a plugin runs on other
people's machines, on every matching tool call, forever. A demo you can install
without thinking about it has to be one that cannot surprise you.

### Try it

Install the plugin, edit a file in any session, then read the log back:

```bash
python3 hooks/scripts/demo_hook.py --tail     # last 20 entries
python3 hooks/scripts/demo_hook.py --where    # where the log lives
```

```
2026-08-26T10:36:18Z  SessionStart  session=abc123de mode=default agent=main source=startup
2026-08-26T10:36:18Z  PostToolUse   session=abc123de mode=acceptEdits agent=main tool=Write path=skills/demo-args/SKILL.md
```

You do not need a session to exercise it. Hooks are ordinary programs that read
JSON on stdin, so pipe an event at it and check the exit code — the first thing
to do when a hook misbehaves:

```bash
echo '{"hook_event_name":"PostToolUse","tool_name":"Write","tool_input":{"file_path":"README.md"},"session_id":"demo"}' \
  | python3 hooks/scripts/demo_hook.py; echo "exit=$?"
```

### Turning it off

Pick whichever is least invasive:

- `AI_AGENCY_DEMO_HOOK=off` in your environment — the script's own kill switch.
- `/hooks` in Claude Code to inspect what is registered, or `"disableAllHooks": true`
  in a settings file to stop every hook at that scope.
- Delete `hooks/hooks.json` from your copy of the plugin.

Set `AI_AGENCY_DEMO_HOOK_DEBUG=1` for the opposite: the script stops swallowing
problems and reports them on stderr, which `PostToolUse` shows to Claude.

## Anatomy of `hooks.json`

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python3",
            "args": ["${CLAUDE_PLUGIN_ROOT}/hooks/scripts/demo_hook.py"],
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

- **Event name** keys the top level. Every event is one array of matcher groups,
  and every group holds its own list of handlers.
- **`matcher`** filters. Bare names and `|`-separated lists are compared as
  exact strings (`Write|Edit`); anything containing other characters is treated
  as an unanchored JavaScript regex (`mcp__memory__.*`). Matching is
  case-sensitive, and omitting the field matches everything — which is what the
  `SessionStart` entry does. What the matcher compares against varies by event:
  tool name for the tool events, `startup|resume|clear|compact|fork` for
  `SessionStart`, agent type for `SubagentStart`, and so on.
- **`command` + `args`** is *exec form*: the process is spawned directly, with
  no shell in between. Use it whenever a path is involved. Drop `args` and you
  get *shell form*, which brings pipes, globs and `&&` — and word-splitting on
  the space in `C:\Users\Ilya Shulgin\...`.
- **`${CLAUDE_PLUGIN_ROOT}`** resolves to wherever the plugin was installed.
  Bundled scripts must be addressed through it; a relative path resolves against
  the session's working directory, not the plugin. The siblings are
  `${CLAUDE_PROJECT_DIR}` (project root) and `${CLAUDE_PLUGIN_DATA}` (a data
  directory that survives plugin updates — where this demo writes).
- **`timeout`** in seconds. The default is generous (10 minutes for command
  hooks); a hook that runs on every edit should be given a short leash instead.
  On timeout the hook is cancelled, renders no decision, and the action proceeds.

`hooks/hooks.json` is the default path. A plugin can point elsewhere with
`"hooks": "./config/hooks.json"` in `plugin.json`, or inline the whole block there.

## The contract

**In.** Every hook receives one JSON object on stdin: `session_id`,
`transcript_path`, `cwd`, `permission_mode`, `hook_event_name`, plus
event-specific fields — `tool_name` and `tool_input` for the tool events,
`source` for `SessionStart`, `stop_hook_active` for `Stop`.

**Out.** The exit code is the primary channel:

| Exit code | Meaning |
| --- | --- |
| `0` | Success. stdout is parsed as JSON if it looks like JSON, otherwise logged for debugging — except on `UserPromptSubmit`, `UserPromptExpansion` and `SessionStart`, where plain stdout is fed to Claude as context. |
| `2` | Blocking error. Blocks on the events that support it (`PreToolUse`, `UserPromptSubmit`, `PreCompact`, …), keeps Claude going on `Stop`/`SubagentStop`, and is ignored on the rest. stderr goes to Claude as the reason. |
| anything else | Non-blocking error. Logged; the action proceeds. |

For anything richer than a yes/no, print JSON on stdout:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "package-lock.json is generated; run npm install instead",
    "additionalContext": "text appended to Claude's context"
  },
  "systemMessage": "shown in the transcript"
}
```

`permissionDecision` is `allow`, `deny` or `escalate`. Hooks can only tighten:
a `deny` holds even under `bypassPermissions`, while an `allow` cannot override
a deny rule in settings.

## Where a hook can live

| Location | Scope | Shareable |
| --- | --- | --- |
| `hooks/hooks.json` in a plugin | wherever the plugin is enabled | yes, bundled |
| `.claude/settings.json` | one project, everyone on it | yes, committed |
| `.claude/settings.local.json` | one project, just you | no, gitignored |
| `~/.claude/settings.json` | all your projects | no |
| Skill frontmatter | from the moment the skill is invoked, for the rest of the session | yes |
| Subagent frontmatter | only while that subagent runs | yes |
| Managed policy settings | the whole organisation | admin-controlled |

Skill frontmatter looks tempting for a demo — it registers on `/skill-name` and
stays opt-in — but `${CLAUDE_SKILL_DIR}` is *not* substituted in frontmatter
hook commands ([claude-code#36135](https://github.com/anthropics/claude-code/issues/36135),
closed as not planned), so a skill cannot portably point at a script it bundles.
That is why this demo ships as plugin JSON.

## Best practices

Rules this demo follows, and the reasoning:

1. **Fail open.** A hook that throws is a hook that breaks someone's session.
   Catch everything, exit 0, and reserve exit 2 for a decision you actually mean.
2. **Be silent when nothing is wrong.** stdout and stderr are not free: on most
   events they land in Claude's context or the user's transcript. Log to a file.
3. **Reserve exit 2 for policy.** `PostToolUse` cannot undo anything — the tool
   already ran. Blocking belongs in `PreToolUse`.
4. **Match narrowly.** `Write|Edit` costs two string comparisons. A matcher-less
   `PreToolUse` hook runs on every tool call in every turn.
5. **Set a timeout.** Every hook on a per-tool-call event is latency the user
   pays each time.
6. **Exec form for paths, quotes in shell form.** `"command": "x", "args": [...]`
   avoids the shell entirely; if you need the shell, wrap the placeholder:
   `"\"${CLAUDE_PLUGIN_ROOT}\"/scripts/x.sh"`.
7. **No dependencies you did not ship.** The official examples parse JSON with
   `jq`, which is not installed on a stock Windows machine. Python's stdlib is a
   safer default; this repo already requires `python3` for the validator.
8. **Treat the event as untrusted input.** Paths and ids come from a model.
   Never interpolate them into a shell command or a filename without sanitising
   — `safe_stem()` in the script exists because `session_id` chooses a filename.
9. **Record metadata, never content.** File contents and command strings are the
   most sensitive thing crossing a hook. Keep them out of anything durable.
10. **Bound your writes.** Logs need a size cap and a home inside
    `${CLAUDE_PLUGIN_DATA}` — never scattered through the user's project.
11. **Don't lean on a sibling.** Hooks on one event run in parallel, and one
    returning `deny` does not stop the others' side effects. For `PreToolUse`
    decisions the most restrictive answer wins: `deny` > `defer` > `ask` > `allow`.
12. **Guard `Stop` hooks.** Claude Code overrides a `Stop` hook after eight
    consecutive blocks; check `stop_hook_active` on stdin and exit 0 when it is
    true, or you will loop.

## Writing your own

```bash
cp hooks/scripts/demo_hook.py hooks/scripts/my_hook.py
$EDITOR hooks/hooks.json          # register it on an event
python3 scripts/validate_skills.py
```

The validator parses `hooks/hooks.json`, checks the shape of each entry, and
verifies that every `${CLAUDE_PLUGIN_ROOT}` path a command points at exists.
Test the handler by piping sample JSON at it before you ever start a session,
and use `/hooks` in Claude Code to confirm it registered where you think.

For a skill that shows *itself* off in the same spirit, see
[`skills/demo-args/`](../skills/demo-args/SKILL.md). Conventions for both live
in [CONTRIBUTING.md](../CONTRIBUTING.md).

## Reference

- [Hooks reference](https://code.claude.com/docs/en/hooks) — every event, field and schema
- [Automate actions with hooks](https://code.claude.com/docs/en/hooks-guide) — worked examples and troubleshooting
- [Plugins reference](https://code.claude.com/docs/en/plugins-reference) — where plugin hooks live
