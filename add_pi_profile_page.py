#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Give the PI a profile page at /author/jian-zhou/ (where the People widget and the
publications link), by copying the existing admin profile into a folder named to
match the name-slug.

The original content/authors/admin/ folder is left untouched, so the homepage
biography (which references username "admin") keeps working.

Edit SRC_USER / DST_SLUG below if your folder or name-slug differ.

RUN from the repo root:
    python3 add_pi_profile_page.py
"""

import os, re, sys, shutil

SRC_USER = "admin"        # your existing profile folder
DST_SLUG = "jian-zhou"    # the slug your name links to (lowercase, hyphenated)

SRC = os.path.join("content", "authors", SRC_USER)
DST = os.path.join("content", "authors", DST_SLUG)

def main():
    if not os.path.isdir(SRC):
        sys.exit(f"Cannot find {SRC}/. Run from your repo root.")
    if os.path.isdir(DST):
        print(f"{DST}/ already exists - leaving it as is.")
    else:
        shutil.copytree(SRC, DST)
        print(f"Copied {SRC}/ -> {DST}/ (including the avatar).")

    idx = os.path.join(DST, "_index.md")
    if not os.path.exists(idx):
        sys.exit(f"No _index.md in {DST}/ - nothing to clean up.")
    t = open(idx, encoding="utf-8").read()

    # This copy is NOT the superuser and must NOT be listed again in People,
    # so remove those two keys. Also drop any self-referencing authors field.
    t = re.sub(r'(?m)^superuser:.*\n', '', t)
    t = re.sub(r'(?m)^user_groups:[ \t]*\n(?:[ \t]*-[ \t]+.*\n)*', '', t)
    t = re.sub(r'(?m)^authors:[ \t]*\n(?:[ \t]*-[ \t]+.*\n)*', '', t)
    # also handle an inline authors: [..] just in case
    t = re.sub(r'(?m)^authors:[ \t]*\[.*\]\s*\n', '', t)

    open(idx, "w", encoding="utf-8").write(t)
    print(f"Cleaned {idx}: removed superuser / user_groups / authors so the PI "
          f"appears once in People and this folder just supplies the profile.")

if __name__ == "__main__":
    main()
