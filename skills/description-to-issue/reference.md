# description-to-issue — reference

Templates and mechanics that would bloat `SKILL.md`. Load when you need the full
shape for a kind, the question bank, or the `gh` commands.

## The four templates

Copy the one that matches the kind, drop sections that would be empty, and keep
every box unchecked — none of this work has been done.

### Bug

```markdown
## Summary
One or two sentences: what goes wrong, for whom, and how often.

> Original report, quoted if it was short and specific.

## Steps to reproduce
1. …
2. …
3. …

## Expected
What should have happened.

## Actual
What happens instead. Paste the error verbatim in a fenced block; collapse
anything longer than ~20 lines in <details>.

## Environment
Version / commit, browser or client, OS, account or data shape if it matters.

## Impact
Who is blocked, how many, and whether a workaround exists.

## Open questions
- [ ] Anything the reporter did not say and you could not determine.
```

If reproduction steps are missing and unobtainable, say so explicitly under
Steps to reproduce — "not reproduced; reported by <source>" — rather than
inventing a plausible sequence. A wrong repro sends the assignee down a wrong
path and costs more than an empty section.

### Feature / enhancement

```markdown
## Problem
Two to five sentences in the user's terms. What they cannot do today, and why
the obvious workaround is not one. No solution here.

## Who this is for
The role or segment asking, and roughly how often it comes up.

## Proposal
Only what was actually requested or is genuinely settled. If the shape is open,
say so and list the options instead of picking one.

## Acceptance criteria
- [ ] Observable behaviour
- [ ] Observable behaviour
- [ ] Observable behaviour

## Out of scope
- The adjacent thing everyone will assume is included. Name it.

## Open questions
- [ ] Decisions that must be made before or during the work.
```

### Chore / tech debt

Usually short. Headings are optional below three paragraphs.

```markdown
## What
The change, in one or two sentences.

## Why now
The cost of waiting: a deprecation date, a blocked upgrade, a recurring
annoyance with a number attached.

## Definition of done
- [ ] …
- [ ] CI green, no behaviour change intended
```

### Spike / research

```markdown
## Question
The single question this answers. One sentence, answerable yes/no or with a
recommendation.

## Why we need to know
The decision or ticket this unblocks.

## Timebox
e.g. "1 day — stop and report whatever is known."

## A good outcome
- [ ] A written recommendation with the tradeoffs
- [ ] A throwaway prototype, or a note saying one was not needed

## Not doing
Shipping anything production-facing from this ticket.
```

A spike's deliverable is a decision, never a feature. If someone expects working
code out of it, it is a feature ticket that has been mislabelled.

## Question bank

Ask at most three, in one message, only where a wrong guess makes the ticket
wrong. These are the ones that most often change the shape of the work:

**Bug**
- Can you reproduce it reliably, or was it a one-off?
- What did you expect to see instead?
- Which environment / version / account did it happen on?
- Is anyone blocked, or is there a workaround?

**Feature**
- What are you trying to accomplish that you cannot today?
- Who needs this — a specific role, a specific customer, everyone?
- What is the smallest version that would already help?
- Anything explicitly *not* wanted, so nobody over-builds it?

**Chore**
- What forces the timing — a deadline, an upgrade, a recurring cost?
- Is any behaviour allowed to change, or must this be invisible?

**Spike**
- What decision does the answer unblock?
- How much time is it worth before we just pick something?

Do not ask: priority, milestone, assignee, estimate, or how to implement it.

## Checking the repo before drafting

```bash
ls .github/ISSUE_TEMPLATE/            # a template the project already expects
gh label list                         # the real label taxonomy
gh issue list --limit 20              # house style for titles
gh issue list --search "csv export"   # is this a duplicate?
```

If `.github/ISSUE_TEMPLATE/` holds a form (`*.yml`) rather than a markdown
template, its fields are mandatory in the web UI — mirror those field names as
headings so the user can paste section by section, and mention that the form
exists.

If `gh` is missing or unauthenticated, do not guess at what it would have said.
Draft from the description, and mark labels as suggestions.

## Filing it

```bash
gh issue create \
  --title "CSV export for the pipeline view" \
  --body-file issue.md \
  --label enhancement --label needs-triage
```

Useful additions once the user has approved the draft:

| Flag | Effect |
|---|---|
| `--repo owner/name` | File somewhere other than the current repo |
| `--assignee @me` | Assign on creation |
| `--milestone "Q4"` | Must already exist |
| `--web` | Open the prefilled form in a browser instead of filing |

`--web` is the safest handoff when anything in the draft is still an assumption:
the user lands in the form with the body filled in and can fix it before
submitting.

## Other trackers

The shapes above are tracker-agnostic; only the mechanics differ.

- **Jira** — headings become bold text or an h2; `- [ ]` task lists do not
  render, so acceptance criteria go in a bulleted list or the description's
  checklist field. Titles are "summaries" and are usually a single sentence.
- **Linear** — Markdown renders close to GitHub's, including task lists.
  Labels are richer; keep the body identical.
- **Plain email or Slack** — drop the headings below three, keep problem,
  criteria, and open questions.

Do not restructure the content per tracker. The problem-before-proposal order and
the observable criteria are the value; the syntax is not.
