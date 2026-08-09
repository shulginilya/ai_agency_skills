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
| `name` | yes | kebab-case, ≤64 chars, matches folder name |
| `description` | yes | ≤1024 chars, third person, what + when |
| `license` | no | SPDX identifier |
| `allowed-tools` | no | list restricting tools while the skill is active |
| `metadata` | no | free-form map (`version`, `author`, `tags`, …) |

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
