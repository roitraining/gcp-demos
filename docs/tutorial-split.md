# Plan: split the ADK logging tutorial into smaller files

Target: `ai/adk/logging/TUTORIAL.md` (1862 lines). Goal: no single file is
overwhelming to read, without changing what the tutorial says.

## Where the lines are

| Section | Lines | Notes |
|---|---|---|
| Intro + Setup | 75 | |
| Part 1: the log level | 625 | 1.1-1.3 local (226), 1.4-1.7 cloud (399) |
| Part 2: uvicorn access logs | 60 | |
| Part 3: plugins | 475 | 3.1/3.3/3.5 local, 3.2/3.4 Cloud Run |
| Part 4: production logging | 172 | |
| Part 5: custom server | 65 | |
| Part 6: Cloud Run | 178 | |
| Part 7: OTel | 74 | |
| Part 8: Agent Runtime | 41 | |
| How to choose / Beyond / Verification / References | 97 | |

Cross-reference inventory (checked with grep):

- ~60 prose references by number ("Part 6 does that", "1.4's finding").
- 1 real anchor link: line 1560 -> `#13-the-same-dial-on-adk-api_server`.
- Inbound: `README.md` (3 links), `docs/adk-logging-*.md` (path mentions only).

## Approach A: one file per Part, numbering unchanged

Mechanical cut at each `## Part N` heading. Prose is untouched.

```
ai/adk/logging/
  TUTORIAL.md              # becomes the index: intro, four-streams idea, TOC, Setup
  tutorial/
    01-log-levels.md       # Part 1  (625; see D2 for an optional 1.3/1.4 cut)
    02-access-logs.md      # Part 2
    03-plugins.md          # Part 3
    04-production.md       # Part 4
    05-custom-server.md    # Part 5
    06-cloud-run.md        # Part 6
    07-otel.md             # Part 7
    08-agent-runtime.md    # Part 8
    09-how-to-choose.md    # How to choose, Beyond logging, Verification, References
```

Each file gets a one-line `prev | index | next` footer. Section numbers stay
exactly as they are, so "see 1.4" still means the same thing in any file.

## Approach B: regroup by where the code runs

Reorganize into reading tracks that match the README's "cloud steps are
optional" framing:

```
ai/adk/logging/tutorial/
  local.md          # Setup, 1.1-1.3, Part 2, 3.1, 3.3, 3.5, Part 4, Part 5   (~700)
  cloud-run.md      # 1.4, 1.5, 3.2, 3.4, Part 6                              (~600)
  agent-runtime.md  # 1.6, 1.7, Part 8                                        (~250)
  otel.md           # Part 7                                                  (~75)
  reference.md      # How to choose, Beyond, Verification, References         (~100)
```

A reader who never deploys reads one file and is done. But every section is
renumbered, and the "same script, next place" pairs (1.1 -> 1.4, 3.1 -> 3.2)
now live in different files.

## Comparison

| | A: per Part | B: per runtime |
|---|---|---|
| Largest file | 625 (Part 1), or 399 with D2 | ~700 (local.md) |
| Prose edits needed | none | renumber every section; rewrite ~60 cross-refs |
| Narrative | intact: each Part still reads "local, then cloud" | broken: 1.4 opens with "the Part 1 script" that is now in another file |
| Reviewability | diff is pure moves; verifiable by heading count | real rewrite; needs a full read-through to check |
| Fits existing `docs/` plans | yes, they cite Part numbers | no, they'd go stale |
| Reader who skips cloud | skips the tail of each Part | reads one file |
| Risk of introducing errors | near zero | moderate |
| Effort | ~1 hour | ~half a day plus re-verification |

## Recommendation: A

The tutorial's whole structure is "do X locally, then watch what happens to X
on Cloud Run, then on Agent Runtime". That is a per-Part story, and B cuts
across it. A gives smaller files today with zero content risk; if reading
tracks turn out to matter, they can be added later as a short "reading paths"
table in the index without moving anything.

## Decisions (review before executing)

- **D1: `TUTORIAL.md` stays as the index.** README and the docs/ plans link to
  it by name; keeping it means nothing external breaks. Setup stays in the
  index because every Part assumes it.
- **D2: cut Part 1 at the 1.3/1.4 seam?** Yes, recommended. Gives
  `01a-log-levels-local.md` (226) and `01b-log-levels-cloud.md` (399), and the
  seam is already the boundary the earlier expansion plan used. Then the
  largest file is Part 3 at 475.
- **D3: leave prose cross-refs as plain numbers.** "See 1.4" reads fine
  without a link. Convert only the one real anchor at line 1560 to a
  cross-file link. Links can be added later if the numbers alone annoy you.
- **D4: no content edits.** Not even typo fixes. If something is wrong, it goes
  in a separate commit so the split diff stays reviewable as pure moves.

## Steps

1. [x] Create `tutorial/` and cut `TUTORIAL.md` at each `## ` heading per the
       layout above (with D2 applied)
       -> verified: heading text list old vs. new is identical in order; only
       adds are `Contents` (index) and the `Part 1, continued` continuation
       heading; reconstructed part bodies are byte-identical to the original
       (only per-file boundary blank lines differ)
2. [x] Rewrite `TUTORIAL.md` as index: keep intro + Setup, add TOC table
       linking each file with a one-line summary
       -> verified: intro and Setup kept verbatim; all 10 files linked
3. [x] Add `prev | index | next` footer to each file
       -> verified: every relative link in every file resolves
4. [x] Convert the line-1560 anchor to a cross-file link
       -> verified: now `01a-log-levels-local.md#13-...` in 06-cloud-run.md
5. [x] Update `README.md` file table: `TUTORIAL.md` row -> "The tutorial index"
       plus one row for `tutorial/`
6. [x] No prose lost (verified by reconstruction diff, step 1)

## Deviations from the plan (both mechanical, no prose changed)

- **Asset links gained `../`.** The part files live in `tutorial/`, so
  `](examples/...)`, `](deploy/...)`, `](demo_agent/...)`, and
  `](agent_runtime_byoc/...)` became `](../...)`. Required for the links to
  resolve; not a content edit.
- **One added heading in 01b.** Because Part 1 is split mid-part (D2), the cloud
  file opens with `## Part 1, continued: the same run in the cloud` plus a
  one-line pointer back to 01a, so it does not start on an orphan `### 1.4`.
