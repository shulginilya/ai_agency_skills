---
name: ai-engineer-gap-plan
description: Diagnoses the distance between a senior software engineer's current evidence and what senior AI engineer postings actually require, then produces a ranked, time-boxed plan of what to learn and what to ship. Use when the user asks what should I learn, am I ready for these roles, what's missing from my profile, what portfolio project should I build, or why they keep getting rejected.
license: MIT
metadata:
  version: 0.1.0
  author: Ilya Shulgin
  tags: [job-search, skills, learning-plan]
---

# AI Engineer Gap Plan

Turn "what am I missing?" into a short list of things to build, ordered by how
much each one moves the hiring needle.

## When to use

- "What should I learn next?" / "Am I ready to apply?"
- "Why am I not getting callbacks?"
- "What should I build for my portfolio?"
- Quarterly re-check against the pipeline's rejection reasons.

## When not to use

- Applying to a specific role → `application-tailor`
- Interview practice → `interview-prep-ai`

## Instructions

1. **Establish current evidence.** Read `docs/job-search/candidate-profile.md`.
   Evidence means shipped artefacts, not exposure. "Read the docs" is not
   evidence; "built and deployed an agent that does X" is.

2. **Establish demand — from real postings, not from priors.** Pull the last
   10–20 roles from `docs/job-search/pipeline.md`, or run a fresh scan. Count how
   often each requirement appears. The demand list is empirical; do not
   substitute a generic AI-engineer curriculum for it.

3. **Diff.** Produce the gap table:

   | Requirement | Frequency in postings | His evidence | Gap | Cost to close |
   |---|---|---|---|---|

   Cost is in evenings, not months, and must be a real number.

4. **Rank by leverage.** Leverage = frequency × (how much it unblocks) ÷ cost.
   Say the ranking out loud. The top three are the plan; everything below is
   noise until they're done.

5. **Convert to shippable artefacts.** Every gap closes with a thing that exists
   in public, not a course completed. See [reference.md](reference.md) for the
   competency map and project patterns. Each artefact gets: what it is, the one
   CV bullet it will earn, and a deadline.

6. **Time-box.** A 6–8 week plan, two or three artefacts, explicit weekly slots.
   More than three parallel threads is a plan that will not survive contact with
   a full-time job.

7. **Close the loop.** Write the plan to `docs/job-search/gap-plan.md`,
   overwriting the previous one but keeping a dated `## History` line summarising
   what the last cycle actually shipped.

## Output

`docs/job-search/gap-plan.md`:

```
# Gap Plan — <date>
## Demand (from N postings)
## Gap table
## The three things
   1. <artefact> — <CV bullet it earns> — <deadline>
## Not doing yet (and why)
## History
```

## Guardrails

- Be blunt about weak evidence. Comfortable ratings cost him interviews.
- Never recommend a certification as the primary answer to a gap.
- Never list more than three active artefacts.
- If the honest answer is "nothing is missing, the applications are the problem",
  say that and hand off to `application-tailor`.
