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
├── .mcp.json                 # MCP servers the plugin provides
├── agents/                   # subagent definitions, one .md per agent
│   └── job-hunter.md
├── skills/                   # source of truth: one folder per skill
│   └── example-skill/
│       └── SKILL.md
├── hooks/                    # deterministic lifecycle automation shipped with the plugin
│   ├── hooks.json            # what the plugin registers, and on which events
│   ├── scripts/demo_hook.py
│   └── README.md
├── monitors/                 # background processes that notify Claude (experimental)
│   ├── monitors.json         # what the plugin registers, and when each starts
│   ├── scripts/demo_monitor.py
│   └── README.md
├── docs/                     # free-form reference notes, not runtime skills
│   ├── README.md
│   └── job-search/           # working data for the job-hunter agent
├── templates/
│   ├── skill-template/       # copy this to start a new skill
│   │   └── SKILL.md
│   ├── agent-template.md
│   ├── mcp-server.json
│   └── monitor.json
├── scripts/
│   └── validate_skills.py    # frontmatter + structure linter
└── .github/workflows/ci.yml
```

Every path above is the location the Claude Code plugin format already expects,
because this repo root *is* the plugin bundle — there is no local convention to
learn.

| Area | What it is |
|---|---|
| `skills/` | The source of truth for capabilities. One folder per skill |
| `agents/` | Subagent definitions — identity, tool allowlist, routing. Procedure lives in skills |
| `hooks/` | The deterministic half: commands run at fixed lifecycle points, whether Claude thinks to or not |
| `monitors/` | The other deterministic half: background processes whose stdout becomes notifications |
| `.mcp.json` | MCP servers. Also read by Claude Code when this repo is opened as a project, not only when installed as a plugin |
| `docs/` | Anything that isn't runtime — notes, playbooks, per-agent working data |

The plugin format supports more component types than this repo uses —
`commands/`, `workflows/`, `output-styles/`, `bin/`, `.lsp.json`, themes and
channels. Adding one later is fine; `scripts/validate_skills.py` checks
`skills/`, `agents/`, and every manifest listed above.

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

Add an MCP server or a monitor:

```bash
$EDITOR .mcp.json                   # templates/mcp-server.json has both shapes
$EDITOR monitors/monitors.json      # templates/monitor.json has both `when` forms
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

## Hooks

A skill asks Claude to do something; a hook makes something happen. Anything in
[`hooks/hooks.json`](hooks/hooks.json) is registered whenever this plugin is
enabled, on events from `SessionStart` to `PreToolUse`.

The one hook shipped here is a demonstration:
[`hooks/scripts/demo_hook.py`](hooks/scripts/demo_hook.py) appends one metadata
line per file edit to a capped log in the plugin's own data directory, prints
nothing, blocks nothing, and swallows its own errors.

```bash
python3 hooks/scripts/demo_hook.py --tail    # read back what it captured
python3 hooks/scripts/demo_hook.py --where   # where the log lives
```

Turn it off with `AI_AGENCY_DEMO_HOOK=off`, or with `"disableAllHooks": true` in
a settings file. [`hooks/README.md`](hooks/README.md) is the full walkthrough:
the JSON anatomy, the stdin/exit-code contract, where hooks can live, and the
practices this one follows.

## Monitors

A hook fires when Claude Code reaches a known point. A **monitor** runs for the
whole session and turns every line it prints on stdout into a notification —
so Claude can react to something that happens on its own schedule: a log line,
a build finishing, a queue draining.

The one monitor shipped here is a demonstration wired to the demo hook: it
watches that hook's audit log and reports each new entry. It is registered
`"when": "on-skill-invoke:demo-monitor"` rather than `"always"`, so it does not
run in ordinary sessions — anything that generates notifications should be opt
in. Run `/demo-monitor` to start it, or drive it by hand:

```bash
python3 monitors/scripts/demo_monitor.py --check      # what it would watch
python3 monitors/scripts/demo_monitor.py --backfill   # replay the existing log too
```

[`monitors/README.md`](monitors/README.md) is the full walkthrough: the
one-line-per-notification contract, the manifest fields, and why monitors are
still an experimental plugin component.

## MCP servers

`.mcp.json` is where MCP servers live. It ships with the plugin *and* is what
Claude Code reads when this repo is opened as a project directly, which is why
it sits at the default path rather than behind a `mcpServers` override in
`plugin.json`.

It is committed, so no credential belongs in it. Use `${ENV_VAR}` — expansion
works in `command`, `args` and `env` for stdio servers, and in `url`, `headers`
and `headersHelper` for remote ones. The validator warns when a
credential-shaped key holds something that is not an environment reference.

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
python3 scripts/validate_skills.py          # lint every skill, agent and manifest
python3 scripts/validate_skills.py skills/x # lint one skill
```

The same run checks every manifest in the repo:

- `hooks/hooks.json` — valid JSON, known event names, usable handlers
- `monitors/monitors.json` — an array, required fields, unique names, and a
  `when` that is `"always"` or names a skill that exists
- `.mcp.json` — a usable shape per server, and no literal secrets
- `.claude-plugin/plugin.json` — component path overrides that point somewhere real
- every `${CLAUDE_PLUGIN_ROOT}` path in a hook, monitor or server command
- every skill an agent's routing table names

CI runs the same check on every push and pull request, plus a non-blocking
`--spec-frontmatter` report so it is visible when a skill has drifted out of
claude.ai-uploadable shape.

## Agents

| Agent | What it does |
|---|---|
| [job-hunter](agents/job-hunter.md) | Runs the senior SWE → senior AI engineer job search: sourcing, applications, pipeline, gap plan, interview prep. Working data in [docs/job-search/](docs/job-search/README.md). |

Every skill named in an agent's `## Routing` table must exist in `skills/`; the
validator treats a backticked kebab-case token in that section as a skill name
and errors on a typo.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
