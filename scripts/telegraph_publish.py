#!/usr/bin/env python3
"""Publish the built telegra.ph body and get a link with native Instant View.

telegra.ph pages are the one place where Instant View works without writing a
template: paste the URL into any Telegram chat and the IV button appears. This
converts `{slug}.telegram-iv.html` into telegra.ph's Node JSON and posts it.

Usage:
    telegraph_publish.py post.telegram-iv.html --title "…" --author "…"
    telegraph_publish.py post.telegram-iv.html --title "…" --token <access_token>
    telegraph_publish.py post.telegram-iv.html --title "…" --dry-run   # print JSON

    # republish an existing page in place, keeping its URL:
    telegraph_publish.py post.telegram-iv.html --title "…" \
        --token <access_token> --edit My-Page-Path-01-02

Without --token a throwaway account is created and its access_token is printed;
save it — editing a page later is impossible without it, and republishing under
a new URL breaks every link you have already shared. Network access is required
unless --dry-run is used.

Exit codes: 0 published (or dry run); 1 failure.
"""

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser

API = "https://api.telegra.ph/"
# telegra.ph Node whitelist; anything else is unwrapped into its children.
ALLOWED = {"a", "aside", "b", "blockquote", "br", "code", "em", "figcaption",
           "figure", "h3", "h4", "hr", "i", "iframe", "img", "li", "ol", "p",
           "pre", "s", "strong", "u", "ul", "video"}
VOID = {"br", "hr", "img"}
ATTRS = {"href", "src"}


class NodeBuilder(HTMLParser):
    """HTML -> telegra.ph Node tree."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = []
        self.stack = []
        self.dropped = set()

    def _append(self, node):
        (self.stack[-1]["children"] if self.stack else self.root).append(node)

    def handle_starttag(self, tag, attrs):
        if tag not in ALLOWED:
            self.dropped.add(tag)
            return
        node = {"tag": tag}
        kept = {k: v for k, v in attrs if k in ATTRS and v}
        if kept:
            node["attrs"] = kept
        if tag in VOID:
            self._append(node)
            return
        node["children"] = []
        self._append(node)
        self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID and tag in ALLOWED and self.stack:
            self.stack.pop()

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]["tag"] == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        if data.strip() or (self.stack and data == " "):
            self._append(data)

    def result(self):
        def prune(nodes):
            out = []
            for n in nodes:
                if isinstance(n, dict):
                    if "children" in n:
                        n["children"] = prune(n["children"])
                        if not n["children"] and n["tag"] not in VOID:
                            continue
                out.append(n)
            return out
        return prune(self.root)


def api(method, params):
    data = urllib.parse.urlencode(params).encode()
    with urllib.request.urlopen(API + method, data=data, timeout=30) as r:
        payload = json.loads(r.read().decode())
    if not payload.get("ok"):
        raise RuntimeError(payload.get("error", "unknown telegra.ph error"))
    return payload["result"]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html", help="the .telegram-iv.html body produced by build_targets.py")
    ap.add_argument("--title", required=True)
    ap.add_argument("--author", default="")
    ap.add_argument("--author-url", default="")
    ap.add_argument("--token", help="existing telegra.ph access_token")
    ap.add_argument("--edit", metavar="PATH",
                    help="update this existing page instead of creating a new one "
                         "(the part of the URL after telegra.ph/); requires --token")
    ap.add_argument("--dry-run", action="store_true", help="print the Node JSON, post nothing")
    args = ap.parse_args()

    if not os.path.isfile(args.html):
        print("✗ no such file: %s" % args.html, file=sys.stderr)
        return 1
    with open(args.html, encoding="utf-8") as f:
        html = f.read()

    builder = NodeBuilder()
    builder.feed(html)
    nodes = builder.result()
    if builder.dropped:
        print("! tags outside the telegra.ph whitelist were unwrapped: %s"
              % ", ".join(sorted(builder.dropped)), file=sys.stderr)

    if args.dry_run:
        print(json.dumps(nodes, ensure_ascii=False, indent=2))
        return 0

    if args.edit and not args.token:
        print("✗ --edit needs --token: only the account that created a page can "
              "change it", file=sys.stderr)
        return 1

    try:
        token = args.token
        if not token:
            acct = api("createAccount", {
                "short_name": (args.author or "author")[:32],
                "author_name": args.author[:128],
                "author_url": args.author_url,
            })
            token = acct["access_token"]
            print("• new telegra.ph account — save this token to edit later:\n  %s" % token)
        params = {
            "access_token": token,
            "title": args.title[:256],
            "author_name": args.author[:128],
            "author_url": args.author_url,
            "content": json.dumps(nodes, ensure_ascii=False),
            "return_content": "false",
        }
        if args.edit:
            page = api("editPage/" + args.edit.strip("/"), params)
        else:
            page = api("createPage", params)
    except Exception as e:                       # network, API or JSON failure
        print("✗ publishing failed: %s" % e, file=sys.stderr)
        return 1

    print("✓ %s: %s" % ("updated" if args.edit else "published", page["url"]))
    print("  paste that URL in Telegram — the Instant View button is automatic")
    print("  feed it back as --iv-url to build_targets.py to link the announcement")
    return 0


if __name__ == "__main__":
    sys.exit(main())
