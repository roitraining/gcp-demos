# Proposal: split the ADK logging tutorial into one page per subtask

## The change you asked for

Today the tutorial is **8 part-files** (`tutorial/NN-topic.md`) plus the
`TUTORIAL.md` index. Each part-file holds several numbered subtasks — Part 5 alone
runs 5.0–5.8 across ~1,100 lines. You want **one page per top-level subtask**
(1.1, 1.2, 1.3, 1.4, …) with **navigation at the top and bottom** of every page.

That takes us from 8 content files to roughly **30 subtask pages** plus the index:

| Part | Subtasks | Pages |
|---|---|---|
| 1. Log levels | 1.1–1.6 | 6 |
| 2. Access logs | (single) | 1 |
| 3. Plugins | 3.1–3.5 | 5 |
| 4. Structured logging | 4.1–4.4 | 4 |
| 5. OpenTelemetry | 5.0–5.8 | 9 |
| 6. Agent Runtime | 6.1–6.4 | 4 |
| How to choose & reference | (single) | 1 |
| **Total** | | **30 + index** |

More pages means the relationship between **page → parent part → whole tutorial**
has to be visible *on every page*, or a reader who lands mid-tutorial is lost.
That's the real design problem, and it's what the three presentations below solve
differently. Each addresses:

- **Page titling** — what the `#` heading on a subtask page says.
- **Relationship display** — how a page shows its parent part and its place in the whole.
- **Nav mechanics** — what the top and bottom nav bars contain.

All three keep the existing conventions from `CLAUDE.md` (real-run output, code-block
labels, the four-streams framing) untouched — this is purely structure and navigation.

---

## A common cost, up front

Whichever we pick, splitting multiplies the **cross-reference maintenance** that
`CLAUDE.md` already warns about. Right now a renumber touches ~8 nav footers; after
the split it touches ~30 top bars **and** ~30 bottom bars, plus every inline
`5.4`-style mention. Two of the three options below address this directly by
generating nav instead of hand-authoring it. Flag for the recommendation.

---

## Presentation A — Flat sequence, breadcrumb-titled

Every subtask is a peer in one long chain. The part is just a label in a breadcrumb;
there are no "part landing" pages.

**Page titling** — the `#` heading carries the full path so the page is
self-identifying out of context:

```
# 5.4 · The same flag on Cloud Run

*Part 5 · OpenTelemetry — stream 4 to Google Cloud*
```

