# Logging tutorial: concision pass

Folder: `ai/adk/logging/tutorial/` (36 pages). Status: **all pages revised (2026-09-05), uncommitted.**

| Measure | Before | After |
|---|---|---|
| Total words | 24,396 | 20,478 |
| Prose words (outside code fences) | 21,501 | 16,923 (21% cut) |
| Code/output words | 3,214 | 3,301 (no captured block removed; the growth is merged blocks and the 5.7 snippet) |
| Pages with a Deep dives section | 0 | 9 (1.2, 1.4, 1.6, 3.1, 3.3, 4.2, 5.1, 5.2, 5.4) |
| Broken anchors / relative links | | 0 / 0 |

Pages still above their word target (1.6, 3.1, 5.2) are dominated by verbatim captured blocks and deep-dive source citations; the prose ahead of the first command is now a few sentences on every page.

## Goals

1. Cut words aggressively without losing facts, captured output, or caveats. Apply `/nbj-write-clearly` and the global writing rules.
2. Get explanation out of the way of action. A page should reach its first **Command:** within a few sentences. Long explanations move to a **Deep dives** section at the end of the page, and the inline text keeps one sentence plus a link.

Explanations that sit next to the code block they explain (a **What it means** callout after an output block, a snippet with a paragraph) stay inline. They are the payoff of the run, not a delay before it.

## The pattern

| Element | Rule |
|---|---|
| **Why you are here** note | At most two sentences: what this page does and what changes from the previous one. No history, no source citations. |
| Pre-action explanation | If it is longer than about three sentences and the reader does not need it to run the step, move it to a deep dive. Leave one sentence and a link. |
| Inline pointer | `See [Title](#anchor).` at the end of the sentence it supports. Plain heading text (no backticks) so GitHub's auto-anchor is predictable. |
| **Deep dives** section | `## Deep dives` after the last step and before the bottom nav. One `### Title` per topic, phrased as the question it answers (`Why .env cannot set these`). Keep the source citations and captured evidence here. |
| Parenthetical asides | Either one sentence inline or a deep dive. No multi-paragraph `> [!WARNING]` blocks in the flow of steps. |
| **What it means** callouts | Keep. Trim to the observation and its consequence. Tables stay when they name fields. |
| Repeated prompts | Show the prompt block once per page. Later steps say "ask the London question in a new session." |
| Cross-page references | Prefer a link to an existing reference page (5.6 for the content knobs, 5.7 for backends) over a new deep dive. |

Anchor rule: GitHub lowercases the heading, drops punctuation, keeps underscores, and turns spaces into hyphens. `### Why metrics need OTEL_RESOURCE_ATTRIBUTES` → `#why-metrics-need-otel_resource_attributes`.

## Page inventory

Target is a rough word budget after the pass, including deep dives. "Move" lists what leaves the flow of steps.

| Page | Words | Target | Move to deep dives / cut |
|---|---|---|---|
| `TUTORIAL.md` | 700 | 550 | Trim intro. Keep diagram and contents table. |
| `00-setup.md` | 382 | 320 | Trim "Meet the agent." |
| `part-1/index.md` | 274 | 200 | Two-sentence note. |
| `1.1` | 953 | 700 | Trim the three after-output paragraphs into the callouts. |
| `1.2` | 311 | 200 | Three paragraphs before the command → one sentence + deep dive "What the flag really does." |
| `1.3` | 546 | 450 | Trim. Keep the `adk run` tip. |
| `1.4` | 803 | 600 | Job-vs-service paragraph → one sentence. "stderr means ERROR" evidence → deep dive. |
| `1.5` | 666 | 500 | Server description → two sentences. |
| `1.6` | 1399 | **~900 (done)** | Native/BYOC mechanics, BYOC traps, Part 4 carry-over → deep dives. |
| `part-2/index.md` | 516 | 400 | Explanation before the filter snippet → shorter; it is code-adjacent, so it stays inline. |
| `part-3/index.md` | 273 | 200 | Two-sentence note. |
| `3.1` | 1147 | 750 | "How the one line works," the fourteen-hook list, the `_log` and `before_tool_callback` source → deep dive "How plugin hooks fire." Keep the sequence diagram. |
| `3.2` | 600 | 450 | Trim both findings. |
| `3.3` | 623 | 450 | The comparison table and the two source snippets → deep dive "How it differs from LoggingPlugin in source." |
| `3.4` | 486 | 350 | Trim. |
| `3.5` | 471 | 400 | Reference page; trim only. |
| `part-4/index.md` | 250 | 180 | Two-sentence note. |
| `4.1` | 312 | 280 | Fine. |
| `4.2` | 926 | 750 | Code-adjacent, mostly stays. Tighten "Two Cloud Run facts" and the ContextVar paragraph. |
| `4.3` | 538 | 420 | Trim callouts. |
| `4.4` | 652 | 500 | Decision page; tighten. |
| `part-5/index.md` | 399 | 250 | Two-sentence note. |
| `5.0` | 412 | 350 | Fine. |
| `5.1` | 1116 | 800 | "The endpoint behind the tab" and "Where those spans have been living" → deep dives. |
| `5.2` | 3270 | **~1900 (done)** | Roles/packages, metrics 400 diagnosis, `.env` timing, `[otel-gcp]` → deep dives. |
| `5.3` | 484 | 380 | Trim the env-var table's Why column. |
| `5.4` | 660 | 500 | `.env` / `GOOGLE_CLOUD_LOCATION` note → deep dive. |
| `5.5` | 850 | 650 | `.env` note → one sentence; second-backend snippet → link to 5.7. |
| `5.6`, `5.7`, `5.8` | 1452 | 1200 | Reference pages; tighten. |
| `part-6/index.md` | 412 | 250 | Prose before the TOC → two sentences; the reuse paragraph → 6.4. |
| `6.1`–`6.4` | 1301 | 1000 | 6.3 states its lesson twice; merge. |
| `how-to-choose.md` | 1912 | 1100 | Verification status is a 1,000-word run log. Turn it into a table: section, what ran, date, open items. |

## Stages

- [x] Stage 0: plan, pattern, and exemplars (1.6, 5.2). Convention added to `ai/adk/logging/CLAUDE.md`.
- [x] Stage 1: Part 1 and Part 2 (`00-setup`, `part-1/*`, `part-2/index`).
- [x] Stage 2: Parts 3 and 4.
- [x] Stage 3: Part 5 (remaining pages) and Part 6.
- [x] Stage 4: `TUTORIAL.md`, `how-to-choose.md` (verification status is now two tables). `README.md` left as is; it was already short.
- [x] Stage 5: anchor check (every `](#…)` resolves to a heading on its page), relative link check, dropped-block check against HEAD, filler-word scan. All clean. Remaining em dashes are the `**Step N — …**` labels the tutorial's CLAUDE.md mandates.
- [ ] Review with Jeff, then commit.

Verify per stage: word counts against the table, every `#anchor` resolves to a heading on the same page, no captured output block changed.
