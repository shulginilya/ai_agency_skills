# Arguments and slash commands — reference

Detail for [SKILL.md](SKILL.md). Nothing here is substituted: sibling files are
read as plain text, so the placeholders below appear literally.

Source: [Claude Code — Extend Claude with skills](https://code.claude.com/docs/en/skills).

## 1. A skill *is* a slash command

Custom commands and skills are the same mechanism. `.claude/commands/deploy.md`
and `.claude/skills/deploy/SKILL.md` both produce `/deploy`. The skill form adds
a directory for supporting files, richer frontmatter, and automatic invocation
by Claude when the `description` matches.

Where the command name comes from:

| Skill location | Command |
| --- | --- |
| `~/.claude/skills/<dir>/SKILL.md` | `/<dir>` — frontmatter `name` is only a display label |
| `.claude/skills/<dir>/SKILL.md` | `/<dir>` |
| `apps/web/.claude/skills/<dir>/SKILL.md` | `/apps/web:<dir>` when the bare name clashes |
| `.claude/commands/<file>.md` | `/<file>` |
| `<plugin>/skills/<dir>/SKILL.md` | `/<plugin>:<dir>`, or `/<plugin>:<name>` when frontmatter sets `name` |

Skills in this repo are plugin skills, so `demo-args` is `/ai-agency-skills:demo-args`,
with bare `/demo-args` working as long as nothing else claims it.

## 2. Substitutions available in the body

| Placeholder | Expands to |
| --- | --- |
| `$ARGUMENTS` | Everything typed after the command, raw. If the body never mentions it, Claude Code appends `ARGUMENTS: <value>` to the end instead |
| `$ARGUMENTS[N]` | The Nth argument, 0-based |
| `$N` | Shorthand for the above — `$0` is the **first** argument |
| `$name` | Named argument declared in the `arguments` frontmatter list, mapped by position |
| `${CLAUDE_SKILL_DIR}` | Directory holding this `SKILL.md` — use it to reference bundled files |
| `${CLAUDE_PROJECT_DIR}` | Project root |
| `${CLAUDE_SESSION_ID}` | Current session ID |
| `${CLAUDE_EFFORT}` | `low` / `medium` / `high` / `xhigh` / `max` |
| `${CLAUDE_PLUGIN_ROOT}` | Plugin install directory — plugin skills only |
| `${CLAUDE_PLUGIN_DATA}` | Plugin data directory that survives updates — plugin skills only |

### Rules worth memorising

- **`$0` is the first argument.** Not the command name. This is the most common
  mistake for anyone coming from shell scripting.
- **Splitting uses shell-style quoting.** `/my-skill "hello world" second` gives
  `$0` = `hello world` and `$1` = `second`. `$ARGUMENTS` always holds the raw
  string as typed, unsplit.
- **Missing arguments behave differently by form.** An indexed placeholder with
  nothing behind it — say `$2` when one argument was passed — is left in the
  content *verbatim*. A named placeholder expands to an empty string. Write the
  body so both cases degrade sensibly.
- **Escaping.** A single backslash before the token prints it literally:
  `\$1.00`, `\$ARGUMENTS`, `\$topic`. It works only for argument placeholders —
  the `${CLAUDE_*}` variables cannot be escaped, so to show one literally, break
  it up in prose instead.
- **Substitution is textual.** Backticks and code fences do not protect a
  placeholder; it expands inside them too.
- **One pass.** Substitution runs once over the original file; injected output
  is not rescanned.

## 3. Frontmatter that shapes the command

| Field | Effect |
| --- | --- |
| `argument-hint` | Text shown in `/` autocomplete, e.g. `[issue-number]` or `[filename] [format]`. Quote it in YAML — an unquoted `[a] [b]` parses as a list |
| `arguments` | Named positional arguments for `$name` substitution. Space-separated string or YAML list; order maps to position |
| `disable-model-invocation` | `true` keeps the skill out of Claude's automatic selection and out of the skill listing — you invoke it, Claude never does. The right default for anything with side effects: deploy, commit, send |
| `user-invocable` | `false` hides it from the `/` menu — Claude only. The inverse of the above |
| `allowed-tools` | Tools pre-approved for the turn that invokes the skill. Also what keeps an injected shell command from aborting the invocation. Clears on the next message |
| `disallowed-tools` | Tools removed from the pool while the skill is active |
| `context: fork` | Runs the skill in a subagent; pair with `agent:` and `background:` |
| `model`, `effort` | Override model or effort for the invoking turn |
| `paths` | Globs that limit automatic activation to matching files |

`demo-args` deliberately leaves `disable-model-invocation` unset so it can be
demonstrated both ways: typed as `/demo-args …`, or picked up by Claude from its
`description`.

## 4. Injecting shell output

A line-leading or whitespace-preceded `` !`command` `` runs before the content
reaches Claude and is replaced by the output. For several commands, open a
fenced block with three backticks followed by `!`, one command per line.

Constraints that bite:

- A non-zero exit **aborts the whole invocation** — Claude sees nothing. Append
  `|| true` to anything expected to fail. Search and comparison commands get a
  carve-out for exit code 1 only.
- Injected commands never prompt. If the permission check does not return
  *allow*, the invocation aborts, so pre-approve them in `allowed-tools`.
- They run in the session's current working directory. Use `${CLAUDE_SKILL_DIR}`
  or `${CLAUDE_PROJECT_DIR}` for paths that must resolve identically every time.
- 2-minute timeout, stderr merged into stdout.
- Never executed for skills synced from a claude.ai account.
- Disabled globally by `"disableSkillShellExecution": true` in settings.

Do not build an injected command out of argument placeholders. Have Claude run
the command itself with the expanded values instead — it is deterministic and it
survives a shell that quotes differently.

## 5. Portability

Claude Code accepts every field above. The [Agent Skills](https://agentskills.io)
spec — which governs claude.ai uploads, the Skills API, and `package_skill.py` —
allows only `name`, `description`, `license`, `compatibility`, `metadata`, and
`allowed-tools`. Anything else is a hard error on upload:

```
Unexpected key(s) in SKILL.md frontmatter: argument-hint. Allowed properties are: allowed-tools, compatibility, description, license, metadata, name
```

So a skill that uses `argument-hint`, `arguments`, or `disable-model-invocation`
is Claude Code / plugin only. Body features are split the same way: shell
injection and the `${CLAUDE_*}` variables do not work in claude.ai chat or
through the API, though a plain `$ARGUMENTS` body is harmless there.

## 6. Copy-paste starting point

```yaml
---
name: fix-issue
description: Fixes a GitHub issue by number, following the repo's coding standards. Use when the user asks to fix, triage, or start work on a specific issue.
argument-hint: "[issue-number] [branch]"
arguments: [issue, branch]
disable-model-invocation: true
allowed-tools: Bash(gh issue view:*)
---

Repo: !`gh repo view --json nameWithOwner -q .nameWithOwner || true`

Fix issue #$issue on branch `$branch`.

Run `gh issue view $issue --json title,body` to read the issue, then work the
fix. (Reading it as a normal tool call rather than an injected command keeps the
argument out of the pre-render shell — see section 4.)
```
