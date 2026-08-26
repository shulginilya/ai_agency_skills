# Interview Prep Reference

## The standard senior AI engineer loop

1. **Recruiter screen** (20–30 min) — motivation, comp, notice, location. Tests
   nothing technical; loses candidates who fumble "why AI" or anchor badly on comp.
2. **Hiring manager** (45 min) — the pivot story, one project deep-dive, scope and
   seniority. This is the round the transition is won or lost in.
3. **Coding** (60 min) — usually practical, not LeetCode-hard: build a small
   retrieval or tool-calling piece, parse and validate model output, handle
   failure. Python is the expected language even for TS-heavy candidates.
4. **AI system design** (60 min) — the differentiating round. See below.
5. **Behavioural / values** (45 min) — mentoring, conflict, incidents, ambiguity.
   His actual seniority advantage; do not under-prepare it because it feels easy.
6. Occasionally: take-home, or a paper/architecture discussion.

## AI system design: what they're testing

Not model internals. They want to see whether he can build a system around an
unreliable component.

The frame that works, in order:

1. **Requirements and the quality bar.** What does "good" mean, and how will we
   know? Anyone who starts drawing boxes before defining the eval is failing.
2. **Data and retrieval.** Sources, freshness, chunking, index choice, hybrid
   search, reranking. Justify each with a trade-off, not a preference.
3. **The model layer.** Routing, prompts as versioned artefacts, structured
   output, tool definitions, fallbacks between models.
4. **Orchestration.** Steps, state, retries, timeouts, idempotency, human
   checkpoints. This is where his distributed-systems background should show.
5. **Evaluation.** Offline set, online signals, LLM-as-judge and its bias,
   regression gating on prompt/model change.
6. **Cost and latency.** Token budget per request, caching, streaming, batching,
   what breaks at 100× traffic.
7. **Safety and failure.** Prompt injection, PII, what happens when the model is
   confidently wrong, how a bad deploy gets rolled back.

Common question shapes: design a support agent over a documentation corpus;
design an evaluation pipeline for a feature already in production; a RAG system
returns plausible but wrong answers — debug it; cut inference cost 70% without
losing quality; design a multi-agent workflow with human approval.

**Strong-signal moves:** defining the eval before the architecture; naming a
cost/latency budget unprompted; choosing *not* to use an agent where a single
call suffices; describing the rollback.

**Weak-signal moves:** naming vendors instead of trade-offs; assuming RAG is the
answer to every grounding problem; no mention of evaluation until asked; treating
the model as deterministic.

## "Why are you moving into AI?"

Bad: "I'm passionate about AI and want to break into the field."

Good, in his own words: the systems he already builds are the hard part of
production AI — the orchestration, the failure handling, the observability — and
he has been building agentic systems on the Claude Agent SDK because that is where
the interesting distributed-systems problems moved. Not a restart; a re-weighting.

Rule: the answer is about the work, never about the industry's excitement, and it
ends with a shipped artefact.

## Behavioural

Four stories, each reusable across many questions, each 90 seconds in
STAR-without-saying-STAR form: an incident he owned end to end; a technical
disagreement he lost or resolved; someone he mentored who levelled up; a project
he changed direction on with evidence. Pull the raw material from
`candidate-profile.md` — invented stories collapse under a follow-up.

## Questions for him to ask

Signal seniority: How do you evaluate quality today, and what breaks first? What
does the path from prototype to production look like here? What decision about
the AI stack would you make differently now? Where does this team sit relative to
the product org?
