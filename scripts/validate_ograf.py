#!/usr/bin/env python3
"""
Validate an OGraf Graphic folder against the bundled OGraf v1 schema set and
the Web Component interface contract. Runs fully offline.

Usage:
    python validate_ograf.py <path-to-graphic-folder> [--package OUT.zip]

Exit code 0 = all manifests valid. Non-zero = at least one problem found.

What it checks
--------------
1. Manifest filename ends with `.ograf.json`.
2. Manifest validates against the bundled graphics JSON Schema (incl. GDD + actions).
3. The `main` JavaScript file referenced by the manifest exists.
4. The JS file: has a `export default`, defines a class extending HTMLElement,
   and implements the required interface methods. If `supportsNonRealTime` is
   true, `goToTime()` and `setActionsSchedule()` must also be present.

The static JS check is intentionally lightweight (text-based, not a full parse):
a Web Component that touches `document`/`HTMLElement` can't be imported outside a
browser, so we look for the required surface rather than executing it.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
except ImportError:
    print("ERROR: install dependencies first:  pip install jsonschema --break-system-packages", file=sys.stderr)
    sys.exit(2)

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = SKILL_ROOT / "assets" / "schemas"
SCHEMA_URI_PREFIX = "https://ograf.ebu.io/v1/specification/json-schemas/"

REQUIRED_METHODS = ["load", "dispose", "playAction", "stopAction", "updateAction", "customAction"]
NON_REALTIME_METHODS = ["goToTime", "setActionsSchedule"]

GREEN, RED, YELLOW, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[0m"


def build_validator():
    """Load the bundled schema set and resolve the https $refs to local files."""
    resources = []
    for f in SCHEMA_DIR.rglob("*.json"):
        rel = f.relative_to(SCHEMA_DIR).as_posix()
        uri = SCHEMA_URI_PREFIX + rel
        resources.append((uri, Resource.from_contents(json.loads(f.read_text()))))
    registry = Registry().with_resources(resources)
    graphics_schema = json.loads((SCHEMA_DIR / "graphics" / "schema.json").read_text())
    return Draft202012Validator(graphics_schema, registry=registry)


def check_js(js_path: Path, needs_non_realtime: bool):
    """Static surface check of the Web Component JS file. Returns list of problems."""
    problems = []
    src = js_path.read_text()
    # strip line + block comments so commented-out code doesn't give false positives
    no_block = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
    code = re.sub(r"//.*", "", no_block)

    if "export default" not in code:
        problems.append("missing `export default` of the Graphic class")
    if not re.search(r"class\s+\w+\s+extends\s+HTMLElement", code):
        problems.append("no `class ... extends HTMLElement` found")

    methods = list(REQUIRED_METHODS)
    if needs_non_realtime:
        methods += NON_REALTIME_METHODS
    for m in methods:
        # match `m(` or `async m(` as a method definition
        if not re.search(rf"(^|\s){re.escape(m)}\s*\(", code):
            problems.append(f"missing required method `{m}()`")
    return problems


def check_js_syntax(js_path: Path):
    """Optional: if Node is available, parse the module with `node --check`.
    Returns a problem string, or None if it passed or Node is unavailable."""
    if not shutil.which("node"):
        return None
    res = subprocess.run(["node", "--check", str(js_path)],
                         capture_output=True, text=True)
    if res.returncode != 0:
        out = (res.stderr or res.stdout).strip().splitlines()
        # Prefer the explicit error line (e.g. "SyntaxError: ...") over the trailing version banner.
        err_lines = [ln.strip() for ln in out if "Error" in ln and "Node.js" not in ln]
        detail = err_lines[-1] if err_lines else (out[0].strip() if out else "syntax error")
        return f"JS syntax error (node --check): {detail}"
    return None


def validate_folder(folder: Path, validator):
    manifests = sorted(folder.rglob("*.ograf.json"))
    if not manifests:
        print(f"{RED}No *.ograf.json manifest found in {folder}{RESET}")
        return False

    all_ok = True
    for manifest_path in manifests:
        rel = manifest_path.relative_to(folder)
        problems = []

        if not manifest_path.name.endswith(".ograf.json"):
            problems.append("filename must end with `.ograf.json`")

        try:
            manifest = json.loads(manifest_path.read_text())
        except json.JSONDecodeError as e:
            print(f"{RED}FAIL{RESET} {rel}\n       - invalid JSON: {e}")
            all_ok = False
            continue

        for err in sorted(validator.iter_errors(manifest), key=lambda e: list(e.path)):
            loc = "/".join(str(p) for p in err.path) or "(root)"
            problems.append(f"schema: [{loc}] {err.message}")

        main = manifest.get("main")
        if main:
            js_path = (manifest_path.parent / main)
            if not js_path.exists():
                problems.append(f"`main` file not found: {main}")
            else:
                needs_nrt = bool(manifest.get("supportsNonRealTime"))
                problems += check_js(js_path, needs_nrt)
                syntax_problem = check_js_syntax(js_path)
                if syntax_problem:
                    problems.append(syntax_problem)

        if problems:
            all_ok = False
            print(f"{RED}FAIL{RESET} {rel}")
            for p in problems:
                print(f"       - {p}")
        else:
            print(f"{GREEN}PASS{RESET} {rel}")
    return all_ok


def package(folder: Path, out_zip: Path):
    files = [p for p in folder.rglob("*") if p.is_file()]
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, p.relative_to(folder.parent))
    print(f"{GREEN}Packaged{RESET} {len(files)} files -> {out_zip}")


def main():
    ap = argparse.ArgumentParser(description="Validate an OGraf Graphic folder.")
    ap.add_argument("folder", help="Path to the graphic folder")
    ap.add_argument("--package", metavar="OUT.zip", help="If valid, zip the folder to this path")
    args = ap.parse_args()

    folder = Path(args.folder).resolve()
    if not folder.is_dir():
        print(f"{RED}Not a directory: {folder}{RESET}", file=sys.stderr)
        sys.exit(2)

    validator = build_validator()
    ok = validate_folder(folder, validator)

    if ok and args.package:
        package(folder, Path(args.package).resolve())

    if ok:
        print(f"\n{GREEN}All OGraf manifests valid.{RESET}")
        sys.exit(0)
    else:
        print(f"\n{RED}Validation failed — fix the issues above before delivering.{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
