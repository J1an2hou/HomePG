#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Hugo Blox publication pages so each shows "Journal volume, pages".

Robust to:
  * folder names that don't match the BibTeX key (matches by TITLE),
  * titles the importer wrapped across multiple indented YAML lines,
  * files left with an orphaned continuation line by an earlier broken run
    (these are detected and repaired).

It rewrites the `title:` and `publication:` fields of each matched page to a
clean single line, leaving the rest of the front matter untouched.

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
            out.append({"title": title, "norm": norm(title),
                        "journal": field("journal"), "volume": field("volume"),
                        "pages": field("pages"), "note": field("note")})
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

def split_front_matter(text):
    m = re.match(r"^(---\n)(.*?\n)(---\n?)(.*)$", text, re.DOTALL)
    if m:
        return list(m.groups()) + ["yaml"]
    m = re.match(r"^(\+\+\+\n)(.*?\n)(\+\+\+\n?)(.*)$", text, re.DOTALL)
    if m:
        return list(m.groups()) + ["toml"]
    return None

# field line + any following indented (continuation/orphan) lines
def field_span_re(name):
    return re.compile(r"(?m)^" + re.escape(name) + r"[ \t]*[:=][ \t]*.*(?:\n[ \t]+.*)*")

def read_field(fm, name):
    mm = field_span_re(name).search(fm)
    if not mm:
        return ""
    block = mm.group(0)
    block = re.sub(r"(?m)^" + re.escape(name) + r"[ \t]*[:=][ \t]*", "", block, count=1)
    val = " ".join(line.strip() for line in block.splitlines())
    val = re.sub(r"\s+", " ", val).strip()
    if len(val) >= 2 and val[0] in "\"'" and val[-1] == val[0]:
        val = val[1:-1]
    return val.replace("''", "'")

def write_field(fm, name, value, fmt):
    esc = value.replace("\\", "\\\\").replace('"', '\\"')
    sep = ":" if fmt == "yaml" else " ="
    repl = f"{name}{sep} \"{esc}\""
    new, n = field_span_re(name).subn(lambda _: repl, fm, count=1)
    return new, n > 0

def find_entry(bib, by_norm, k):
    if not k:
        return None, None
    e = by_norm.get(k)
    if e:
        return e, "exact"
    # stored title is a prefix of one full title (wrapped, read partially)
    c = [e for e in bib if len(k) >= 15 and e["norm"].startswith(k)]
    if len(c) == 1:
        return c[0], "prefix"
    # stored title starts with a full title (corrupted: duplicated tail)
    c = [e for e in bib if len(e["norm"]) >= 15 and k.startswith(e["norm"])]
    if len(c) == 1:
        return c[0], "corrupted"
    return None, ("ambiguous" if c else "none")

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

    updated = repaired = 0
    unmatched = []
    for md in files:
        if os.path.basename(os.path.dirname(md)).startswith("_"):
            continue
        text = open(md, encoding="utf-8").read()
        parts = split_front_matter(text)
        if not parts:
            unmatched.append((md, "<no front matter>", "skipped"))
            continue
        open_d, fm, close_d, body, fmt = parts

        title = read_field(fm, "title")
        entry, how = find_entry(bib, by_norm, norm(title))
        if entry is None:
            unmatched.append((md, title[:70], how))
            continue

        before = fm
        fm, _  = write_field(fm, "publication", build_citation(entry), fmt)
        fm, _  = write_field(fm, "title", entry["title"], fmt)  # also normalizes wrapping
        if how in ("prefix", "corrupted"):
            repaired += 1
        if fm != before:
            open(md, "w", encoding="utf-8").write(open_d + fm + close_d + body)
            updated += 1

    print(f"\nDone. Updated {updated} (repaired {repaired} wrapped/corrupted titles). "
          f"Unmatched {len(unmatched)}.")
    for md, t, why in unmatched:
        print(f"  - [{why}] {md}  (title: {t!r})")

if __name__ == "__main__":
    main()
