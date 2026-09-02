---
name: description-to-issue
description: Turn a plain-language description of work that has not been done yet — a feature request, a reported bug, a chore, or a research question — into a GitHub-format issue with a title, labels, a body, and acceptance criteria. Optionally takes the description inline (/description-to-issue "search returns stale results after an edit"). Use whenever the user says "make this a ticket", "turn this into a GitHub issue", "write an issue for this", "file this request", "we need a ticket for X", or pastes a Slack message, email, voice note or bug report and asks for an issue out of it. For work that has already been done — a diff, a branch, changes made earlier in the conversation — use change-to-issue instead.
argument-hint: "[the description]"
metadata:
  version: 0.1.0
  author: Ilya Shulgin
  tags: [github, issues, planning, writing]
---

# Description → issue

## The description you were given

Requested work: `$ARGUMENTS`

Everything typed after the command is the description, raw and unsplit — a
description is free prose, so it is read through `$ARGUMENTS` rather than a named
or indexed argument, which would hand you only its first word. When nothing was
typed, the backticks above are empty and the description is somewhere else: the
message that invoked you, a pasted Slack thread or email, or an attached file.
Find it before doing anything else, and if you genuinely cannot, ask what should
be ticketed rather than inventing something.

```
/description-to-issue search returns stale results after an edit
/description-to-issue "clients keep asking for a CSV export of the pipeline view"
/ai-agency-skills:description-to-issue                # description is in the conversation
```

## What you are producing

An issue for work **nobody has started**. Its reader is whoever picks it up in
three weeks with the requester unavailable. They must reach three conclusions
without asking anyone:

1. **What problem this solves** — in the requester's terms, not in terms of a patch.
2. **What "done" looks like** — checkable from the outside.
3. **What is still undecided** — the questions someone has to answer before or
   during the work.

That third one is the difference between a ticket and a wish. A description
arrives with holes in it; the ticket's job is to make the holes visible, not to
quietly fill them.

> **The trap.** A description is raw material for a *ticket*, not a brief for a
> *design*. You will be tempted to specify the schema, name the endpoint, pick
> the library. Don't. Every implementation detail you invent is a decision the
> assignee now has to argue with instead of make. Write the problem and the
> constraints; leave the solution to whoever takes it, unless the requester
> actually stated one.

## Step 1 — Separate what was said from what you inferred

Read the description twice and sort every fact into three piles:

| Pile | What it is | Where it goes in the ticket |
|---|---|---|
| **Stated** | The requester actually said it | The body, as fact |
| **Inferred** | You worked it out from context, the codebase, or common sense | The body, marked as an assumption |
| **Missing** | Needed for the ticket to be actionable, and absent | A question (step 3) or an open question in the body |

Nothing crosses from *inferred* to *stated* because it seems obvious. "Users
want a CSV export" does not state who can export, whether it is filtered, or
whether 200k rows are in scope — and each of those changes the work by a day.

If the description names a solution ("add a Redis cache"), keep it, but recover
the problem underneath it too. A ticket whose only content is someone's first
guess at a fix cannot be reviewed.

## Step 2 — Classify the ticket

The kind decides the shape. Pick one; if the description is really two things,
say so and offer to split rather than writing a ticket that cannot be closed.

| Kind | The tell | Shape |
|---|---|---|
| **Bug** | Something behaves wrongly *now* — "broken", "returns the wrong", "crashes", a report from a user | Repro → expected vs actual → environment → impact |
| **Feature / enhancement** | Something does not exist yet — "we need", "it would be great if", "clients keep asking" | Problem → proposal → acceptance criteria → out of scope |
| **Chore / tech debt** | Nothing visible changes for users — upgrades, cleanups, CI, renames | What → why now → definition of done |
| **Spike / research** | The answer is unknown — "can we", "figure out whether", "investigate" | Question → timebox → what a good outcome is |

Full templates for all four: [reference.md](reference.md).

## Step 3 — Fill the gaps before you draft, not after

Look before you ask. If the repo can answer it, answer it yourself — read the
code, check `.github/ISSUE_TEMPLATE/` for a template the project already uses,
run `gh label list` and `gh issue list --search …` to see house style and
whether this is a duplicate.

