# Contributing

## Adding a skill

```bash
cp -r templates/skill-template skills/<skill-name>
```

Rules:

- Folder name is kebab-case and **must equal** the `name` in frontmatter.
- `SKILL.md` is required. Frontmatter needs `name` and `description`.
- `description` is the only thing the model sees when deciding whether to load
  the skill. Write it in the third person and state both *what it does* and
  *when to use it*. Include trigger words a user would actually type.
- Keep `SKILL.md` under ~500 lines. Push detail into sibling files
  (`reference.md`, `examples.md`, `scripts/`) and link to them — they load only
  when needed.
- Prefer one skill per capability over one mega-skill.

### Frontmatter fields

| Field | Required | Notes |
|---|---|---|
| `name` | yes | kebab-case, ≤ 64 chars, matches folder name |
| `description` | yes | ≤ 1024 chars, third person, what + when |
| `license` | no | SPDX identifier |
| `allowed-tools` | no | tools pre-approved for the turn that invokes the skill; string or list |
| `metadata` | no | free-form map (`version`, `author`, `tags`, …) |
| `argument-hint` | no | autocomplete hint, e.g. `"[issue-number] [branch]"` — quote it |
| `arguments` | no | named positional arguments for `$name` substitution |
| `disable-model-invocation` | no | `true` = you invoke it, Claude never does |
| `user-invocable` | no | `false` = Claude invokes it, you never do |

Everything below `metadata` is Claude Code / plugin only. A claude.ai upload or
`package_skill.py` accepts just `name`, `description`, `license`,
`compatibility`, `metadata`, and `allowed-tools`, and hard-errors on the rest.
Check portability with:

```bash
python3 scripts/validate_skills.py --spec-frontmatter
```

## Skills as slash commands

Every skill is also a slash command. A repo skill ships in the plugin, so
`skills/foo/` is `/ai-agency-skills:foo`, with bare `/foo` working unless
another command claims the name. Anything typed after the command is passed as
arguments and substituted into the body before Claude sees it:

| Placeholder | Expands to |
|---|---|
| `$ARGUMENTS` | everything after the command, raw and unsplit |
| `$0`, `$1`, … | positional, **0-based** — `$0` is the first argument, not the command |
| `$ARGUMENTS[N]` | long form of the above |
| `$name` | named argument declared in `arguments`, mapped by position |
| `${CLAUDE_SKILL_DIR}` | this skill's directory — use it to reference bundled files |

Two traps: an indexed placeholder with no argument behind it stays in the text
verbatim, while a named one expands to an empty string; and `` !`command` ``
injection aborts the whole invocation on a non-zero exit, so append `|| true`.

`skills/demo-args/` is a working demonstration — run `/demo-args "hello world"
json` to watch each form resolve, and see its
[reference.md](skills/demo-args/reference.md) for the full rules.

## Adding an MCP server

Edit `.mcp.json`; `templates/mcp-server.json` has a stdio and an HTTP example to
copy from.

Rules:

- A server is **either** stdio (`command`, optional `args`/`env`/`cwd`) **or**
  remote (`url`, optional `headers`/`headersHelper`), never both.
- **No literal credentials.** This file is committed. Use `${ENV_VAR}`, which
  expands in `command`, `args` and `env` for stdio servers and in `url`,
  `headers` and `headersHelper` for remote ones. The validator warns when a key
  matching `key|token|secret|password|credential|auth` holds a value that is not
  an environment reference.
- `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}` and `${CLAUDE_PROJECT_DIR}`
  expand in the same places. A `${CLAUDE_PLUGIN_ROOT}` path must point at a file
  this repo actually ships — the validator checks.
- It stays at the repo root rather than behind a `mcpServers` override in
  `plugin.json`, because that path also works when the repo is opened as a
  project rather than installed as a plugin.

## Adding a monitor

Edit `monitors/monitors.json`; `templates/monitor.json` has both `when` forms.

Rules:

- The manifest is a **JSON array**, not an object keyed by event. `hooks.json`
  is the one that is keyed.
- `name`, `command` and `description` are required and must be non-empty.
  `name` must be unique — it is what stops a reload starting a second copy.
- `when` is `"always"` (the default) or `"on-skill-invoke:<skill-name>"`, and
  the named skill must exist in `skills/`.
- **Default to opt-in.** Every stdout line becomes a notification, which
  interrupts. Unless a monitor is genuinely wanted in every session, register it
  `on-skill-invoke:` and let someone ask for it.
- **Flush every line.** Python buffers stdout when it is not a terminal, so an
  unflushed monitor looks like a dead one. `print(..., flush=True)` or `python3 -u`.
- Quote path placeholders in `command` — an installed plugin path can contain
  spaces.
- Monitors are an experimental plugin component; the manifest location may move.

[`monitors/README.md`](monitors/README.md) covers the contract in full.

## Adding an agent

```bash
cp templates/agent-template.md agents/<agent-name>.md
```

Rules:

- File name is kebab-case and **must equal** the `name` in frontmatter.
- Frontmatter needs `name` and `description`; `tools` (comma-separated allowlist)
  and `model` are optional. Omit `tools` to inherit everything.
- Keep the agent file thin: identity, ground truth, routing table, guardrails.
  Procedure goes in a skill so it loads only when needed.
- Inside the `## Routing` section, a backticked kebab-case token is read as a
  skill name and must exist in `skills/`. That is what catches a routing typo,
  which otherwise dead-ends silently at runtime.
- Restrict `tools` deliberately. An agent that can send email or submit forms
  should have to be given those tools on purpose.

## Adding a hook

Hooks live in [`hooks/hooks.json`](hooks/hooks.json) and ship with the plugin,
so they run on other people's machines on every matching event. Treat them
accordingly:

- Point at bundled scripts through `${CLAUDE_PLUGIN_ROOT}`, in exec form
  (`"command": "python3", "args": ["${CLAUDE_PLUGIN_ROOT}/hooks/scripts/x.py"]`).
  A relative path resolves against the session's working directory, not the plugin.
- Match as narrowly as the job allows, and set a `timeout`. A hook on
  `PreToolUse` with no matcher runs on every tool call in every turn.
- Fail open. Exit 0 unless you mean to block; exit 2 is a policy decision, and
  stderr becomes the reason Claude sees.
- Stay quiet on success. stdout and stderr land in Claude's context or the
  user's transcript on most events.
- Parse the event JSON with Python's stdlib, not `jq` — it isn't installed
  everywhere, and this repo already depends on `python3`.
- Never log file contents or command strings, and cap anything you write.

[`hooks/README.md`](hooks/README.md) covers the full contract and the demo hook
that follows all of the above. `python3 scripts/validate_skills.py` checks the
manifest's shape and that referenced scripts exist; test the handler itself by
piping a sample event at it:

```bash
echo '{"hook_event_name":"PostToolUse","tool_name":"Write","tool_input":{"file_path":"README.md"},"session_id":"demo"}' \
  | python3 hooks/scripts/demo_hook.py; echo "exit=$?"
```

## Adding reference docs

Anything that isn't a runtime skill goes in `docs/`. No schema — just keep
filenames descriptive and add a link from `docs/README.md`.

## Before opening a PR

```bash
python3 scripts/validate_skills.py
```

CI runs this on every push and PR. Fix all errors; warnings are advisory.

## Commit style

Conventional Commits:

```
feat(skills): add competitor-research skill
fix(skills): tighten trigger wording in seo-audit description
docs: expand docs/README index
chore(ci): bump actions/checkout
```
