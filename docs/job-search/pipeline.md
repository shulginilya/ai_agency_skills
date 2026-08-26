# Job Search Pipeline

Single source of truth for every role in flight. The `job-hunter` agent updates
this in the same run it touches a role — an unrecorded application does not exist.

**Stages:** `sourced` → `drafted` → `applied` → `screen` → `interviewing` →
`offer` | `rejected` | `dropped`

## Active

| Date | Company | Title | Location | Score | Stage | Next action | Notes |
|---|---|---|---|---|---|---|---|
| _(empty — run `role-sourcing` to populate)_ | | | | | | | |

## Closed

| Date | Company | Title | Stage | Outcome / reason |
|---|---|---|---|---|
| _(empty)_ | | | | |

## Rejection reasons log

One line per rejection, with the reason if known. `ai-engineer-gap-plan` reads
this to find the pattern — three rejections for the same missing thing is a gap,
not bad luck.

- _(empty)_
