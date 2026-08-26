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
├── agents/                   # subagent definitions, one .md per agent
│   └── job-hunter.md
├── skills/                   # source of truth: one folder per skill
│   └── example-skill/
│       └── SKILL.md
├── docs/                     # free-form reference notes, not runtime skills
│   ├── README.md
│   └── job-search/           # working data for the job-hunter agent
├── templates/
│   └── skill-template/       # copy this to start a new skill
│       └── SKILL.md
├── scripts/
│   └── validate_skills.py    # frontmatter + structure linter
└── .github/workflows/ci.yml
```

`skills/` is the source of truth for capabilities. `agents/` holds subagent
definitions — thin files that carry identity, a tool allowlist, and routing, and
delegate procedure to skills. `docs/` is for anything that isn't runtime — research
notes, playbooks, client context, architecture decisions, and per-agent working
data. Adding a new top-level area later (e.g. `mcp/`, `prompts/`) is fine; the
validator looks at `skills/` and `agents/`.

## Quick start

Create a new skill:

```bash
cp -r templates/skill-template skills/my-new-skill
$EDITOR skills/my-new-skill/SKILL.md
python3 scripts/validate_skills.py
```

Create a new agent:

```bash
cp templates/agent-template.md agents/my-agent.md
$EDITOR agents/my-agent.md          # file name must match frontmatter `name`
python3 scripts/validate_skills.py
```

## Slash commands and arguments

Every skill is also a slash command, and anything typed after it is substituted
into the skill body before Claude sees it — `$ARGUMENTS` for the raw string,
`$0`/`$1` positionally (0-based), or named arguments declared in frontmatter.

```
/demo-args "hello world" json some trailing notes
```

[`skills/demo-args/`](skills/demo-args/SKILL.md) is a live demonstration: it
prints what every placeholder expanded to, including the cases that surprise
people. Its [reference.md](skills/demo-args/reference.md) is the full rule set;
[CONTRIBUTING.md](CONTRIBUTING.md) has the short version.

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
python3 scripts/validate_skills.py          # lint every skill and agent
python3 scripts/validate_skills.py skills/x # lint one skill
```

CI runs the same check on every push and pull request.

## Agents

| Agent | What it does |
|---|---|
| [job-hunter](agents/job-hunter.md) | Runs the senior SWE → senior AI engineer job search: sourcing, applications, pipeline, gap plan, interview prep. Working data in [docs/job-search/](docs/job-search/README.md). |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
