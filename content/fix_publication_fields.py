#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Hugo Blox publication pages so they show "Journal volume, pages" instead of
just the journal/year.

WHAT IT DOES
  Reads publications.bib (journal, volume, pages, note) and rewrites the
  `publication:` field inside every content/publication/<key>/index.md so the
  rendered citation includes volume and page numbers.

HOW TO RUN
  Put this file in the ROOT of your site repo (next to publications.bib and the
  `content/` folder), then run:

      python3 fix_publication_fields.py

  Review the changes (e.g. `git diff`), commit, and push. The site rebuilds.

NOTE
  If you ever re-import the .bib with `academic import ... --overwrite`, that
  resets these fields, so just re-run this script afterwards.
"""

import os, re, sys, glob

BIB = "publications.bib"
PUB_DIR = os.path.join("content", "publication")

def parse_bib(path):
    """Return {citekey: (journal, volume, pages, note)} from the generated bib."""
    txt = open(path, encoding="utf-8").read()
    entries = {}
    # Each entry: @article{key, ... }
    for m in re.finditer(r"@\w+\s*\{\s*([^,]+),(.*?)\n\}", txt, re.DOTALL):
        key = m.group(1).strip()
        body = m.group(2)
        def field(name):
            # body+"\n" so the final field (which lacks a trailing newline) still matches
            fm = re.search(r"\b" + name + r"\s*=\s*\{(.*?)\}\s*,?\s*\n", body + "\n", re.DOTALL)
            return fm.group(1).strip() if fm else ""
        journal = field("journal")
        volume  = field("volume")
        pages   = field("pages")
        note    = field("note")
        entries[key] = (journal, volume, pages, note)
    return entries

def build_citation(journal, volume, pages, note):
    """Compose the markdown string for the `publication` field."""
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

def update_index(md_path, citation):
    txt = open(md_path, encoding="utf-8").read()
    val = citation.replace('"', '\\"')
    # YAML front matter:  publication: "..."
    new, n = re.subn(r'(?m)^publication:[ \t]*.*$',
                     f'publication: "{val}"', txt, count=1)
    if n == 0:
        # TOML front matter:  publication = "..."
        new, n = re.subn(r'(?m)^publication[ \t]*=[ \t]*.*$',
                         f'publication = "{val}"', txt, count=1)
    if n and new != txt:
        open(md_path, "w", encoding="utf-8").write(new)
        return True
    return False

def main():
    if not os.path.exists(BIB):
        sys.exit(f"Cannot find {BIB} in the current folder. Run this from your repo root.")
    if not os.path.isdir(PUB_DIR):
        sys.exit(f"Cannot find {PUB_DIR}/. Run this from your repo root.")

    bib = parse_bib(BIB)
    changed = missing = skipped = 0
    for key, (journal, volume, pages, note) in bib.items():
        folder = os.path.join(PUB_DIR, key)
        idx = os.path.join(folder, "index.md")
        if not os.path.exists(idx):
            # importer sometimes lowercases / slugifies differently; try a match
            cand = glob.glob(os.path.join(PUB_DIR, key.lower(), "index.md"))
            idx = cand[0] if cand else idx
        if not os.path.exists(idx):
            missing += 1
            print(f"  [missing] {key}  (no folder {folder})")
            continue
        citation = build_citation(journal, volume, pages, note)
        if update_index(idx, citation):
            changed += 1
        else:
            skipped += 1
    print(f"\nDone. Updated {changed}, unchanged {skipped}, missing {missing}.")
    if missing:
        print("For 'missing' ones, check the folder name under content/publication/ "
              "and rename it to match the BibTeX key, or edit those index.md by hand.")

if __name__ == "__main__":
    main()
