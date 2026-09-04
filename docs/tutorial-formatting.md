# Plan: make the logging tutorial files scannable

Files: `ai/adk/logging/tutorial/*.md`. Consumed by GitHub only (checked: no
`docs/` site references them), so GitHub-flavored alerts and `<details>` are
safe. **Formatting only — no prose rewrites.**

## What makes them hard to scan

| Problem | Where | Fix |
|---|---|---|
| The four-beat rhythm (Why / Do this / You'll see / What it means) is flat bold text | every section | give each beat a consistent visual marker |
| ~35 asides are all identical `>` blockquotes regardless of urgency | 01b, 03, 07 mostly | type them as GitHub alerts (NOTE/TIP/WARNING/CAUTION/IMPORTANT) |
| Long console/YAML dumps bury the takeaway | the 15+ line blocks | collapse the longest behind `<details>` |
| Files open on a dense `## Part N: sentence` with no orientation | all | `#` title + one-line italic dek |

## The changes

### C1 — Type the blockquote asides as GitHub alerts (recommended, high value)

GitHub renders `> [!WARNING]` etc. as a colored, icon-tagged box. Same text,
now visually sorted by urgency.

**Before**
```markdown
> **The catch that decides where you use it.** `LoggingPlugin` writes with
> `print()` and ANSI color codes, **not** through the `logging` module. That is
> perfect in a terminal and wrong for a deployed service...
```

**After**
```markdown
> [!WARNING]
> **The catch that decides where you use it.** `LoggingPlugin` writes with
> `print()` and ANSI color codes, **not** through the `logging` module. That is
> perfect in a terminal and wrong for a deployed service...
```

Mapping: framing/by-the-way → `[!NOTE]`, a handy shortcut → `[!TIP]`, "this
will bite you" → `[!WARNING]`, data-loss / security → `[!CAUTION]`, must-know
before you run → `[!IMPORTANT]`. The "Two traps" list in 06 becomes two
`[!WARNING]` boxes.

### C2 — Mark the four-beat rhythm (recommended)

Keep the labels; give each beat one consistent glyph so the eye finds the
rhythm down the left margin. The "Why you are here" opener becomes a NOTE
(it is framing, not action).

**Before**
```markdown
**Why you are here.** The log level is the first and bluntest dial...

**Do this.**
​```bash
.venv/bin/python examples/01_log_levels.py info
​```

**What it means.** Those five lines are the agent loop, in order:
```

**After**
```markdown
> [!NOTE]
> **Why you're here** — the log level is the first and bluntest dial...

**▶ Do this**
​```bash
.venv/bin/python examples/01_log_levels.py info
​```

**💡 What it means** — those five lines are the agent loop, in order:
```

Glyphs: `▶ Do this`, `💡 What it means`, plain **You'll see** lead-in kept as
is (the code block under it is self-evidently the output). This is the one
taste call — see the "Decisions" note on emoji.

### C3 — Collapse only the longest output blocks (recommended, selective)

**Before** — a 16-line dump sits inline between "Do this" and "What it means".

**After**
```markdown
<details>
<summary>Output — full agentic-loop narration (16 lines)</summary>

​```console
[logging_plugin] 🚀 USER MESSAGE RECEIVED
...
​```
</details>
```

Rule: collapse a block only if it is >12 lines **and** the point is made in the
prose around it (the `LoggingPlugin` narration, the YAML capture, the DEBUG
dump). Short 3-6 line blocks stay inline — collapsing those would just add
clicks.

### C4 — Per-file title + dek (recommended, cheap)

**Before**
```markdown
## Part 1: the log level, and what each one shows you
```

**After**
```markdown
# Part 1 · The log level

*What `DEBUG`, `INFO`, `WARNING`, and `ERROR` each reveal — on a script,
`adk web`, and `adk api_server`.*
```

The full original sentence survives as the dek, so nothing is lost; the H1 is
a clean tab/anchor and the nav footer already carries the short title.

## Recommendation

Do **C1 + C3 + C4** everywhere; do **C2** with the glyphs but hold the emoji
choice for review. C1 is the biggest single win. Skip 09 (`how-to-choose`) —
it is already all tables and scans fine; it only needs C4.

## Rollout

1. [x] Pilot on `01a` + `03`, push, review rendered on GitHub
2. [x] Adjust from review: What it means → TIP callout; Do this → 👉 (dropped ▶)
3. [x] Apply the agreed system to `01b, 02, 04–08`
4. [x] `09`: title + dek only
   -> verified each file: word sequence identical to the split commit after
   reversing the title styling and stripping alert tags (prose untouched);
   one H1 per file; no stray `▶`/`💡`
5. [x] Change "What it means" callouts from TIP → IMPORTANT (23 swaps)
6. [x] Scannability pass: horizontal dividers, output labels, step numbering
   - `---` before every `##`/`###`/`####` heading (24 dividers)
   - `**You will see**` → `**Expected output** —` (17 renames + 1 manual split)
   - Numbered step labels on 01a section 1.3's multi-terminal flow

## Decisions (confirmed)

- **D1: the beat treatments (C2), revised after pilot review.**
  - **What it means** → a `> [!IMPORTANT]` callout (was `[!TIP]`, was an
    inline `💡` label). The interpretation is now a purple box that closes
    each section. Where it introduces a table, the table rides inside the
    callout; elaboration paragraphs after it stay as body.
  - **Do this** → inline bold label with the 👉 emoji (was `▶`; the play
    button is dropped for an action-oriented glyph).
  - Prose inside is left verbatim — markers only.
- **D2: `<details>` collapses the >12-line blocks only.** ✅ Short blocks stay
  inline.
- **D3: pilot both `01a` and `03`.** ✅ Short file + hardest file.
- **D4: alert-type palette.** NOTE = framing/why-you're-here; IMPORTANT =
  the takeaway ("What it means"); TIP = optional detours and handy shortcuts;
  WARNING = the gotcha that bites.
