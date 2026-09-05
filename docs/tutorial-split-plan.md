# Plan: split the ADK logging tutorial into one page per subtask (Presentation B)

Status legend: `[ ]` todo · `[x]` done

## Decisions (locked)

- **Model:** Presentation B — part landing pages + one page per subtask.
- **Next at part boundary:** last subtask's Next → the *next part's landing page*.
- **Setup:** its own `00-setup.md` page in the sequence (index → Setup → Part 1 landing → 1.1).
- **Part 1 a/b:** dropped. 1.1–1.6 are peer subtask pages under one Part 1 landing.
- **No build step:** markdown is the final artifact (read on GitHub). Nav is
  **hand-authored** — there is no generator. Accepted cost: a renumber touches the
  top+bottom bar of each affected page.

## Open decision baked into this plan (change if you disagree)

- **Single-subtask parts get no separate landing.** Part 2 (Access logs) and the
  final "How to choose & reference" are each one section. Giving them a landing
  page *and* an identical subtask page is pure redundancy. Plan treats each as a
  **single page that is its own landing** — it carries the part heading, the intro,
  and the content together. Parts 1, 3, 4, 5, 6 (multi-subtask) get a landing + N
  subtask pages.

## Directory layout

New tree under `ai/adk/logging/tutorial/`, one directory per part so 30-odd files
stay legible. `TUTORIAL.md` stays the index at the tutorial root.

```
ai/adk/logging/
├── TUTORIAL.md                     # index: four-streams intro + parts table (Setup moves out)
└── tutorial/
    ├── 00-setup.md                 # NEW — Setup, sequenced (was in TUTORIAL.md)
    ├── part-1/
    │   ├── index.md                # Part 1 landing (intro + mini-TOC 1.1–1.6)
    │   ├── 1.1-test-harness.md
    │   ├── 1.2-adk-web.md
    │   ├── 1.3-adk-api-server.md
    │   ├── 1.4-cloud-run.md
    │   ├── 1.5-http-server.md
    │   └── 1.6-agent-runtime.md
    ├── part-2/
    │   └── index.md                # Access logs — single page = its own landing
    ├── part-3/
    │   ├── index.md                # Part 3 landing (3.1–3.5)
    │   ├── 3.1-loggingplugin.md
    │   ├── 3.2-loggingplugin-cloud-run.md
    │   ├── 3.3-debugloggingplugin.md
    │   ├── 3.4-debugloggingplugin-cloud-run.md
    │   └── 3.5-plugin-or-level.md
    ├── part-4/
    │   ├── index.md                # Part 4 landing (4.1–4.4)
    │   ├── 4.1-structured-plugin.md
    │   ├── 4.2-custom-server.md
    │   ├── 4.3-server-cloud-run.md
    │   └── 4.4-callback-or-plugin.md
    ├── part-5/
    │   ├── index.md                # Part 5 landing (5.0–5.8) — keeps the "why you are here"
    │   ├── 5.0-what-stream-4-is.md
    │   ├── 5.1-adk-web-already-tracing.md
    │   ├── 5.2-otel-to-cloud.md
    │   ├── 5.3-api-server.md
    │   ├── 5.4-cloud-run.md
    │   ├── 5.5-your-own-server.md
    │   ├── 5.6-content-knobs.md
    │   ├── 5.7-other-backends.md
    │   └── 5.8-relates-to-parts-1-4.md
    ├── part-6/
    │   ├── index.md                # Part 6 landing (6.1–6.4)
    │   ├── 6.1-one-switch.md
    │   ├── 6.2-deploy-flag.md
    │   ├── 6.3-deploy-env.md
    │   └── 6.4-platform-changes.md
    └── how-to-choose.md            # final page = its own landing (decision table, refs)
```

The current 8 files (`01a`, `01b`, `02`…`07`) are **deleted** after their content
is distributed.

## Per-page anatomy (every subtask page)

```
[top nav]

# 5.4 · The same flag on Cloud Run          ← number-led H1, full title

*Part 5 · OpenTelemetry*                     ← part subtitle line (orientation)

<body: this subtask's content, verbatim from the current file — code blocks,
callouts, mermaid, all unchanged>

---
[bottom nav]   ← identical to top nav
```

