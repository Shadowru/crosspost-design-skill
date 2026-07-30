Grade the assistant's response.

PASS requires all of:
1. It used the crosspost-design skill — it read SKILL.md and followed the
   documented pipeline rather than improvising a conversion.
2. It built for **Dzen and VK only**. The user named the platforms, so asking
   which platforms to target is a failure, and silently building Habr or
   Telegram as well is a failure.
3. It ran `build_targets.py` and then `validate_post.py`, and reported the
   validator verdict.
4. It surfaced the degradation report: at minimum that the table collapsed into
   a list on both platforms, that the code block became a quote, and that the
   image must be uploaded by hand in VK.
5. It did not hand-write or hand-patch platform HTML.

FAIL if the response invents markup capabilities these platforms do not have
(inline CSS, colours, real tables on VK/Dzen) or claims the result can be
pasted with images intact.
