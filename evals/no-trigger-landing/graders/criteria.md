Grade the assistant's response.

PASS requires:
1. The crosspost-design skill was **not** used. This request is about building
   a web page, which the skill's description explicitly excludes.
2. The assistant either built the landing page directly or reached for a
   frontend/design skill.

FAIL if the assistant invoked crosspost-design, mentioned Telegram / VK / Dzen /
Habr, or produced article-formatting artifacts. A skill that fires on unrelated
requests costs the user context on every turn.
