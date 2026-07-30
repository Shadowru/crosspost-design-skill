Grade the assistant's response.

PASS requires all of:
1. It used the crosspost-design skill and ran `scripts/typography_lint.py`
   against the file.
2. It did **not** run the build — the user said not to. Producing platform
   artifacts here is a failure to read the request.
3. It explained the Russian rules it applied or checked: «ёлочки» for quotes,
   em dash rather than a hyphen between words, en dash in numeric ranges, `…`
   as one character.
4. If it reported that the file is already clean, that is correct and passes —
   the shipped sample is clean. Inventing fixes that were not needed is a fail.

FAIL if it hand-edits punctuation with sed or manual rewrites instead of using
the linter, or if it builds platform outputs.
