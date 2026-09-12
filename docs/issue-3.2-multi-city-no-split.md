# Issue: page 3.2 "Volume and shape" — the promised split does not happen

Status: **open, needs your decision.** Nothing changed in the tutorial for this
yet (the agent edit I started was reverted). This file explains what 3.2 was
supposed to teach, what the live run actually showed, and the options.

## What 3.2 is supposed to teach

3.2's lesson is **"repeated work shows up as two populations in one metric."**
The idea: most turns do a little work, some turns do a lot, and a histogram of
"work per turn" shows that as two clumps (two populations) rather than one
average. The operator question on the page is *"Is repeated work driving latency
and consumption?"*

The two metrics it reads are per-invocation counts ADK records once per turn:

- `gen_ai.invoke_agent.tool_calls` — how many tool calls that turn made
- `gen_ai.invoke_agent.inference_calls` — how many model calls that turn made

The `multi-city` scenario was designed to create the split: one turn in four asks
for three cities in a single prompt ("What's the weather in London, Tokyo, and
New York?"), the rest ask for one city. The page predicts:

- single-city turns → **1 tool call**, ~2 inference calls
- three-city turns → **3 tool calls**, more inference calls

So a bucket histogram of `tool_calls` per turn should show a spike at 1 (the
common turns) and a second, smaller spike at 3 (the three-city turns). That
second spike is "the two populations."

## What the live run actually showed

I ran `multi-city` against `adk web --otel_to_cloud` and read the distributions
back. Every turn — including the three-city ones — recorded **exactly 1 tool
call and 2 inference calls.** There is no second population.

The `tool_calls` bucket histogram (cumulative counts by upper bound `le`):

```
le=0  -> 0
le=1  -> 60      <- every turn is <= 1 tool call
le=2  -> 60
le=3  -> 60      <- nothing added between 1 and 3; no second spike
...
```

Every count lands at or below `le=1`, meaning no turn exceeded one tool call. The
`inference_calls` histogram is the same story: everything sits at 2, nothing
higher.

### Why it happens

The model (Gemini 3.7 Flash) reads "the weather in London, Tokyo, and New York"
and answers it with a **single** `get_weather` call, or answers all three from
one call's context, rather than calling the tool once per city. The demo tool
signature is `get_weather(city)` — one city per call — but nothing forces the
model to fan out, and it chooses not to. The model is being efficient; our
scenario just assumed it would not be.

So the page describes a behavior the model does not exhibit. The metric is
working correctly; the premise about how the agent behaves is wrong.

## Why this matters

If we shipped 3.2 as written, a reader following along would run `multi-city`,
read the `tool_calls` histogram, and see one population where the page promises
two. The page's whole point would visibly fail on their screen. Every console
block in this tutorial is supposed to be a real capture; this one cannot be,
because the thing it describes does not occur.

## The options

### Option A — Re-aim 3.2 at the token distribution (keep the scenario)

Keep `multi-city`, but change the lesson from "more calls" to "more tokens per
call." A three-city prompt is longer and its answer is longer, so those turns
cost more input and output tokens. The split would show up in the
`gen_ai.client.token.usage` histogram, not the `tool_calls` histogram.

- Pro: no agent change; the scenario name and prompt stay.
- Con: the token-cost story is what **3.4** ("Tokens and cost") already teaches,
  so 3.2 and 3.4 would overlap. And in a mixed run the token spread is muddied by
  other scenarios, so a clean capture needs an isolated window.
- Con: weaker lesson. "Longer prompt costs more tokens" is almost obvious; "some
  turns do 3× the work" is the more interesting operator signal.

### Option B — Change the scenario to one that really splits (e.g. slow-tool)

Point 3.2 at a scenario that does produce two populations. `slow-tool` mixes
instant `get_weather` turns with slow `get_forecast` turns, so a **latency**
histogram shows two clumps.

- Pro: two real populations, no agent change.
- Con: that is exactly what **3.1** ("Latency, three ways") already teaches with
  `slow-tool`. 3.2 would become a near-duplicate of 3.1.
- Con: it abandons the `tool_calls`/`inference_calls` metrics, which then get no
  page of their own.

### Option C — Make the agent fan out (my recommendation)

Add one sentence to the agent's instruction: each tool call handles one city, so
when a question names several cities, call the tool once per city. Then a
three-city turn really does make 3 tool calls, and the `tool_calls` histogram
splits exactly as 3.2 describes.

The change (reverted for now) was:

```python
# added to the instruction string:
" Each tool call handles exactly one city, so when a question names several"
" cities, call the tool once per city."
```

- Pro: keeps 3.2's lesson and its metrics (`tool_calls`, `inference_calls`)
  intact, distinct from 3.1 (latency) and 3.4 (tokens).
- Pro: arguably more realistic. A tool that takes one city is normally called
  once per city; the current one-call-for-three behavior is the odd case.
- Con: it changes agent behavior, so it touches every page that runs the agent.
  But it only adds a fan-out for multi-city prompts. Single-city turns
  (`baseline` and every other scenario) still make 1 tool call / 2 inference
  calls, so Parts 1–2 and the other Part 3 captures are unaffected. I would
  re-verify that after the change.
- Con: it is "teaching to the metric" — shaping the agent so the demo lands.
  That is a fair objection. The counter-argument: the scenario always intended
  multi-city to mean multi-call; the instruction just makes the agent honor the
  scenario's intent instead of relying on the model to guess it.

## What I need from you

Which option (A, B, or C), or something else. My recommendation is **C**: it is
the smallest change that keeps 3.2 teaching its own lesson, and it makes the demo
agent more representative rather than less. If you dislike shaping the agent for
the demo, **B** is the honest fallback but costs us a distinct 3.2 (it merges
into 3.1's territory).
