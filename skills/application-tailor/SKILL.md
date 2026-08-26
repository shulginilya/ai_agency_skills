---
name: application-tailor
description: Produces the application package for one specific job posting — a tailored CV, a cover letter, and the recruiter or referral message — positioning a senior software engineer for senior AI engineering roles. Use when the user says apply to this job, tailor my CV, write a cover letter, draft a message to this recruiter, or shares a posting they want to go after.
license: MIT
metadata:
  version: 0.1.0
  author: Ilya Shulgin
  tags: [job-search, cv, cover-letter]
---

# Application Tailor

One posting in, one application package out. Never generic.

## When to use

- "Apply to this one" / "tailor my CV for this"
- "Write the cover letter for <company>"
- "Draft a reply to this recruiter"

## When not to use

- Deciding *whether* to apply → `role-sourcing`
- "I don't have the skills for this yet" → `ai-engineer-gap-plan`

## Instructions

1. **Get the posting in full.** URL → fetch it. Pasted → use it. Never work from
   a title alone. Extract, verbatim: required skills, nice-to-haves, team
   description, seniority signals, and any stated stack.

2. **Read the ground truth.** `docs/job-search/candidate-profile.md`. Every line
   you write must trace to something there. If the posting demands something the
   profile does not contain, do not invent adjacent experience — either find the
   honest nearest neighbour or flag the gap in step 6.

3. **Map before writing.** Build a two-column table: each of the posting's top
   6–8 requirements → the specific evidence answering it, or `GAP`. Show this
   table. It is the plan; the documents are just its prose.

4. **Write the CV.** Start from the master CV and cut, reorder, and re-word — do
   not regenerate from scratch. Rules in [reference.md](reference.md). The AI and
   agentic work goes above the fold on every version. Bullets are
   `<action> <system> <constraint or scale> → <outcome>`; no adjectives.

5. **Write the cover letter.** Max 250 words, four moves: the specific reason
   this company, the strongest piece of matching evidence, the transition framed
   as accumulated leverage rather than a career restart, a plain closing. No
   "I am writing to express my interest". No enthusiasm inflation.

6. **Name the gaps out loud.** List what he cannot honestly claim for this role
   and what he would need to build to claim it next time. Two or three lines.
   This goes in chat, never in the documents.

7. **Record.** Add or move the role in `docs/job-search/pipeline.md` to stage
   `applied` (or `drafted` if he hasn't sent it), with the date and a link to the
   generated files.

## Output

Written to `docs/job-search/applications/<company>-<role-slug>/`:

- `cv.md` — tailored CV
- `cover-letter.md` — the letter
- `outreach.md` — recruiter reply and/or referral ask, if relevant
- `posting.md` — archived posting text, so a later rewrite has the source

Ask before converting to PDF or DOCX; use the `pdf` / `docx` skill when he wants
one and deliver the file.

## Guardrails

- Draft only. Gmail drafts, never sends. Never submit through the browser.
- No fabricated employers, dates, titles, metrics, model names, or tools.
- If the posting is below his stated floor or outside his markets, say so before
  spending the cycle.
