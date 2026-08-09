---
name: example-skill
description: Reference implementation showing the structure of a skill in this repository. Use only as a formatting example when authoring a new skill; it performs no real work and should not be triggered for user tasks.
license: MIT
metadata:
  version: 1.0.0
  author: Ilya Shulgin
  tags: [meta, example]
---

# Example Skill

A minimal but complete skill, kept so the validator and CI always have something
to check and so new skills have a concrete model to copy.

## When to use

Never, in real work. Copy `templates/skill-template/` instead.

## Instructions

1. Read the frontmatter above — `name` matches the folder name, `description`
   states what and when.
2. Note that headings are short and instructions are imperative.
3. Note that supporting detail lives in [reference.md](reference.md) rather than
   inline, so it loads only when needed.

## Output

Nothing. This skill is illustrative.