**Relationship display** — a breadcrumb line under the title:
`Tutorial › Part 5 · OpenTelemetry › 5.4`. The part name is text, not a link
(there's no part page to link to).

**Nav mechanics** — identical top and bottom bars, strictly linear:

```
← 5.3 The api_server flag   ·   Tutorial index   ·   5.5 Your own server →
```

Prev/Next cross part boundaries transparently: 5.6's Next is 6.1.

**Pros**
- Simplest mental model: one straight line of 30 pages, like a slideshow.
- "Next" always works; a reader can hold the Enter key from 1.1 to the end.
- Fewest files — no part landing pages to write or maintain.

**Cons**
- The part grouping is decorative only. A reader wanting "just the OTel part" has
  no single page to land on or link to.
- The index (`TUTORIAL.md`) becomes the *only* place the structure is visible, and
  it's now a 30-row table.
- Loses the current part-intros (e.g. Part 5's "why you are here" note) unless they
  get grafted onto the first subtask of each part.

---

## Presentation B — Part landing pages + subtask pages (two-tier)

Each part keeps a short **landing page** (its intro + a mini-TOC of its subtasks);
each subtask is its own page under it. Two levels of navigation.

**Page titling** — subtask pages title short, because the parent is one click away
and shown in the nav:

```
# The same flag on Cloud Run
```

The `5.4` and part name live in the nav bars and breadcrumb, not the heading.

**Relationship display** — a breadcrumb that's fully linked, plus an "in this part"
rail:
`Tutorial › Part 5 · OpenTelemetry › 5.4 Cloud Run`, where **Part 5** links to the
Part 5 landing page. The landing page lists 5.0–5.8 with one-line descriptions —
the current part-intro content becomes that page.

**Nav mechanics** — top and bottom bars carry three anchors plus an up-link:

```
↑ Part 5 · OpenTelemetry
← 5.3 api_server   ·   Tutorial index   ·   5.5 Your own server →
```

**Pros**
- Mirrors how the tutorial already thinks (parts are real, with real intros).
- A part is linkable and landable — "read the OTel part" has an address.
- Preserves the existing part-intro prose as the landing page verbatim; least
  rewriting of content.
- Scales: the index stays a 6-row part table, not a 30-row subtask table.

**Cons**
- Most files (30 subtasks **+ 6 landings + index = 37**) and the most nav wiring.
- Two-tier nav is more to keep correct by hand; renumber cost is highest unless
  automated.
- A "Next" that stops at a part boundary and sends you to the next landing page
  (rather than straight to the next subtask) can feel like a speed bump; sending
  it straight to the next subtask undercuts the landing pages. Have to pick one.

---

## Presentation C — Flat sequence with a persistent part sidebar-in-nav

Like A (no landing pages, one linear chain), but the relationship is carried by a
**contextual "in this part" strip** in the nav rather than a breadcrumb, so the
whole shape of the current part is visible on every page without a separate landing
page.

**Page titling** — number-led, medium length; enough to stand alone in search
results or a shared link:

```
# 5.4 The same flag on Cloud Run
```

No separate subtitle line; the nav strip supplies context.

**Relationship display** — the top nav shows the current part's subtasks inline,
with the current one marked:

```
Part 5 · OpenTelemetry:  5.0 · 5.1 · 5.2 · 5.3 · [5.4] · 5.5 · 5.6 · 5.7 · 5.8
```

Each number links to that subtask; `[5.4]` is the current page, unlinked. This is a
per-part table of contents rendered on every page — the reader always sees where
they are within the part and can jump within it.

**Nav mechanics** — the part strip (above) sits at top and bottom; a thin linear
bar underneath it handles cross-part Prev/Next and the index link:

```
Part 5 · OpenTelemetry:  5.0 · 5.1 · 5.2 · 5.3 · [5.4] · 5.5 · 5.6 · 5.7 · 5.8
← 5.3   ·   Tutorial index   ·   5.5 →
```

**Pros**
- Best in-context orientation: you see the whole part *and* the linear thread on
  every page, with no extra landing pages to maintain.
- Jump-within-part without a round-trip to an index or landing page.
- Fewer files than B (30 + index), same as A.

**Cons**
- The part strip is repeated markup on every page — **must** be generated, not
  hand-maintained, or a renumber is a nightmare (30 strips to edit).
- Markdown renders the strip as a plain run of links; it only looks like a proper
  "you are here" rail with CSS (which the codelab/`custom.css` pipeline can supply,
  but raw-GitHub-markdown viewers won't).
- Slightly heavier nav visually — two rows top and bottom.

---

## Comparison

| | A · Flat breadcrumb | B · Landing + subtasks | C · Flat + part strip |
|---|---|---|---|
| Files | 30 + index | **37** | 30 + index |
| Part is landable/linkable | No | **Yes** | No |
| Orientation on a mid-tutorial landing | Weak | Good | **Best** |
| Jump within a part | Via index only | Via landing page | **Inline, 1 click** |
| Preserves current part-intros | Grafted onto 1st subtask | **Verbatim as landing** | Grafted onto 1st subtask |
| Hand-maintainable nav | **Yes** | Only if generated | Only if generated |
| Renumber blast radius | Medium | High | High (unless generated) |

---

## Recommendation: **B**, the two-tier landing + subtask model

It's the only option that keeps the parts *real* — landable, linkable, and carrying
their existing intros — which matches how this tutorial is already written and how
`CLAUDE.md` already frames it (per-part files with a `# Part N` heading and a subtitle).
The current part-intros (Part 5's "why you are here," the four-streams framing on the
index) are some of the strongest content in the tutorial; B preserves them as landing
pages with **zero rewriting**, where A and C force us to bolt them onto whichever
subtask happens to be first.

Two decisions to lock before building B:

1. **Boundary behavior of "Next":** at the last subtask of a part, Next → the *next
   part's landing page* (recommended — respects the part as a unit and shows its intro
   before its first subtask), not straight to the next subtask.
2. **Nav generation:** author nav from a single manifest (an ordered list of
   part/subtask entries) and generate the top+bottom bars, rather than hand-writing
   ~74 bars. This kills the renumber-blast-radius con outright and is worth doing
   before, not after, the split. If we're staying in hand-authored markdown with no
   build step, **A** becomes the pragmatic pick instead — it has the least nav to
   keep correct by hand.

So: **B if we add a tiny nav-generation step; A if we stay fully hand-authored.**
C is the one I'd skip — it buys the best orientation but pays B's maintenance cost
*without* B's landable parts.

## Open questions for you

- Is there a **build step** already in the pipeline (the codelab/`custom.css` HTML
  export), or is the markdown the final artifact? This decides B-vs-A directly.
- Should the **Setup** section (currently on the index) become its own page in the
  sequence — effectively "0. Setup" — so Next flows Setup → 1.1? Or stay on the index?
- Keep the split-Part-1 (`01a`/`01b`) distinction, or does one-page-per-subtask
  make it moot (1.1–1.3 local, 1.4–1.6 cloud, all just peer pages under Part 1)?
