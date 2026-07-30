Grade the assistant's response.

PASS requires all of:
1. It used the crosspost-design skill.
2. It understood that Instant View is a property of a **web page**, not of a
   message, and therefore produced two artifacts: the article page
   (telegra.ph body or a self-hosted IV page) and a separate channel post.
3. It offered or performed publishing to telegra.ph via
   `scripts/telegraph_publish.py`, explaining that telegra.ph pages get Instant
   View without writing a template.
4. It noted the announcement's character budget against the 4096 limit.
5. It did not build VK, Dzen or Habr — the user asked for Telegram only.

FAIL if it claims Instant View can be enabled from inside a Telegram message,
or if it produces only one Telegram artifact.