Then ask, in **one message, at most three questions**, and only for essentials —
things where a wrong guess makes the ticket wrong rather than merely thin:

- **Bug:** how to reproduce it; what was expected instead; where it happens
  (version, environment, who is affected).
- **Feature:** what problem it solves for the user; who it is for; what the
  smallest useful version is.
- **Chore:** why now; what breaks if it waits.
- **Spike:** what decision this unblocks; how much time it is worth.

Never ask about the implementation, priority, or milestone — that is the
assignee's and the triager's to decide.

If no answer comes back, or you are running unattended, **draft anyway**: put an
`## Assumptions` block directly under the title with one line per inferred fact,
worded so a wrong one is obvious at a glance, and tell the user in your message
that the ticket is unverified in those places.

## Step 4 — Write the body

Use the shape for the kind, drop any section that would be empty, and keep it
proportional: a one-line chore does not get five headings. Rules that hold for
every kind:

- **Problem first, always.** Even a chore has one.
- **Concrete over general.** "Export times out on the 40k-row account" beats
  "export is slow".
- **The requester's words for domain things.** If they say "pipeline view",
  that is what the ticket calls it — even if the class is named `DealBoard`.
- **Quote the source when it is short.** A two-line blockquote of the original
  Slack message or bug report tells a triager more than your paraphrase, and
  proves you did not embellish. Long threads get summarised, not pasted.
- **Never state a number you were not given.** No invented row counts, error
  rates, user counts, or deadlines.

### Acceptance criteria are the part that matters

They are what turns a description into something closeable. Write them as
unchecked task-list items, observable from outside the code:

```markdown
## Acceptance criteria

- [ ] A user with the `analyst` role can download the current pipeline view as CSV
- [ ] The export respects the filters applied on screen
- [ ] An export of 50k rows completes without a timeout, or fails with a clear message
```

Good: behaviour someone else can check. Bad: `- [ ] Add ExportService` — that is
a task, and it belongs to whoever writes the code.

Leave every box unchecked. Nothing here is done yet; that is the whole premise.

## Title and labels

Title: one line, specific enough to be found in a list of two hundred. Name the
thing and the outcome — "CSV export for the pipeline view", not "export
improvements"; for a bug, name the symptom — "Search returns stale results after
an edit". Match what `gh issue list` shows the repo already doing (conventional
prefixes or plain prose), and skip severity theatre — "URGENT" is a label, not a
title.

Labels: prefer the repo's real ones from `gh label list`. If the CLI is not
available or authenticated, suggest one or two obvious ones and say plainly that
they are guesses. Never invent a taxonomy the project does not use.

## GitHub-specific formatting

The body is GitHub Flavored Markdown and will be read in a web form:

- Task lists (`- [ ]`) render as tickable checkboxes and drive the progress bar.
- Fence every code block, log, and command with a language tag.
- Reference issues as `#123` (or `owner/repo#123` across repos) — bare numbers
  do not link. Do not write `Closes #123` in an issue; closing keywords only
  work from pull requests.
- Collapse anything long — a stack trace, a full log — in `<details><summary>`.
- Avoid raw HTML beyond `<details>`, and avoid heading levels above `##`; the
  title is the h1.

More, including `gh` recipes: [reference.md](reference.md).

## Handing it over

Write the body to a markdown file and deliver it — the user is going to paste it
into a web form — and put the **title** and **labels** in your message, on their
own lines, so both fields can be copied without scrolling into the file. Keep
the commentary to a couple of lines: the assumptions you made, the questions
that went unanswered, and whether you think this should be two tickets.

Offer to file it, do not file it silently:

```bash
gh issue create --title "…" --body-file issue.md --label bug --label triage
```

Show the draft first and wait for approval. A draft is editable; a filed issue
has already notified everyone watching the repo.

## Anti-patterns

- **The invented spec.** Endpoints, table columns and library choices nobody asked for.
- **The restated one-liner.** A title, the same sentence as the body, and no criteria.
- **Criteria that are tasks.** "Write tests", "refactor the module" — unobservable.
- **Silent gap-filling.** Guessing the browser, the volume, or the deadline and
  writing it as fact.
- **Two tickets in one.** "Fix the export *and* add scheduling" can never be closed.
- **Priority invention.** P0 because the requester used an exclamation mark.
