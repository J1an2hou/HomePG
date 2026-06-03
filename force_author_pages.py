#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Force Hugo Blox to generate a profile page for every author folder.

For each content/authors/<username>/_index.md, ensure the front matter contains
    authors: ["<username>"]
(the folder name). Hugo only builds an author's profile page when that username
appears in some page's `authors` field, so this makes every group member's
profile render with their own info.

Safe: only ADDS the line if no `authors:` field is already present. Never edits
existing fields, so it can't corrupt YAML.

RUN from the repo root:
    python3 force_author_pages.py
"""

import os, re, glob, sys

AUTHORS_DIR = os.path.join("content", "authors")

def main():
    if not os.path.isdir(AUTHORS_DIR):
        sys.exit(f"Cannot find {AUTHORS_DIR}/. Run from your repo root.")

    added = skipped = 0
    for idx in sorted(glob.glob(os.path.join(AUTHORS_DIR, "*", "_index.md"))):
        username = os.path.basename(os.path.dirname(idx))
        text = open(idx, encoding="utf-8").read()

        m = re.match(r"^(---\n)(.*?\n)(---\n?)(.*)$", text, re.DOTALL)
        if not m:
            print(f"  [skip: no YAML front matter] {idx}")
            skipped += 1
            continue
        open_d, fm, close_d, body = m.groups()

        if re.search(r"(?m)^authors\s*:", fm):
            skipped += 1  # already has an authors field; leave it alone
            continue

        fm = f'authors:\n  - "{username}"\n' + fm
        open(idx, "w", encoding="utf-8").write(open_d + fm + close_d + body)
        print(f"  [added authors: {username}] {idx}")
        added += 1

    print(f"\nDone. Added authors field to {added} profile(s); left {skipped} unchanged.")

if __name__ == "__main__":
    main()
