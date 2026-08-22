---
name: agent-template
description: One or two sentences, third person, covering what this agent owns and when to hand work to it. Replace this entirely. File name must match this `name`.
tools: Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch, Skill
model: opus
---

# Agent Template

> Delete this blockquote. Keep the agent file thin — identity, ground truth,
> routing, guardrails. Procedure belongs in skills, not here.

## Ground truth

Files this agent must read before acting, and the rule that it never invents
facts absent from them.

## Routing

| The user wants | Load skill |
|---|---|
| … | `skill-name` |

## Operating rules

1. Numbered, imperative, and specific enough to change behaviour.

## Output

Where deliverables land and in what format.
