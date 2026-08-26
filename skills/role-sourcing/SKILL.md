---
name: role-sourcing
description: Finds, screens, and scores senior AI engineer openings across LinkedIn, company career pages, job boards, and inbound recruiter email, then records the keepers in the job-search pipeline. Use when the user asks to find jobs, run a job scan, check for new roles, evaluate whether a posting is worth applying to, or asks "is this job a fit".
license: MIT
metadata:
  version: 0.1.0
  author: Ilya Shulgin
  tags: [job-search, sourcing, linkedin]
---

# Role Sourcing

Turn the open market into a short ranked list of roles worth his evening.

## When to use

- "Find me AI engineer roles" / "run the weekly scan"
- "Is this posting worth applying to?" (paste or URL)
- "Anything new from recruiters?"

## When not to use

- Writing the actual application → `application-tailor`
- "What should I learn first?" → `ai-engineer-gap-plan`

## Instructions

1. **Read the target definition.** `docs/job-search/candidate-profile.md` §Targets
   holds titles, markets, company profile, and the compensation floor. If it is
   empty, ask for the missing constraint before searching.

2. **Pick channels.** Default to web search plus Gmail — both work unattended.
   Add Chrome/LinkedIn only when he is present and asks for LinkedIn coverage;
   add an Apify actor only for a broad unattended sweep, and say it costs credits
   before calling one. See [reference.md](reference.md) for queries and actors.

3. **Search wide, then cut.** Aim for 30–60 raw hits, then filter hard:
   - Drop anything posted >30 days ago with no reposting signal.
   - Drop staffing-agency reposts of the same req; keep the direct source.
   - Drop roles requiring a PhD *and* publications — that is a research
     scientist req wearing an engineer's title.
   - Keep roles named "AI Engineer", "ML Engineer (product)", "LLM Engineer",
     "Applied AI", "Forward Deployed Engineer", "Agent Engineer", and senior
     backend/platform roles whose body is 50%+ AI systems work.

4. **Score each survivor 0–100** with the rubric in [reference.md](reference.md).
   Show the four component scores, not just the total. Be honest about the fit
   score — an inflated 85 wastes a week of his life.

5. **Report the top 5–8.** For each: company, title, location/remote terms, comp
   if stated, total score with components, the one sentence that makes it
   interesting, and the single biggest reason he might be rejected.

6. **Record.** Append every role scoring ≥65 to `docs/job-search/pipeline.md` at
   stage `sourced`, newest first. Never duplicate a company+title already there —
   update the existing row instead.

## Output

A ranked table in chat plus an updated `docs/job-search/pipeline.md`. Structure:

```
| Score | Company | Title | Location | Comp | Why | Risk |
```

Then one paragraph: what the batch says about the market this week (which
skills keep recurring, which of his gaps keep costing him hits). That paragraph
is the part he actually acts on — do not skip it.

## Guardrails

- Read-only in the browser. Never click Apply, Connect, or Message.
- Never invent comp figures. "Not stated" is an acceptable cell value.
- If a channel fails twice, say so and continue with the others rather than
  retrying in a loop.
