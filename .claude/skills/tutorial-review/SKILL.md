---
name: tutorial-review
description: Reviews a tutorial in this repo as a fresh reader, reruns its demos unattended, and writes a findings report without editing tutorial content or scripts. Use when Jeff asks to review a tutorial, part, or page, or runs "/tutorial-review <path>".
argument-hint: <tutorial folder, part, or page, e.g. ai/adk/tracing or ai/adk/tracing/tutorial/part-4>
---

# Tutorial review

Review a tutorial as a student who knows general software engineering but is
new to ADK. Report findings; don't fix them.

## Scope

The argument is a tutorial folder, a part folder, or a single page. Review
only that scope. If no argument was given, ask for it.

Review the working tree, including uncommitted changes, not `HEAD`.

## What the review may change

Treat every tracked file as read-only: tutorial pages, examples, demo agents,
deploy and load scripts, and `env.sh.example`. Read and run them, but don't
edit them. Report a broken script as a finding.

- Run demos in place. They may write gitignored output such as `out/` and logs.
- Don't edit `env.sh`. Export the variables a demo needs in the shell that runs
  it.
- Create no file except the report described in Output.
- Run `git status --porcelain` before the first demo and after the last. Apart
  from the report, the two results must match. If they don't, list the
  differences in the report.

## Review rules

### Writing

- Write concisely, clearly, cleanly, correctly, and elegantly.
- Treat shorthand as a defect: any phrase that only makes sense if you already
  know the point, such as a compressed label, a metaphor, or a term of art.

### Facts

Check each assertion against the ADK version pinned in the tutorial's
`requirements.txt`, using:

- Introspection of that installed ADK and GenAI SDK. Confirm the version with
  `pip show`.
- Documentation. If the latest docs differ from the pinned version, note the
  difference but don't count it as a defect.
- The demo runs below.

### Demos

Rerun, unattended, every demo the pages ask the reader to run. Confirm that the
output matches what the page shows and claims.

- Give each demo agent its own dev project, `jwd-dev-1` through `jwd-dev-5`.
  Never use `jwd-gcp-demos`, because it holds the tutorials' published captures.
- Export `PROJECT_ID`, `GOOGLE_CLOUD_PROJECT`, and the page's other variables
  explicitly. Don't rely on values already set in the shell.
- Deploy when a demo calls for it. Before finishing, delete every cloud
  resource the review created, and list any you couldn't delete.
- Skip any demo likely to cost more than $2. Report it as skipped, with the
  cost estimate.

### Logic

- Check that each page's story holds together.
- Check that guidance and examples are sensible and realistic.

## Rubric

Before reviewing, read these sources in full, in this order:

1. The rules in this skill.
2. `.claude/skills/tutorial-style/SKILL.md` and every file it references in
   that folder.
3. The tutorial's own `CLAUDE.md`.
4. The Writing section of `~/.claude/CLAUDE.md`, and the pedagogy note at
   `~/.claude/projects/-Users-jeff-Desktop-Dev-gcp-demos/memory/feedback-tutorial-pedagogy.md`.

Merge them into one rubric. List each rule on one line with its source: the
file and section, or "this skill." If two sources state the same rule, list
it once and cite both.

If sources conflict, this skill wins. Otherwise the more specific source wins:
the tutorial's `CLAUDE.md` over the tutorial-style skill, and that skill over
global preferences. Mark each conflict in the rubric with the rule you applied
and the rule you overrode, so no conflict is resolved silently.

## Execution

Run sub-agents on Sonnet 5.5 (`model: "sonnet"`). As the main agent:

1. Build the rubric and pass it to every sub-agent.
2. For each part in scope, launch three sub-agents:
   - **Reader:** writing, shorthand, and logic, checked against the rubric.
   - **Fact:** assertions, checked against the pinned SDKs and docs.
   - **Demo:** reruns the part's demos on its own dev project.
3. Merge the results, check for inconsistencies across pages, and write the
   report.

## Output

Write the report to `docs/<tutorial>-review-<YYYY-MM-DD>.md`, then post a short
summary in chat. In the report:

- Group findings by file path, in reading order.
- For each finding, give a severity tag (**wrong**, **misleading**,
  **unclear**, or **style**), the exact quoted text, the standard it breaks,
  and a concrete rewrite. Sort each page's findings by severity.
- Report only real problems. Mark clean pages "no findings."
- List each demo run with its command, project, and result. List skipped demos
  separately.
- End with cross-page inconsistencies, then any leftover cloud resources or
  `git status` differences.
- Put the rubric in an appendix. Start with the rules this review found
  violated.
