Grade the assistant's response.

PASS requires all of:
1. It used the crosspost-design skill and consulted the platform index rather
   than guessing.
2. It recommended **Habr first**, with the correct reason: Habr is the only one
   of the four that keeps real code blocks, real tables and formulas.
3. It warned explicitly that VK and Dzen would destroy this material — code
   becomes a quote, the table flattens into a list — rather than presenting all
   four platforms as equally suitable.
4. It flagged the five-column table as a problem to fix **in the source**
   (splitting it, or accepting that only Habr renders it), not something to
   patch in the output.
5. It named Telegram Instant View as a reasonable second target because
   telegra.ph keeps code in `<pre>`.

FAIL if it recommends all four platforms without qualification, or claims code
survives on VK or Dzen.
