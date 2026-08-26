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
- Restrict `tools` deliberately. An agent that can send email or submit forms
  should have to be given those tools on purpose.

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
