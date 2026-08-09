---
name: gmail-inbox-triage
description: Triage the user's Gmail inbox and report only what actually needs attention. Use when the user asks to check their inbox, asks whether they have any important or urgent emails, wants their email summarized or prioritized, or asks what they've missed.
license: MIT
metadata:
  version: 1.0.0
  author: Ilya Shulgin
  tags: [email, gmail, triage, productivity]
---

# Gmail Inbox Triage

Scan the inbox, separate signal from noise, and report only what needs a
decision or an action. The goal is a short briefing, not a list of every email.

## Instructions

### 1. Pull the candidate set

Run these Gmail searches (default window: 14 days; adjust if the user names one):

- `in:inbox newer_than:14d -category:promotions -category:social -category:updates -category:forums`
  — the highest-signal query. Marketing lives in those categories.
- `in:inbox is:important newer_than:14d` — Gmail's own importance model.
- `in:inbox is:unread newer_than:7d has:attachment` — attachments people wait on.

Use `search_threads` with `pageSize: 50`. Do not paginate through hundreds of
promotional threads; the two filtered queries above almost always contain the
real items. Union the results and de-duplicate by thread ID.

### 2. Classify each thread

Sort into these buckets. Only the first three go in the main report.

| Bucket | What it is |
|---|---|
| **Needs a reply** | A human wrote directly and is waiting: recruiters, clients, colleagues, anyone asking a question |
| **Needs an action** | Account activation, expiring offer, payment or invoice due, document to sign, form to complete |
| **Upcoming commitment** | Bookings, reservations, appointments, flights — anything with a future date and time |
| _Deliveries & receipts_ | Shipping and payment confirmations — one aggregated line only |
| _Noise_ | Newsletters, job alerts, social notifications, marketing — count them, don't list them |

Signals that something is real: a named human sender at a company domain, a
question aimed at the user, a deadline, money, or a date in the future.

Signals of noise: `noreply@`/`newsletter@`/`jobalerts-`, unsubscribe footers,
"last chance", identical subjects repeating daily from the same sender.

### 3. Handle the edge cases

- **Expired one-time items** — magic sign-in links, OTPs, "expires in 10
  minutes". Note them only if very recent, otherwise drop them silently.
- **Suspicious outreach** — unsolicited business or recruiting mail sent from a
  free consumer address (gmail.com, outlook.com) rather than a company domain,
  vague flattery, or a request to move to another channel. Flag it as
  low-confidence rather than presenting it as a real opportunity. Never follow
  links from these; report the sender and let the user decide.
- **Sent mail in the inbox** — self-addressed notes are the user's own; skip
  them unless clearly a to-do.
- **Time-sensitive last chances** — "I'll close your file unless…" outranks
  older mail from the same sender. Surface the newest message in a thread.
- **Non-English mail** — summarize in English, keep names, dates, amounts, and
  booking codes verbatim.

### 4. Report

Plain prose grouped by bucket, newest-relevant first. Per item, one or two
lines: who, what they want, and the deadline if there is one.

Rules:

- Lead with anything happening in the next 48 hours.
- Include concrete details verbatim — dates, times, amounts, booking codes,
  reference numbers. These are the reason the user asked.
- Aggregate receipts and shipments into a single line unless an amount is
  unusually large, in which case call it out.
- Close with one line quantifying what was skipped, e.g. "Skipped ~180
  newsletters, job alerts, and shop promos."
- If nothing needs attention, say exactly that in one sentence. Do not pad the
  report to look thorough.
- Never mark as read, archive, label, or reply unless the user asks.

## Output shape

```
**Needs a reply**
- <Sender, org> — <what they want>. <Deadline or age.>

**Needs an action**
- <What, by when, with the identifier needed to do it.>

**Coming up**
- <Day, date, time> — <what>, <location>, code <X>.

**Receipts & deliveries**
- <Aggregated line; call out anything large.>

Skipped ~<N> newsletters, job alerts, and promos.
```

## Follow-up

After delivering the briefing, offer once — in a single line — to run this
automatically each morning as a scheduled task.