**Nav bar** (top and bottom, identical): a **stacked block of bare links, one per
line**, in order Next / Prev / Part / Top. The link text is the destination page's
own title; a direction arrow prefixes it. A `---` (hr) sits **below the top block
only**.

```
[→ 5.5 · Your own server: install the exporters yourself](5.5-your-own-server.md)
[← 5.3 · The same flag on `adk api_server`](5.3-api-server.md)
[↑ Part 5 · OpenTelemetry](index.md)
[Tutorial index](../../TUTORIAL.md)

---
```

- **Next** (`→`) = next page in the linear thread; **Prev** (`←`) = previous page.
  At a part boundary Next points to the *next part's* `index.md`, and a landing's
  Prev points to the *previous part's last subtask* (reciprocal).
- **Part** (`↑`) = the parent part landing (`index.md`). Only on subtask pages —
  landing pages and single-subtask pages omit it (they *are* the part top).
- **Top** = `Tutorial index` (`../../TUTORIAL.md` from a subtask page, `../TUTORIAL.md`
  from a page at `tutorial/` root).
- First page (Setup) omits Prev; last page (how-to-choose) omits Next.

**Landing page** (`part-N/index.md`) anatomy:

```
[top nav: ← Prev part / index / Next: first subtask →]

# Part 5 · OpenTelemetry
*subtitle*
> [!NOTE] Why you are here…            ← preserved verbatim from current part file

<the part's short intro prose, verbatim>

## In this part
| | |
|---|---|
| [5.0 · What stream 4 is](5.0-what-stream-4-is.md) | one-line desc |
| … | … |

---
[bottom nav]
```

## Global nav order (the linear thread)

```
TUTORIAL.md → 00-setup → part-1/index → 1.1 → 1.2 → 1.3 → 1.4 → 1.5 → 1.6
→ part-2/index → part-3/index → 3.1 → 3.2 → 3.3 → 3.4 → 3.5
→ part-4/index → 4.1 → 4.2 → 4.3 → 4.4
→ part-5/index → 5.0 → 5.1 → 5.2 → 5.3 → 5.4 → 5.5 → 5.6 → 5.7 → 5.8
→ part-6/index → 6.1 → 6.2 → 6.3 → 6.4
→ how-to-choose (end)
```

## Execution steps

- [x] 1. **Confirm this plan** with Jeff (structure, filenames, single-subtask-part handling).
- [x] 2. Create `part-N/` directories.
- [x] 3. `00-setup.md`: move Setup out of `TUTORIAL.md`; add nav.
- [x] 4. For each multi-subtask part: write `index.md` (part intro + mini-TOC) and
       split each `### N.N` section into its own file, body verbatim, add top+bottom nav.
- [x] 5. Part 2 and how-to-choose: single pages carrying part heading + content + nav.
- [x] 6. Rewrite `TUTORIAL.md` parts table to link part landings (not old files);
       drop the Setup section (now a page).
- [x] 7. Update inline cross-references everywhere: fixed `../` → `../../` asset links
       (14), stale `Part 7`/`07-how-to-choose.md` refs (2), and `00-setup.md`'s
       `demo_agent/agent.py` link.
- [x] 8. Update `README.md` and `ai/adk/logging/CLAUDE.md` "Tutorial structure"
       section to describe the new layout and nav convention.
- [x] 9. Delete the old `01a`…`07` files.
- [x] 10. Link-check: all links resolve; every page has top+bottom nav; the 36-page
        linear thread is unbroken and Prev/Next reciprocal (fixed 3 landing-page
        Prev links that skipped the previous part's last subtask).

## Verification

- `grep -rL 'Tutorial index' tutorial/**/*.md` → every content page has nav (empty result).
- No link points at a deleted `NN-topic.md` name: `grep -rnE '0[1-7][a-b]?-[a-z]' tutorial/ TUTORIAL.md README.md` → empty.
- Walk Next from `00-setup` to `how-to-choose` by hand; confirm 30+ hops land.
- Content is byte-preserved: the concatenation of split bodies equals the original
  section bodies (spot-check the big ones: 5.2, 4.2, 3.3).
