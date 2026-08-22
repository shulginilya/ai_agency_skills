# Application Tailor Reference

## CV rules for the SWE → AI engineer pivot

**Order of sections.** Summary → AI & Agentic Systems → Experience → Core
Engineering → Education. The AI section exists so a 20-second skim finds the
pivot before it finds the frontend history.

**The summary.** Three lines, no more. Line 1: seniority and years and the
systems he owns. Line 2: the AI systems work, concrete — SDK, agents, retrieval,
evaluation, whatever the profile actually supports. Line 3: the market/terms
signal (Berlin, remote, notice period) only if it helps.

**Bullets.** `<action> <system> <constraint or scale> → <outcome>`.

- Bad: "Responsible for improving performance of the platform."
- Good: "Cut LCP from 4.1s to 1.6s across the SSR catalogue by moving rendering
  to ISR and trimming the hydration payload."

Verbs that carry weight: designed, shipped, migrated, cut, owned, instrumented,
scaled, decomposed. Verbs that do not: helped, participated, was responsible for,
worked on.

**Keyword matching.** Mirror the posting's own vocabulary where it is honest —
ATS filters are literal. If they say "RAG", do not write "retrieval pipeline".
If they say "LLMOps" and he has evaluation and observability work, say
"evaluation and observability for LLM systems (LLMOps)". Never mirror a keyword
he cannot defend in an interview.

**Length.** Two pages. A senior with a decade of work who submits three pages is
telling the reader he cannot prioritise.

**What to cut per version.** Anything not answering this posting: unrelated
stacks, old roles compressed to one line each, certifications nobody asked for,
the skills-cloud of every library ever touched.

## Framing the transition

The pivot is a re-weighting, not a restart. Three framings that land, in
descending order of strength:

1. **"I build the systems around the model."** Agent orchestration, tool design,
   evaluation harnesses, retrieval, cost and latency budgets, deployment — this
   is engineering work, and it is what most AI engineer reqs actually pay for.
2. **"I've already shipped this."** Any concrete agentic project beats any
   statement of intent. Lead with the artefact.
3. **"The hard part of production AI is production."** Distributed systems,
   observability, rollback, incident response — the things he has done for years
   are the things AI teams most often lack.

Never: "I'm looking to break into AI", "transitioning career", "passionate about
the potential of AI", "eager to learn". They read as a discount request.

## Cover letter skeleton

```
<Company>, <role>.

[1 sentence: the specific thing about this company/product/problem — not its
size, not its mission statement. Something only someone who read it would say.]

[2–3 sentences: the single strongest piece of evidence, told as a system with a
constraint and an outcome. Same fact as the CV, more context.]

[2 sentences: what he'd bring that the posting implies they need but didn't ask
for — usually the production/scale side of AI systems.]

[1 sentence: availability and a plain close.]
```

Under 250 words. If it needs more, the evidence is too weak, not too short.

## Recruiter reply

Four lines: yes/no on interest, the one-line positioning, the two questions that
decide it (comp band, and the thing that would disqualify the role), a time
window. Ask about comp early — it saves both sides three calls.
