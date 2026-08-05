# Plan: multi-topic DIN site with a root-level menu

Status: **approved, in progress**. Decisions recorded in §6.

> **Framing that governs everything below.** These pages are not codelabs in the
> usual sense. Each step / left-nav card is a **standalone activity** on a single
> concept — steps do not build on each other and are not meant to be worked in
> order. The codelab shell is being used purely as a menu-and-navigation
> mechanism. Never write a step that references "the previous step" or carries
> state forward; each activity gets its own setup and stands alone.

## 1. Where things stand

`docs/` is published as GitHub Pages from `main` at
<https://roitraining.github.io/gcp-demos/> (confirmed via the Pages API:
`source: {branch: main, path: /docs}`).

```
docs/
├── index.html   1,413 lines — 30 BigQuery DIN steps, hand-maintained
├── custom.css     525 lines — restyle layered over codelab-elements.css
└── img/            4 PNGs
```

`index.html` is a single `<google-codelab>` element containing 30
`<google-codelab-step>` children. The claat/Google Doc generation flow was
abandoned (per the comment at the top of the file); the file is edited directly.
Codelab behavior (left-hand step nav, prev/next, progress) comes from the hosted
`codelab-elements.js` bundle. `custom.css` restyles it — step cards, cost notes,
asides, code blocks, nav buttons.

Today `/` **is** the BigQuery codelab. There is no landing page and no second
topic.

## 2. What we're building

```
docs/
├── index.html          NEW — landing page / topic menu
├── bigquery.html       today's index.html, moved
├── dataflow.html       NEW — Dataflow DINs
├── data-engineering.html  NEW — Misc. Data Engineering DINs
├── custom.css          gains a landing-page section
└── img/
```

Three decisions to confirm before building — see §6.

## 3. The landing page (`index.html`)

A plain standalone HTML page — **not** a `<google-codelab>`. Reasons:

- `codelab-elements.js` assumes step children; feeding it a menu fights the
  library for no benefit.
- The landing page needs no step nav, progress, or prev/next.
- It stays fast and trivially editable when a fourth topic appears.

It reuses `custom.css` (same `:root` tokens, fonts, radius, blue) so it reads as
the same product. Proposed structure:

```
┌──────────────────────────────────────────────────────┐
│  ROI Training · Do-It-Now Activities                 │  ← header, matches
│                                                      │    codelab top bar
├──────────────────────────────────────────────────────┤
│  tl;dr hands-on > demos > slides                     │  ← the framing that
│  <short intro: what a DIN is, ILT guidance>          │    currently opens
│  <cost legend: 🟢 / 💰 / 💸>                          │    the Overview step
│                                                      │
│  ┌────────────────┐ ┌────────────────┐ ┌───────────┐ │
│  │ BigQuery       │ │ Dataflow       │ │ Misc.     │ │  ← topic cards,
│  │ 30 activities  │ │ N activities   │ │ Data Eng. │ │    responsive grid
│  │ Queries, perf, │ │ Batch, stream, │ │ N activs. │ │
│  │ loading, …     │ │ …              │ │ …         │ │
│  └────────────────┘ └────────────────┘ └───────────┘ │
│                                                      │
│  <link back to the gcp-demos repo>                   │
└──────────────────────────────────────────────────────┘
```

Each card: topic name, one-line description, activity count, and a short list of
the themes covered. Whole card is the link.

## 4. Changes to the existing BigQuery codelab

1. **Move** `index.html` → `bigquery.html` via `git mv` (preserves history).
   External links to the bare Pages URL will now hit the menu rather than
   BigQuery directly — acceptable, and arguably the point.
2. **Trim the Overview step.** The cost legend, the "tl;dr", and the ILT note
   move to the landing page. What stays in Overview is BigQuery-specific: the
   sample-data section (`roi-bq-demos.bq_demo`, `bq_demo_small`, the
   schema-demo link). Alternative: keep Overview intact and accept the
   duplication — see §6.
3. **Restore the back link.** `custom.css:155` hides `#arrow-back` because it
   navigated to an unrelated org root. With a real menu at `/`, that button now
   has a correct destination. Options: un-hide it and set `?index=./` (which is
   what codelab-elements reads), or leave it hidden and put an explicit
   "← All activities" link in the header. The explicit link is more predictable
   than relying on the library's URL parsing.
4. No changes to any of the 30 step bodies.

## 5. The two new codelab files

