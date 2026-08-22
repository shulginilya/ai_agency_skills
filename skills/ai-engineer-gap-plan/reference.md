# Gap Plan Reference

## What "senior AI engineer" reqs actually ask for

Grouped by how often they appear in product-AI (not research) postings. Verify
against the live pipeline each cycle — this is a starting prior, not the answer.

**Near-universal**

- LLM application design: prompting as engineering, structured output, tool/
  function calling, context management.
- Retrieval: chunking strategy, embeddings, vector stores, hybrid search,
  reranking, and knowing when RAG is the wrong answer.
- Agentic systems: multi-step loops, tool design, state, failure and retry,
  human-in-the-loop checkpoints.
- Evaluation: offline eval sets, LLM-as-judge and its failure modes, regression
  suites, tracking quality across prompt/model changes.
- Python fluency at production quality.
- Cloud deployment and cost/latency control.

**Common**

- Observability and tracing for non-deterministic systems.
- Fine-tuning or adapters — usually "understands when it's worth it" rather than
  "has trained models".
- Streaming, token budgets, caching, batching.
- Data pipelines feeding the model layer.
- Safety, prompt injection, PII handling.

**Occasional / often a research req in disguise**

- Training from scratch, distributed training, CUDA, publications, PhD.

## Where a senior SWE is already ahead

Name these explicitly in the plan — the gap table should not read as all deficit.

- Distributed systems, queues, idempotency, backpressure — agent orchestration is
  these problems with a stochastic worker.
- Observability, rollout, rollback, incident response — most AI teams are weak
  here and know it.
- API and platform design, clean architecture — tool interfaces are API design.
- Code review, mentoring, technical governance — what "senior" is actually buying.

## Artefacts that close gaps

Ordered by hiring signal per evening spent.

1. **A deployed agent with an evaluation harness.** Public repo, README with
   architecture, a real eval set with numbers, deployed somewhere reachable.
   Closes: agentic systems, evaluation, deployment. Single highest-value item.
2. **A retrieval system over a non-toy corpus,** with a written comparison of two
   chunking/reranking strategies and the measured difference. Closes: retrieval,
   evaluation, judgement.
3. **A written post-mortem or technical post** on something he actually built —
   the cost/latency trade-off, why an approach failed. Closes: credibility, and
   it is the thing recruiters read.
4. **An OSS contribution to an agent/LLM framework.** Small but real. Closes: the
   "has he touched this outside his own repo" question.

Anti-patterns: another chatbot demo, a notebook with no deployment, a course
certificate, a repo with no README, a "framework comparison" with no measurements.

## Sizing

An evening is 2–3 focused hours. A weekend is one evening's worth of focus plus
overhead. Anything estimated over 20 evenings is not an artefact, it is a career
change — split it.
