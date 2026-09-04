## Problem

`README.md` lists five export targets in a table but explains only three of them
in prose. Someone exporting to a harness that isn't Claude got a single table row
— `generic | copied flat | copied | copied | copied` — and nothing else: not where
the bundle lands by default, not what is in it, not what to do with it once it
exists. The one target whose whole point is that the receiving harness knows none
of our conventions was the one target documented purely by convention.

Worse, two of the bullets under **What the exporter guarantees** were written as
if they held for every target. They do not. `export_generic` always copies and
writes no receipt, so "Symlinks by default" and "`--uninstall` removes our files"
were straightforwardly wrong for anyone reading them on the way to a generic
export.

`scripts/export.py` was also missing from the layout tree — it had existed for two
commits without appearing in the repo map that the tree is supposed to be.

## Proposal

Docs only; no behaviour changes.

| Change | |
|---|---|
| New section: **Exporting to a harness that isn't Claude** | three invocation forms, what the bundle contains, and why the manifest exists |
| New subsection: **A worked example** | real console output, the resulting tree, the `manifest.json`, and four numbered notes on wiring each component type into a loader of your own |
| Scoped two guarantee bullets | "Symlinks by default **on the two Claude Code targets**"; "Each **Claude Code** install writes a receipt" |
| New heading: **Exporting for upload to claude.ai** | the pre-existing paragraph, now a sibling of the other two rather than a dangling tail |
| Layout tree | `scripts/export.py` added |

## Design decisions worth reviewing

The underlying call is that this is a documentation ticket, not a fix — which
shapes the rest:

- **The `${CLAUDE_PLUGIN_ROOT}` gap is documented, not fixed.** `export_generic`
  copies `hooks/hooks.json` and `monitors/monitors.json` verbatim, while
  `export_claude_code` runs them through `substitute_plugin_root`. So a generic
  bundle ships two manifests containing a token that only expands inside a Claude
  Code plugin. The README now says so and tells the reader to define it or rewrite
  the paths. This is the bullet I most expect pushback on: the fix is roughly five
  lines and one could argue a README should not narrate a bug it could close. I
  kept the change docs-only so the fix gets its own reviewable ticket — see
  follow-ups.
- **The worked example passes `--dest` rather than showing the default.** The
  default is `dist/generic/`, which is gitignored, so an example built around it
  would put the reader's output somewhere they cannot see it in the repo. `--dest`
  is also the flag most people will actually want.
- **The console output in the example is real.** It came from an actual run
  against this repo; only the paths were rewritten to a neutral home directory.
  The `manifest.json` shown is truncated to three skills — illustrative of the
  shape, not a listing that goes stale on the next skill added.
- **The wiring notes are a numbered list per component type, not prose.** The
  reader at that point is writing a loader and wants a checklist of four
  decisions, one of which (hooks/monitors) they may legitimately skip.
- **Caveats come after the example, not before it.** First the thing to run, then
  what to watch out for.

## Acceptance criteria

- [x] The `generic` target has a prose section stating default destination, bundle
      contents, and the role of `manifest.json`
- [x] A worked example shows an invocation, its output, the resulting tree, and
      the manifest
- [x] Wiring guidance exists for each of skills, agents, MCP servers, hooks and
      monitors
- [x] No guarantee bullet claims for all targets something that holds only for the
      Claude Code ones
- [x] `scripts/export.py` appears in the layout tree
- [x] The `${CLAUDE_PLUGIN_ROOT}` behaviour of the generic target is stated
- [ ] Rendered markdown reviewed on GitHub (written and read as source only; the
      nested code fences and the `console` fence are the parts most likely to
      surprise)

## Out of scope / follow-ups

- [ ] **`python3 scripts/export.py --target generic` does not currently succeed on
      this repo.** The pre-export validator fails with
      `agents/manager-engineering.md: agent file has no YAML frontmatter delimited
      by '---'`. That file is untracked work in progress, unrelated to this change,
      but it means anyone following the new docs verbatim today gets a validator
      error instead of a bundle. The example output above was produced with
      `--skip-validate`.
- [ ] **Make `export_generic` substitute `${CLAUDE_PLUGIN_ROOT}`**, the way
      `export_claude_code` already does, and delete the caveat this ticket adds.
- [ ] **`manifest.json` lists only top-level agents.** The untracked
      `agents/agents/` directory (six worker agents) is copied into the bundle by
      `shutil.copytree` but never named in the manifest, so a harness that trusts
      the manifest cannot see it. Either the manifest should recurse or agents
      should not nest — a decision, not a typo.
- [ ] The example's `"mcpServers": []` is accurate (`.mcp.json` is currently
      empty), which means the docs never show a populated server entry.

## Notes for the reviewer

One file: `README.md`, +100 / −7. No code touched, so nothing to run; the only
verification performed was executing the documented command and copying its real
output.

While drafting this I corrected one claim in the new text: it originally said the
hook and monitor scripts both read JSON on stdin. `demo_monitor.py` is
argparse-driven and prints lines; only the hook reads stdin. Fixed before this
ticket was written.

The working tree also holds two untracked files — `agents/manager-engineering.md`
and `agents/agents/` — that are someone's in-progress agent work and form no part
of this change.
