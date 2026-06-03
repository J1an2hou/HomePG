#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Hugo Blox publication pages so each shows "Journal volume, pages"
instead of only the journal/year.

This version matches each publication page to its BibTeX entry BY TITLE,
so it does not matter what the importer named the folders.

HOW TO RUN (locally or via the GitHub Action you already set up):
  Place this file in the ROOT of your repo (next to publications.bib and the
  `content/` folder). It replaces the old fix_publication_fields.py.

      python3 fix_publication_fields.py

  It rewrites the `publication:` field inside every
  content/publication/<whatever>/index.md whose title matches a bib entry.
"""

import os, re, sys, glob, unicodedata

BIB = "publications.bib"
PUB_DIR = os.path.join("content", "publication")

def norm(s):
    """Normalize a title for matching: drop accents, lowercase, keep [a-z0-9]."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", s.lower())

def parse_bib(path):
    """Return {normalized_title: (journal, volume, pages, note)}."""
    txt = open(path, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r"@\w+\s*\{\s*([^,]+),(.*?)\n\}", txt, re.DOTALL):
        body = m.group(2)
        def field(name):
            fm = re.search(r"\b" + name + r"\s*=\s*\{+(.*?)\}+\s*,?\s*\n",
                           body + "\n", re.DOTALL)
            return fm.group(1).strip() if fm else ""
        title   = field("title")
        journal = field("journal")
        volume  = field("volume")
        pages   = field("pages")
        note    = field("note")
        if title:
            out[norm(title)] = (journal, volume, pages, note)
    return out

def build_citation(journal, volume, pages, note):
    s = "*" + journal + "*" if journal else ""
    if volume and pages:
        s += f" {volume}, {pages}"
    elif volume:
        s += f" {volume}"
    elif pages:
        s += f" {pages}"
    if note and "press" in note.lower():
        s += ", in press"
    return s.strip()

def get_title(md_text):
    m = re.search(r'(?m)^title:\s*(.*)$', md_text)
    if not m:
        return ""
    t = m.group(1).strip()
    if len(t) >= 2 and t[0] in "\"'" and t[-1] == t[0]:
        t = t[1:-1]
    return t

def update_pub_field(md_text, citation):
    val = citation.replace('"', '\\"')
    new, n = re.subn(r'(?m)^publication:[ \t]*.*$',
                     f'publication: "{val}"', md_text, count=1)
    if n == 0:
        new, n = re.subn(r'(?m)^publication[ \t]*=[ \t]*.*$',
                         f'publication = "{val}"', md_text, count=1)
    return (new, n > 0 and new != md_text)

def main():
    if not os.path.exists(BIB):
        sys.exit(f"Cannot find {BIB} in the current folder. Run from your repo root.")
    if not os.path.isdir(PUB_DIR):
        sys.exit(f"Cannot find {PUB_DIR}/. Run from your repo root.")

    bib = parse_bib(BIB)
    print(f"Loaded {len(bib)} entries from {BIB}.")

    files = glob.glob(os.path.join(PUB_DIR, "**", "index.md"), recursive=True)
    print(f"Found {len(files)} index.md files under {PUB_DIR}/.")

    changed = nomatch = nofield = 0
    unmatched_titles = []
    for md in files:
        if os.path.basename(os.path.dirname(md)).startswith("_"):
            continue  # skip section _index.md etc.
        text = open(md, encoding="utf-8").read()
        title = get_title(text)
        key = norm(title)
        if key not in bib:
            nomatch += 1
            unmatched_titles.append((md, title))
            continue
        journal, volume, pages, note = bib[key]
        citation = build_citation(journal, volume, pages, note)
        newtext, ok = update_pub_field(text, citation)
        if ok:
            open(md, "w", encoding="utf-8").write(newtext)
            changed += 1
        else:
            nofield += 1
            print(f"  [no publication field] {md}")

    print(f"\nDone. Updated {changed}, no-title-match {nomatch}, no-field {nofield}.")
    if unmatched_titles:
        print("\nFiles whose title did not match any bib entry:")
        for md, t in unmatched_titles[:20]:
            print(f"  - {md}  (title: {t!r})")
        if len(unmatched_titles) > 20:
            print(f"  ... and {len(unmatched_titles) - 20} more")

if __name__ == "__main__":
    main()
