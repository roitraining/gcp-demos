---
name: tutorial-style
description: Write or edit tutorial pages, part landing pages, indexes, and READMEs under tutorial folders in this repo. Defines the shared teaching approach, page structure, navigation, formatting, and verification.
---

# Tutorial house style

Use this skill for conventions shared across tutorials. Keep tutorial-specific
guidance in that tutorial's `CLAUDE.md`, including its governing model, asset
paths, and deployment conventions. Templates in `references/` provide the
required navigation and labels.

## Teaching approach

- Teach one lesson per page. Start with a simple application, then add
  variations and features in small increments.
- Have the reader do something early. Explain enough to complete the task;
  put deeper material in the page's Deep dives section or a final reference
  page.
- Keep shown and runnable code limited to what the section teaches.
- Capture output from actual runs where practical. Label illustrative output
  and output that has not yet been captured.
- Name likely misconceptions and use the output to correct them.

## Files

- `README.md`: introduce the tutorial and its central idea. Include an index
  link, files table, quick start, and status.
- `TUTORIAL.md`: give the purpose in two paragraphs, explain the governing
  model with a diagram, and include a *Verified against* blockquote naming
  versions and what ran. Follow with a `Part | What it covers` table and
  a Setup link.
- `tutorial/00-setup.md`: cover one-time environment setup, credentials,
  shell variables, and the shared example.
- `tutorial/part-N/index.md`: introduce a part with several pages.
  A single-page part serves as its own landing page.
- `tutorial/part-N/N.M-slug.md`: cover one numbered subtask.
- Optional final reference page: collect decisions, best practices,
  verification status, and links.
- `examples/` and `deploy/`: hold runnable assets. Link to them with relative
  paths.

Pages render directly on GitHub. Navigation is hand-authored Markdown;
there is no build step.

## Navigation

Repeat the same navigation block at the top and bottom of every page.
Separate it from the body with `---`. Put one link per line, joined with
`<br>`, in this order:

1. `← Prev`
2. `→ Next`
3. `↑ Part N · Title` (subtask pages only)
4. `Tutorial index`

Omit Prev on the first page and Next on the last. From a part's last page,
link Next to the next part's `index.md`.

When renumbering a page, rename the file and update:

- its navigation and both neighbors' navigation;
- the part TOC, tutorial index table, and README;
- inline `N.M` references.

Search for the old number and filename to catch remaining references.

## Subtask pages

Copy [references/subtask-page.md](references/subtask-page.md).
Use this order:

1. Navigation and rule.
2. `# N.M · Title`, followed by `*Part N · Title*`.
3. A `> [!NOTE]` callout labeled **Why you are here.** In at most two
   sentences, explain what the page does and what changed since the
   previous page.
4. One to three sentences of context. Reach the first **Command:** within
   a few sentences of the H1.
5. Steps using the structure below.
6. A teardown step if the page created cloud resources.
7. One sentence introducing the next page.
8. `## Deep dives`, if needed.
9. Rule and navigation.

Keep the page between 200 and 750 words, including deep dives.
Captured output does not count.

### Steps and output

Each step contains:

1. `**Step N — Verb phrase.**`, or `**👉 Do this.**` for a one-action page.
2. `**Command:**` and a `bash` fence.
3. `**Expected output**` and a `console` fence.
4. A `> [!IMPORTANT]` callout interpreting the output.

Apply these label rules:

- **Command:** precedes every runnable fence, except a second fence under
  the same lead-in. Omit it for illustrative code, pipe fragments, and
  browser input.
- **Expected output** precedes every result fence. An optional short note
  follows a dash or colon.
- **What it means.** introduces an observation and its consequence in two
  to four sentences.
- When payload keys are new to the reader, use **What you are looking at.**
  with a `field | value | what it is` table instead.
- For two findings from one output, distinguish them with labels such as
  **What it means, finding one: …**

Show a prompt or request body once per page. Refer to it by name afterward.

### Explanations and deep dives

Keep inline explanations beside the code or output they explain. Move
material unnecessary for the step to a deep dive, leaving a one-sentence
summary and `See [Title](#anchor).`