**Scope for this pass: an Overview step only. No activity steps.** Both files
are structural copies of `bigquery.html` — same `<head>`, same script tags, same
`custom.css`, a `<google-codelab>` with its own `title`/`id`, and a single
Overview step that sets up the topic and states that activities are coming.

They exist so the landing page has real destinations and so the scaffolding is
settled before any activity writing starts. Activities get added later, one at a
time, each self-contained per the framing note at the top of this doc.

Source material already in the repo, for when activities are written:

**Dataflow** — `dataflow/simple_demos/beam_demo_1.py`, `beam_demo_2.py`;
`dataflow/dflow-bq-stream-python/` (a full Pub/Sub → Dataflow → BigQuery
streaming pipeline with `setup.sh`, `send_events.py`, `process_events.py`,
`schema_defs.py`, plus `pipeline.png`, `rows.png`, `send.png`).

**Misc. Data Engineering** — `composer/dags/` and `composer/dag_development/`;
`dataplex/profiling/` and `dataplex/lineage/`; `dataproc/` scaling and
autoscaling scripts; the `lakehouse/` Iceberg work; `dlp-demo/` and `security/`.

## 6. Decisions (settled)

1. **Overview duplication** — the cost legend, tl;dr, and ILT framing move to
   the landing page. Each codelab's Overview keeps only what is specific to its
   topic.
2. **New pages** — Overview step only for now; no activity steps.
3. **Build order** — restructure first (menu + BigQuery move), then the two new
   pages as scaffolding. Activity content follows separately.
4. **Extensibility** — the landing page must take additional topic cards without
   rework. The card grid is data-shaped and reflows on its own; adding a topic is
   one `<a class="din-card">` block and nothing else.

## 7. Work items

**This pass — done**
- [x] `git mv docs/index.html docs/bigquery.html`
- [x] New `docs/index.html` landing page
- [x] `.din-*` landing-page section in `custom.css`, reusing the existing tokens
- [x] "All activities" back-link on all three codelab pages, via `docs/din-nav.js`
- [x] Trimmed the BigQuery Overview per decision #1
- [x] `docs/dataflow.html` — Overview step only
- [x] `docs/data-engineering.html` — Overview step only
- [x] Verified all four pages in headless Chrome: rendering, back-link
      injection, Done target, 30 BigQuery steps intact, narrow-screen reflow

### Two things worth knowing about the nav

Both came out of reading the minified `codelab-elements.js`.

1. **`#arrow-back` cannot reach this menu.** Its href comes from a function that
   reads `?index=`, strips every character outside `[a-z0-9-]`, and resolves the
   result against `location.origin`. On a project Pages site it can only ever
   produce `/gcp-demos` or `/` — it cannot express a path ending in a slash. The
   `custom.css` rule hiding it stays, and `din-nav.js` injects an explicit link
   instead.
2. **`#done` had the same broken target**, since it is built from the same
   computed href. That went unnoticed before because Done only appears on the
   last of 30 steps; on the new single-step pages it shows immediately.
   `din-nav.js` repoints it at the menu.

`din-nav.js` injects rather than being authored inline because
codelab-elements builds `#codelab-title` itself and discards anything already
there.

### Adding a topic later

1. Copy `dataflow.html` to `<topic>.html`, change `<title>`, the `id`, the
   `title` attribute, and the Overview body.
2. Add one `<a class="din-card">` block to `.din-grid` in `index.html`.

Nothing else. The grid uses `auto-fit` with a `min()` track, so it adds a column
when the viewport allows and collapses to one when it doesn't — a fourth and
fifth card need no CSS changes. Keep `.din-card-count` current as pages fill in;
`.din-card-count-soon` is the neutral placeholder for a topic with no activities
yet.

**Later, separately**
- Write Dataflow activities; move `dataflow/dflow-bq-stream-python/*.png` into
  `docs/img/` as needed
- Write Data Engineering activities
- Update the activity counts on the landing-page cards as they fill in
- Cross-link from the repo `README.md`

## 8. Risks

- **Broken external links.** Anyone who bookmarked the Pages root lands on the
  menu instead of BigQuery. Low impact; one extra click.
- **`custom.css` scope.** Nearly every rule is prefixed `google-codelab …`, so
  it won't touch the landing page. New landing rules need their own namespace
  (`.din-*`) to avoid the reverse problem.
- **Content drift.** Three files repeat the same `<head>` and script block. A
  library upgrade means editing three places. Acceptable at this scale; a
  templating step would cost more than it saves.
