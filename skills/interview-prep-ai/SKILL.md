---
name: interview-prep-ai
description: Prepares and drills senior AI engineer interviews — recruiter screens, coding rounds, LLM and agent system design, evaluation deep-dives, and behavioural rounds — including company-specific prep and post-interview debriefs. Use when the user has an interview scheduled, asks for mock questions, wants system design practice, asks how to answer why the switch to AI, or wants to review how a round went.
license: MIT
metadata:
  version: 0.1.0
  author: Ilya Shulgin
  tags: [job-search, interview, system-design]
---

# Interview Prep (AI Engineer)

Drill the rounds he will actually face, using his own material.

## When to use

- "I have an interview at <company> on <date>"
- "Give me mock questions" / "run a system design drill"
- "How do I answer why you're moving into AI?"
- "Here's how the round went" → debrief

## When not to use

- Getting the interview → `role-sourcing`, `application-tailor`
- "I don't know the material yet" → `ai-engineer-gap-plan`

## Instructions

### Preparing for a named interview

1. **Pull the context.** Company and role from `docs/job-search/pipeline.md`; the
   archived posting under `docs/job-search/applications/`. Search for the
   company's published interview process and engineering blog. State plainly what
   you found and what you are guessing.
2. **Map the loop.** Which rounds, in what order, who runs each, what each is
   actually testing. See [reference.md](reference.md) for the standard shapes.
3. **Predict 8–12 questions** specific to this company and posting. For each,
   give the answer's skeleton — not a script. Scripts sound like scripts.
4. **Find the two hardest.** Usually the gap the posting exposes and the "why the
   switch" question. Work those until the answers are short and true.
5. **Write it to** `docs/job-search/applications/<company>-<role>/prep.md`.

### Drilling

Ask one question. Wait for his answer. Then: what worked, what a senior
interviewer would probe next, and the strongest version of the answer. Never
grade without showing the better answer. One question per exchange — a wall of
ten questions is reading, not practice.

### Debriefing

After a round: what was asked, what he answered, what to fix. Add the outcome to
the pipeline row. If a weakness shows up in two separate debriefs, it is a gap —
hand it to `ai-engineer-gap-plan`.

## Output

- `prep.md` per interview: loop map, predicted questions with skeletons, the two
  hard answers, three questions for him to ask them.
- In-chat drilling, one question at a time.
- Pipeline row updated with stage and outcome after every round.

## Guardrails

- Answers use only facts from `candidate-profile.md`. Rehearsing a fabrication is
  how it reaches a real interview.
- Do not soften feedback. A weak answer he thinks is strong costs him the offer.
- Never claim knowledge of a company's process without a source; say "typical for
  companies of this shape" when that's what it is.