Link to an existing reference page before adding a new deep dive.

Use plain-text `###` headings phrased as questions. Keep GitHub anchors
predictable: lowercase letters, punctuation removed, spaces replaced with
hyphens, and underscores retained.

Put each gotcha in a deep dive on the page where the reader encounters it.

## Landing pages

Copy [references/landing-page.md](references/landing-page.md).
Use this order:

1. Navigation without the up-link, then a rule.
2. `# Part N · Title`.
3. An italic, one-sentence subtitle.
4. The **Why you are here.** note.
5. At most one paragraph of context.
6. `## In this part` with a `Section | What it covers` table.
7. Rule and navigation.

Aim for about 200 words.

## Reference pages

Place an optional reference page at the end of a part or tutorial.
Use comparison tables, diagrams, selection guidance, and concrete cases.
Do not include steps. Reference pages may exceed the subtask word budget.

## Markdown and formatting

### Callouts

- `> [!NOTE]`: orient the reader or explain an artifact of how output
  was read.
- `> [!IMPORTANT]`: interpret output.
- `> [!TIP]`: offer an optional side path. Use sparingly.
- `> [!WARNING]`: give a one-sentence warning. Use sparingly; move longer
  explanations to a deep dive.

Use bold sentences ending in periods for callout labels, except the
multiple-finding labels specified above.

### Diagrams and tables

Use one Mermaid `flowchart` per mental model, followed by an italic,
one-line caption. Aim for a diagram on roughly one page in four.

Use tables for TOCs, comparisons, field-by-field explanations, decisions,
and verification status. Use prose when two sentences suffice.

### Code and emphasis

- Use `bash` fences for commands, `console` for captured output, `python`
  for illustrative code, and untagged fences for query strings.
- For illustrative code, link to the source file and show only the relevant
  class or function.
- Use bold for UI elements the reader clicks or reads, and for labels.
- Use inline code for typed input, flags, paths, environment variables,
  and logger names.
- Use neither bold nor inline code for emphasis.
- In Bash fences, put each `--flag` on its own continuation line and each
  `export` on its own line. Preserve short one-liners and `curl` short flags.
- Set an environment variable on its own `export` line before the command, not
  as an inline `VAR=value command` prefix. The reader sees the variable as a
  named setting they can read, change, or unset, and it does not scroll off the
  end of a long command. Write two lines:

  ```bash
  export ADK_EXPERIMENTAL_TELEMETRY=true
  .venv/bin/python examples/01_console_metrics.py
  ```

  not `ADK_EXPERIMENTAL_TELEMETRY=true .venv/bin/python …`. When a variable
  should apply to one command only, say so in the prose and add the matching
  `unset` after, rather than relying on the inline prefix to scope it.
- Do not put comments (`#`) inside a `bash` fence. A reader who copies the whole
  fence pastes the comment as a command. Put any direction, such as which values
  to edit or when a step is optional, in the prose before the fence. Split one
  fence into two around the prose if a mid-sequence instruction is needed. This
  applies only to runnable `bash` fences; comments in `python` code and
  docstrings are fine.

## Voice and evidence

- Use second person, present tense, and imperative steps.
- Use one term consistently for each concept.
- Refer to the next part by number: “Part 2 is about that.”
- When output does not show a behavior, cite its source as
  `path/file.py:line`.
- Follow the global writing rules. Use `/nbj-write-clearly` to draft
  and audit.
- Reserve em dashes for `**Step N — …**` labels.

On the reference page, record what ran, when it ran, and what it showed.
List remaining gaps in a **Not verified** table.

## Working method

- Plan in `docs/<tutorial>-<topic>.md`. Maintain a checklist of stages and
  update it as each stage is completed.
- Before a structural change, document the options, their pros and cons,
  and one recommendation.
- For a new pattern, rewrite and review two exemplar pages before applying
  it throughout.
- Before a concision pass, set a rough word budget for each page.
- Before committing, check that every local `#anchor` and relative link
  resolves, all captured output remains, and filler is removed.
- When a pattern stabilizes, document it in the same commit: here for shared
  conventions, or in the tutorial's `CLAUDE.md` for tutorial-specific ones.