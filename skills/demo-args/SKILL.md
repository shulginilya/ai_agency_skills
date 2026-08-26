---
name: demo-args
description: Live demonstration of how a skill receives arguments when it is invoked as a slash command. Invoke it as /demo-args <topic> <format> [notes...] to see exactly what the whole-argument, positional, indexed, and named placeholders expanded to, along with the skill-directory and session variables. Use it as the copy-from reference when authoring a skill that takes arguments; it performs no real work.
license: MIT
argument-hint: "[topic] [format] [notes...]"
arguments: [topic, format]
allowed-tools: Bash(pwd) Bash(date)
metadata:
  version: 1.0.0
  author: Ilya Shulgin
  tags: [meta, demo, arguments, slash-command]
---

# Demo: arguments in a skill

This skill is a mirror. Everything in the "Captured arguments" table below was
written as a placeholder in `SKILL.md`; what you are reading now is the text
*after* Claude Code substituted it. Compare the two columns to see the mechanics.

Invoke it as:

```
/demo-args refactoring markdown some trailing notes
/demo-args "hello world" json          # quote multi-word values
/demo-args                             # no arguments — see the fallbacks below
```

In this repo the skill ships inside the `ai-agency-skills` plugin, so the full
command is `/ai-agency-skills:demo-args`; bare `/demo-args` also works unless
another command already claims that name.

## Captured arguments

| Placeholder in the source | Expanded to |
| --- | --- |
| `\$ARGUMENTS` — everything after the command | $ARGUMENTS |
| `\$ARGUMENTS[0]` — indexed, 0-based | $ARGUMENTS[0] |
| `\$0` — shorthand for the **first** argument | $0 |
| `\$1` — the **second** argument | $1 |
| `\$2` — the **third** argument | $2 |
| `\$topic` — named, from `arguments: [topic, format]` | $topic |
| `\$format` — named, second position | $format |
| `CLAUDE_SKILL_DIR` (wrapped in `${...}`) | ${CLAUDE_SKILL_DIR} |
| `CLAUDE_SESSION_ID` (wrapped in `${...}`) | ${CLAUDE_SESSION_ID} |
| `CLAUDE_EFFORT` (wrapped in `${...}`) | ${CLAUDE_EFFORT} |

## Injected shell output

The block below is a fenced code block opened with a bang (see `reference.md`
for the exact syntax). Claude Code ran it *before* this content reached Claude
and pasted the output in place — Claude never saw the commands themselves.

```!
pwd
date
```

## Your task

1. Restate the "Captured arguments" table to the user, dropping any row whose
   value came back unexpanded or empty, and say plainly which arguments were
   received.
2. Call out whichever of these actually happened this run:
   - **No arguments at all.** `$ARGUMENTS` is empty, the named placeholders
     `$topic` and `$format` expanded to empty strings, and the indexed ones
     (`\$0`, `\$1`, `\$2`) stayed in the text verbatim — that asymmetry is the
     single most surprising rule here.
   - **A missing positional.** Same rule: an index with no argument behind it is
     left as literal text, so never assume `\$2` holds a value.
   - **A quoted multi-word value.** Indexed and named arguments are split with
     shell-style quoting, so `"hello world"` is one argument; `$ARGUMENTS` alone
     keeps the raw string exactly as typed.
3. Note the off-by-one that catches people: `\$0` is the **first** argument, not
   the command name as in a shell script.
4. Offer to walk through [reference.md](reference.md) — the full substitution
   table, the frontmatter fields that control slash-command behaviour, escaping
   rules, and the portability caveats. It also lives at
   `${CLAUDE_SKILL_DIR}/reference.md`, which is how a skill points at its own
   bundled files no matter what directory the session is in.

Keep the whole response under roughly 30 lines. Do not do any other work: this
skill is a teaching demo and has no side effects.
