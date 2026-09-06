---
name: tutorial-style
description: House style for hands-on tutorials in this repo. Page anatomy, nav, Command and Expected output labels, callouts, deep dives, voice, verification. Use when writing or editing any tutorial page, part landing page, index, or README under a tutorial folder.
---

# Tutorial house style

This skill holds what every tutorial in the repo shares. A tutorial's own
`CLAUDE.md` holds what is specific to it: its governing model, asset paths,
deploy conventions. Templates with the nav and labels in place are in
`references/`.

## Teaching approach

- Build understanding from simple to sophisticated. Start with a simple,
  obvious application, then add variations and features in bite-sized chunks.
- Application first, with a simple explanation. Each page has the reader do
  something and explains just enough to follow.
- Deeper material comes after, in a Deep dives section on the page or on a
  reference page at the end.
- Keep code minimal. Code that is shown and run has only the elements the
  section teaches.
- Prefer real output. Capture it from actual runs where practical. Mark a block
  that is illustrative or not yet captured.

## Files

- `README.md`: what it is, the one idea, a link to the index, a files table,
  quick start, status.
- `TUTORIAL.md`: the index. Purpose in two paragraphs, the governing model with
  a diagram, a *Verified against* blockquote (versions, what ran), a
  `Part | What it covers` table, and a link to Setup.
- `tutorial/00-setup.md`: do-once environment, credentials, shell variables,
  the shared example.
- `tutorial/part-N/index.md`: landing page for a part with several pages. A
  single-page part is its own landing.
- `tutorial/part-N/N.M-slug.md`: one page per numbered subtask.
- A final reference page (optional): decision table, best practices,
  verification status, links.
- `examples/`, `deploy/`: runnable assets, linked by relative path.

Nav is hand-authored markdown. The pages are read on GitHub with no build step.

## Nav

Every page has the same nav block at the top and the bottom, one link per line
joined with `<br>`, in this order: `← Prev`, `→ Next`, `↑ Part N · Title`
(subtask pages only), `Tutorial index`. A `---` rule separates it from the
body. The first page has no Prev and the last has no Next. A part's last page
points Next at the next part's `index.md`.

To renumber a page: rename the file, then fix the nav on the page and both
neighbors, the part TOC, the index table, the README, and inline `N.M`
mentions. Grep for the number and the filename before you stop.

## Subtask page

Copy `references/subtask-page.md`. Top to bottom:

1. Nav, rule.
2. `# N.M · Title`, then `*Part N · Title*`.
3. `> [!NOTE]` with **Why you are here.** Two sentences at most: what this page
   does and what changed since the last one.
4. One to three sentences of context. The first **Command:** comes within a
   few sentences of the H1.
5. Steps. Each is `**Step N — Verb phrase.**` (or `**👉 Do this.**` on a
   one-action page), then `**Command:**`, a `bash` fence,
   `**Expected output**`, a `console` fence, and a `> [!IMPORTANT]` callout.
6. A tear-down step if the page created cloud resources.
7. One sentence handing off to the next page.
8. `## Deep dives`, if needed.
9. Rule, nav.

Rules for the slots:

- **Command:** precedes every runnable fence. Not for illustrative code, pipe
  fragments, browser input, or a second fence under one lead-in.
- **Expected output** precedes every result fence. A short note may follow it
  after a dash or colon.
- The callout after output is **What it means.** (observation, then
  consequence, two to four sentences). When the payload's keys are new to the
  reader, use **What you are looking at.** with a `field | value | what it is`
  table instead. Two findings on one output: **What it means, finding one: …**
- Show a prompt or request body once per page. Later steps refer to it by name.
- Explanation stays inline only when it sits beside the code or output it
  explains. Anything else the reader does not need for the step moves to a
  deep dive, leaving one sentence and `See [Title](#anchor).`
- Deep dive headings are `###`, phrased as the question they answer, in plain
  text so GitHub's anchor is predictable: lowercase, punctuation dropped,
  spaces to hyphens, underscores kept.
- Link an existing reference page before writing a new deep dive.
- Budget: 200 to 750 words including deep dives. Captured output does not
  count.

## Landing page

Copy `references/landing-page.md`: nav without the up-link, `# Part N · Title`,
an italic one-sentence subtitle, the **Why you are here** note, at most one
paragraph, then `## In this part` with a `Section | What it covers` table, then
nav. About 200 words.

## Reference page

Optional, at the end of a part or of the tutorial. A comparison table, a
diagram, when to use which, concrete cases. No steps. May run long.

## Markdown devices

- `> [!NOTE]` orients: Why you are here, or an artifact of how output was read.
  `> [!IMPORTANT]` interprets output. `> [!TIP]` is a side path, rare.
  `> [!WARNING]` is one sentence, rare; a longer warning becomes a deep dive.
- Callout labels are bold sentences ending in a period.
- One mermaid `flowchart` per mental model, followed by an italic one-line
  caption. Roughly one page in four has one.
- Tables for TOCs, comparisons, field-by-field reads, decisions, and
  verification status. Not for anything that reads fine as two sentences.
- Fences: `bash` for commands, `console` for captured output, `python` for
  illustrative code, plain for query strings.
- Illustrative code links the source file and shows only the relevant class or
  function.
- Bold for UI the reader clicks or reads, and for labels. Inline code for what
  the reader types, plus flags, paths, env vars, and logger names. Neither for
  emphasis.
- Bash in fences: one `--flag` per continuation line, one `export` per line.
  Leave short one-liners, env-prefix invocations, and `curl` short flags alone.

## Voice

- Second person, present tense, imperative steps.
- Name the reader's likely misconception, then correct it with the output.
- One lesson per page. Hand off by number: "Part 2 is about that."
- One term per concept, reused verbatim.
- Cite a source location as `path/file.py:line` when a behavior is not visible
  in the output.
- The global writing rules apply. Use `/nbj-write-clearly` to draft and audit.
  The `**Step N — …**` label is the only em dash.

## Verification

- The reference page keeps a short record: what ran, when, what it showed, and
  a **Not verified** table of what has not.
- A gotcha goes in a deep dive on the page that hits it.

## Working method

- Plan in `docs/<tutorial>-<topic>.md` with a stage checklist. Update it as
  stages land.
- Before a structural change, write the options with pros and cons and one
  recommendation.
- Rewrite two exemplar pages to a new pattern, review, then roll out.
- Set a rough word budget per page before a concision pass.
- Before committing: every `#anchor` resolves on its page, every relative link
  resolves, no captured block was dropped, no filler words.
- When a pattern stabilizes, record it in the same commit: here if shared, in
  the tutorial's `CLAUDE.md` if specific.
