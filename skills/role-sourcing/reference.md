# Role Sourcing Reference

## Scoring rubric (0–100)

Four components, weighted. Show each.

| Component | Weight | 0 | Full marks |
|---|---|---|---|
| **Fit** | 40 | Requires ML research, PhD, or 5+ yrs production ML | Wants a strong senior engineer who can own LLM/agent systems end to end |
| **Leverage** | 25 | Nothing he already has transfers | Explicitly wants TypeScript/Node, Python, AWS, distributed systems, or platform ownership alongside AI |
| **Terms** | 20 | Below floor, wrong market, on-site in another country | At or above floor, Berlin or EU/global remote, contract shape he accepts |
| **Trajectory** | 15 | Dead-end wrapper work, no AI team | Real AI product, senior scope, people who will make him better |

Bands: **≥80** apply this week · **65–79** apply if the batch is thin ·
**<65** log only, do not spend a tailoring cycle on it.

## Search queries

Web / Firecrawl — vary the title, keep the market clause:

- `"senior AI engineer" (Berlin OR "remote Germany") -recruiter`
- `"LLM engineer" OR "agent engineer" hiring senior remote europe`
- `"applied AI engineer" site:jobs.ashbyhq.com`
- `"AI engineer" site:boards.greenhouse.io senior`
- `"forward deployed engineer" senior remote`
- Company-direct: `<company> careers "AI engineer"` for anything on his target list.

Board hosts worth querying by `site:` — greenhouse.io, lever.co, ashbyhq.com,
workable.com, join.com, personio.de, smartrecruiters.com. Berlin-specific:
berlinstartupjobs.com, germantechjobs.de.

## LinkedIn via Chrome

Only with him present. Sequence: `tabs_context_mcp` → `tabs_create_mcp` →
`navigate` to the search URL → `get_page_text` / `read_page` → paginate.

Useful URL shape:

```
https://www.linkedin.com/jobs/search/?keywords=AI%20Engineer&location=Berlin&f_TPR=r604800&f_E=4
```

`f_TPR=r604800` = posted in the last week. `f_E=4` = senior. `f_WT=2` = remote.

Never interact beyond reading and scrolling.

## Apify

Call `search-actors` for LinkedIn/Indeed job scrapers rather than hardcoding an
actor id — they change. Check the input schema with `fetch-actor-details` before
`call-actor`, then read results with `get-dataset-items`. Say the credit cost
before running.

## Gmail

Recruiter sweep:

- `newer_than:14d (recruiter OR "opportunity" OR "role" OR hiring) -label:job-search-processed`
- `newer_than:30d from:(linkedin.com) "InMail"`

Label handled threads so the next scan skips them. Draft replies; never send.
