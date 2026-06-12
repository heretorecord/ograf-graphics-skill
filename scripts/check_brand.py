#!/usr/bin/env python3
"""
Advisory brand-consistency check for an OGraf graphic against a brand kit.

Usage:
    python check_brand.py <graphic-folder> <brand-kit.json>

Always exits 0 (this is guidance, not a spec gate). It reports:
  - hex colours used in the component(s) that are NOT in the kit palette;
  - font-family stacks that don't match the kit's primary font;
  - whether the manifest's `v_brand` stamp matches the kit id/version.

Run the real gate (validate_ograf.py) separately — that one enforces the spec.
"""
import json
import re
import sys
from pathlib import Path

GREEN, RED, YELLOW, DIM, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[2m", "\033[0m"


def norm_hex(h):
    h = h.lower()
    if len(h) == 4:  # #abc -> #aabbcc
        h = "#" + "".join(c * 2 for c in h[1:])
    return h


def _norm_font(s):
    # Lower-case, drop quotes, collapse whitespace so "Arial", 'Arial' and Arial match.
    s = s.lower().replace('"', "").replace("'", "")
    s = re.sub(r"\s+", " ", s)
    return ", ".join(part.strip() for part in s.split(","))


def main():
    if len(sys.argv) != 3:
        print("Usage: python check_brand.py <graphic-folder> <brand-kit.json>", file=sys.stderr)
        sys.exit(0)

    folder = Path(sys.argv[1]).resolve()
    kit = json.loads(Path(sys.argv[2]).read_text())

    palette = {norm_hex(v) for v in (kit.get("colors") or {}).values()
               if isinstance(v, str) and v.startswith("#")}
    primary_font = _norm_font((kit.get("fonts") or {}).get("primary", ""))

    js_files = list(folder.rglob("*.mjs")) + list(folder.rglob("*.js"))
    manifests = list(folder.rglob("*.ograf.json"))

    print(f"{DIM}Brand check against kit {kit.get('id')} v{kit.get('version')}{RESET}\n")

    # --- colours ---------------------------------------------------------
    used = {}
    for f in js_files:
        for m in re.finditer(r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?\b", f.read_text()):
            used.setdefault(norm_hex(m.group(0)), set()).add(f.name)
    off_palette = {c: files for c, files in used.items() if c not in palette}
    if not used:
        print(f"{DIM}No hex colours found in component (may use CSS vars only).{RESET}")
    elif off_palette:
        print(f"{YELLOW}Colours not in the kit palette:{RESET}")
        for c, files in sorted(off_palette.items()):
            print(f"   {c}  ({', '.join(sorted(files))})")
        print(f"{DIM}   Palette: {', '.join(sorted(palette)) or '(none)'}{RESET}")
    else:
        print(f"{GREEN}All hex colours are within the kit palette.{RESET}")

    # --- fonts -----------------------------------------------------------
    fonts = set()
    for f in js_files:
        for m in re.finditer(r"font-family\s*:\s*([^;{}\n]+)", f.read_text(), re.I):
            fonts.add(_norm_font(m.group(1)))
    if fonts and primary_font:
        mismatched = [s for s in fonts if s != primary_font]
        if mismatched:
            print(f"\n{YELLOW}Font stacks that differ from the kit primary:{RESET}")
            for s in sorted(mismatched):
                print(f"   {s}")
            print(f"{DIM}   Kit primary: {primary_font}{RESET}")
        else:
            print(f"\n{GREEN}Font stack matches the kit primary.{RESET}")

    # --- provenance ------------------------------------------------------
    print()
    stamped = False
    for mf in manifests:
        m = json.loads(mf.read_text())
        vb = m.get("v_brand")
        if not vb:
            print(f"{YELLOW}{mf.name}: no v_brand stamp — add "
                  f'"v_brand": {{"id":"{kit.get("id")}","version":"{kit.get("version")}"}}{RESET}')
            continue
        stamped = True
        if vb.get("id") == kit.get("id") and str(vb.get("version")) == str(kit.get("version")):
            print(f"{GREEN}{mf.name}: v_brand matches the kit.{RESET}")
        else:
            print(f"{YELLOW}{mf.name}: v_brand is {vb}, kit is "
                  f'{{"id":"{kit.get("id")}","version":"{kit.get("version")}"}}{RESET}')

    print(f"\n{DIM}Advisory only — this does not gate delivery.{RESET}")
    sys.exit(0)


if __name__ == "__main__":
    main()
