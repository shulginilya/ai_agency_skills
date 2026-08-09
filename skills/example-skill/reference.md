# Reference

Detail that would bloat `SKILL.md`. The agent reads this file only after it has
decided the skill is relevant — that's the point of splitting it out.

## Progressive disclosure

Three levels of loading:

1. **Frontmatter** (`name` + `description`) — always in context, cheap.
2. **`SKILL.md` body** — loaded when the skill triggers.
3. **Bundled files** (`reference.md`, `examples.md`, `scripts/`) — loaded only
   when the instructions point at them.

Keep level 1 tight, level 2 under ~500 lines, and push everything else to
level 3.

## Bundled scripts

Scripts in a skill's `scripts/` directory can be executed directly rather than
re-derived by the model each run. Reference them by relative path from
`SKILL.md` and state exactly how to invoke them.
