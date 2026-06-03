#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Hugo Blox publication pages so each shows "Journal volume, pages".

Matches each publication page to its BibTeX entry BY TITLE (folder names are
ignored). Handles the case where the importer TRUNCATED long titles: if a page's
title is a prefix of exactly one bib title, it is matched, and the full title is
restored in the page as well.

RUN from the ROOT of your repo (next to publications.bib and content/):
    python3 fix_publication_fields.py
"""

import os, re, sys, glob, unicodedata

BIB = "publications.bib"
PUB_DIR = os.path.join("content", "publication")

def norm(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", s.lower())

def parse_bib(path):
    """Return list of dicts with full title + venue info."""
    txt = open(path, encoding="utf-8").read()
    out = []
    for m in re.finditer(r"@\w+\s*\{\s*([^,]+),(.*?)\n\}", txt, re.DOTALL):
        body = m.group(2)
        def field(name):
            fm = re.search(r"\b" + name + r"\s*=\s*\{+(.*?)\}+\s*,?\s*\n",
                           body + "\n", re.DOTALL)
            return fm.group(1).strip() if fm else ""
        title = field("title")
        if title:
            out.append({
                "title": title, "norm": norm(title),
                "journal": field("journal"), "volume": field("volume"),
                "pages": field("pages"), "note": field("note"),
            })
    return out

def build_citation(e):
    s = "*" + e["journal"] + "*" if e["journal"] else ""
    if e["volume"] and e["pages"]:
        s += f" {e['volume']}, {e['pages']}"
    elif e["volume"]:
        s += f" {e['volume']}"
    elif e["pages"]:
        s += f" {e['pages']}"
    if e["note"] and "press" in e["note"].lower():
        s += ", in press"
    return s.strip()

def get_title(md_text):
    m = re.search(r'(?m)^title:\s*(.*)$', md_text)
    if not m:
        m = re.search(r'(?m)^title\s*=\s*(.*)$', md_text)
    if not m:
        return ""
    t = m.group(1).strip()
    if len(t) >= 2 and t[0] in "\"'" and t[-1] == t[0]:
        t = t[1:-1]
    return t

def set_field(md_text, field, value):
    val = value.replace('"', '\\"')
    new, n = re.subn(r'(?m)^' + field + r':[ \t]*.*$',
                     f'{field}: "{val}"', md_text, count=1)
    if n == 0:
        new, n = re.subn(r'(?m)^' + field + r'[ \t]*=[ \t]*.*$',
                         f'{field} = "{val}"', md_text, count=1)
    return new, n > 0

def main():
    if not os.path.exists(BIB):
        sys.exit(f"Cannot find {BIB}. Run from your repo root.")
    if not os.path.isdir(PUB_DIR):
        sys.exit(f"Cannot find {PUB_DIR}/. Run from your repo root.")

    bib = parse_bib(BIB)
    by_norm = {e["norm"]: e for e in bib}
    print(f"Loaded {len(bib)} entries from {BIB}.")

    files = glob.glob(os.path.join(PUB_DIR, "**", "index.md"), recursive=True)
    print(f"Found {len(files)} index.md files under {PUB_DIR}/.")

    updated = title_fixed = nomatch = ambiguous = 0
    unmatched = []
    for md in files:
        if os.path.basename(os.path.dirname(md)).startswith("_"):
            continue
        text = open(md, encoding="utf-8").read()
        title = get_title(text)
        k = norm(title)
        if not k:
            continue

        entry = by_norm.get(k)
        truncated = False
        if entry is None:
            # prefix match: the stored title is a truncated start of a full one
            cands = [e for e in bib if len(k) >= 15 and e["norm"].startswith(k)]
            if len(cands) == 1:
                entry = cands[0]; truncated = True
            elif len(cands) > 1:
                ambiguous += 1
                unmatched.append((md, title, "ambiguous"))
                continue

        if entry is None:
            nomatch += 1
            unmatched.append((md, title, "no match"))
            continue

        newtext, ok = set_field(text, "publication", build_citation(entry))
        if truncated:  # also repair the truncated display title
            newtext, okt = set_field(newtext, "title", entry["title"])
            if okt:
                title_fixed += 1
        if ok and newtext != text:
            open(md, "w", encoding="utf-8").write(newtext)
            updated += 1

    print(f"\nDone. Updated {updated} (of which {title_fixed} also had a truncated "
          f"title repaired). Ambiguous {ambiguous}, no-match {nomatch}.")
    if unmatched:
        print("\nStill unmatched:")
        for md, t, why in unmatched:
            print(f"  - [{why}] {md}  (title: {t!r})")

if __name__ == "__main__":
    main()
