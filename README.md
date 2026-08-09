# ai_agency_skills

A repository of reusable **Agent Skills** and supporting reference docs.

Skills follow the [Anthropic Agent Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)
format: one directory per skill containing a `SKILL.md` with YAML frontmatter.
The repo also doubles as an installable **plugin marketplace** for Claude Code / Cowork.

## Layout

```
.
├── .claude-plugin/
│   ├── marketplace.json      # makes this repo installable as a plugin source
│   └── plugin.json           # the repo root *is* the plugin bundle
├── skills/                   # source of truth: one folder per skill
│   └── example-skill/
│       └── SKILL.md
├── docs/                     # free-form reference notes, not runtime skills
│   └── README.md
├── templates/
│   └── skill-template/       # copy this to start a new skill
│       └── SKILL.md
├── scripts/
│   └── validate_skills.py    # frontmatter + structure linter
└── .github/workflows/ci.yml
```

`skills/` is the source of truth. `docs/` is for anything that isn't a skill —
research notes, playbooks, client context, architecture decisions. Adding a new
top-level area later (e.g. `agents/`, `mcp/`, `prompts/`) is fine; the validator
only looks at `skills/`.

## Quick start

Create a new skill:

```bash
cp -r templates/skill-template skills/my-new-skill
$EDITOR skills/my-new-skill/SKILL.md
python3 scripts/validate_skills.py
```

## Using these skills

**Personal (single skill):** copy the skill folder into `~/.claude/skills/`.

**Project-scoped:** copy into `<project>/.claude/skills/`.

**As a plugin marketplace (recommended):**

```
/plugin marketplace add shulginilya/ai_agency_skills
/plugin install ai-agency-skills@ai-agency-skills
```

## Validation

```bash
python3 scripts/validate_skills.py          # lint every skill
python3 scripts/validate_skills.py skills/x # lint one
```

CI runs the same check on every push and pull request.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
