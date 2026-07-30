# Eval cases

Behavioural regression tests for the skill itself, in the layout
`claude plugin eval` expects (`prompt.md` plus `graders/criteria.md`).

Run them with:

    claude plugin eval crosspost-design

The command runs each prompt with and without the plugin (ablation) and scores
the two arms against the grader rubric, so it measures whether the skill
actually improves the answer — not merely that it loads.

**These cases have never been executed.** `claude plugin eval` is in early
access and refuses to run on the account this repository was built with; every
invocation prints `plugin eval is currently in early access` and exits. The
prompts and rubrics are written but unverified: expect to fix the layout or the
wording on the first real run.

What each case pins down:

| Case | Guards against |
|---|---|
| `trigger-ru-crosspost` | not firing on a plain Russian request; asking for platforms the user already named |
| `trigger-en-instant-view` | treating Instant View as a property of a message instead of a page |
| `no-trigger-landing` | firing on unrelated work and taxing every session |
| `platform-choice-technical` | recommending all four platforms as if they were equivalent |
| `degradation-honesty` | shipping a degraded artifact without saying what was lost |
| `typography-only` | building when the user asked only for a typography pass |

The human-readable version of the same list, including cases that need no LLM
grader, is [../references/eval-cases.md](../references/eval-cases.md).
