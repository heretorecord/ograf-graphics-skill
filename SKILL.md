---
name: ograf-graphics
description: Create broadcast graphics (lower thirds, full-screen titles, tickers, bugs/logos, clocks, scoreboards, name supers) that conform to the EBU OGraf v1 specification, so they run in any OGraf-compatible renderer. Use this skill whenever the user wants to build, generate, design, or export a TV/broadcast/live graphic, an "OGraf graphic", an HTML graphic for playout, or anything they describe wanting to "use in their production" — even if they don't say the word "OGraf". Also use it to validate or fix an existing OGraf graphic against the spec.
---

# OGraf Graphics

Build broadcast graphics that pass the EBU OGraf v1 specification and run in any
compatible renderer. The deliverable is a **validated graphic folder** (manifest +
JS Web Component + any resources), packaged as a zip the user can drop into a
renderer or editor.

A graphic is only done when `scripts/validate_ograf.py` passes. Never deliver an
unvalidated graphic — "looks right" is not the same as "passes the spec".

## What an OGraf graphic is

A folder containing:
- **A manifest** — a JSON file whose name ends with `.ograf.json`, describing the
  graphic and its editable data. Full field reference: `references/manifest-spec.md`.
- **A JS Web Component** (referenced by the manifest's `main`) — a `class extends
  HTMLElement` with a `default export`, implementing the OGraf lifecycle/action
  methods. Full contract: `references/component-interface.md`.
- **Resources** (optional) — images, fonts, video, organized however you like.

## Workflow

### 1. Understand the graphic

Get enough to build the right thing. Ask only what you can't reasonably infer, and
prefer sensible, stated defaults over stalling.

- **Type** — lower third, full-screen title, ticker, bug/logo, clock, scoreboard, etc.
- **Editable fields — always clarify this explicitly.** Which values should an operator
  be able to change at play-out, and which are baked into the design? For each editable
  value, capture its **type**: text, multi-line text, number, integer, on/off, colour,
  image, or a fixed set of choices (enum). These become the manifest `schema`;
  everything else is hard-coded in the component. Don't expose everything by default —
  expose only what an operator realistically changes. If the user is unsure, propose a
  short typed list based on the graphic type and confirm it. When the surface allows
  interactive prompts (e.g. a multi-select), offer the candidate fields that way rather
  than as prose. Field types map to GDD types in `references/manifest-spec.md`.
- **Brand** — check whether the user has a **brand kit** (see "Brand kits" below). If
  they do, build from it. If they don't and they care about a consistent look across
  graphics, offer to start one. If they reference a kit from earlier work, search past
  conversations to recover it.
- **Look** — colours, fonts, position. Default to the brand kit, else clean broadcast
  conventions (below); don't block on styling.
- **Behavior** — single reveal (stepCount 1) vs multiple steps; realtime (default) vs
  also non-realtime (post-production scrubbing).

Every editable field MUST get a sensible `default` in the schema, **and** the component
MUST seed itself from those defaults at `load()` (e.g. `this.state = { ...DEFAULTS }`
before applying `params.data`) so it never renders blank when a renderer doesn't inject
manifest defaults. Momentum over interrogation.

### 2. Build the folder

Start from the templates — they are valid and dependency-free:
- `assets/templates/manifest.ograf.json`
- `assets/templates/graphic.mjs` (vanilla JS + CSS transitions, Shadow DOM for style
  isolation, 1920×1080 transparent stage, title-safe positioning)

Copy them into a working folder (e.g. `/home/claude/<graphic-id>/`) and adapt:
- Set `id` (reverse-domain, unique), `name`, `version`, `author`.
- Define the `schema` to match the editable fields, each with a `default`. The property
  keys are exactly what the component reads from `params.data`.
- If a brand kit is in play, apply its tokens (colours, fonts, safe-area, motion) as the
  component's CSS variables and defaults, and stamp provenance in the manifest with a
  `v_brand` field. See `references/brand-kit.md`.
- Build the DOM/CSS and the in/out/update animations in the component.

**Default to dependency-free** (CSS transitions or the Web Animations API). It makes
the graphic fully self-contained and portable — nothing extra to ship. Only reach for
a library (e.g. GSAP, bundled locally as resources) if the user asks or the motion
genuinely needs it. If `supportsNonRealTime: true`, you MUST implement `goToTime()`
and `setActionsSchedule()` from a deterministic timeline — see the interface reference.

### 3. Validate (required gate)

```bash
pip install jsonschema --break-system-packages -q   # first run only
python3 scripts/validate_ograf.py /home/claude/<graphic-id>
```

This checks, fully offline, against the bundled EBU schema set:
- manifest filename ends with `.ograf.json`;
- manifest validates against the graphics JSON Schema (incl. GDD data model + actions);
- the `main` JS file exists;
- the component has a `default export`, extends `HTMLElement`, and implements every
  required method (plus `goToTime`/`setActionsSchedule` when non-realtime).

Fix every reported issue and re-run until it passes. The messages point at the exact
field or method.

### 4. Package and deliver

```bash
python3 scripts/validate_ograf.py /home/claude/<graphic-id> --package /mnt/user-data/outputs/<graphic-id>.zip
```

`--package` only writes the zip if validation passes. Then present both the zip and
the individual files (manifest + JS) so the user can review the source. Briefly tell
them what the graphic does, its editable fields, and how to load it (any OGraf
renderer, e.g. the EBU "OGraf Simple Rendering System", or an OGraf-compatible editor).

## Broadcast conventions (sensible defaults)

- **Stage**: 1920×1080, **transparent background** — graphics composite over video.
- **Title-safe**: keep content within ~5% inset from each edge so it isn't cropped.
- **Type**: large and legible (names ~48–60px, supporting text ~28–36px at 1080p);
  high contrast; avoid hairline strokes and pure-saturated reds that bleed on broadcast.
- **Motion**: quick, eased in/out (≈0.3–0.8s); resolve action Promises when the
  animation settles so the renderer can sequence reliably.
- **Isolation**: use Shadow DOM (as the template does) so renderer page styles can't
  leak in.

## Brand kits

A **brand kit** is a small JSON file the user keeps and reuses so every graphic they
make shares one look — palette, fonts, logo, safe-area, motion timing, corner radius.
It is *not* part of the OGraf spec; it's a convention this skill uses to keep a user's
graphics consistent.

How to use it:
- **At intake**, ask whether the user has a kit. If they upload one, build from it. If
  they mention one from past work, search past conversations to recover it. If they want
  consistency but have none, offer to create one from `assets/templates/brand-kit.json`
  and hand it back so they can keep it.
- **When building**, derive the component's CSS variables and field defaults from the
  kit instead of inventing values, and record which kit/version was used in the manifest
  via `v_brand`.
- **Before delivering**, run the consistency check (advisory):
  ```bash
  python3 scripts/check_brand.py /home/claude/<graphic-id> path/to/brand-kit.json
  ```
  It flags colours/fonts in the component that fall outside the kit, and confirms the
  `v_brand` stamp matches. Warnings don't block delivery, but resolve them unless there's
  a reason to deviate.

Because each conversation starts fresh, the kit lives with the user — they keep the file
and provide it for each build. Full structure and application rules: `references/brand-kit.md`.

## Critical spec rules (easy to get wrong)

- The manifest filename **must** end with `.ograf.json`.
- `$schema` **must** be the exact constant string; any other value fails validation.
- The manifest is **strict** — unknown top-level fields fail. Vendor fields must be
  prefixed `v_`.
- A graphic must support realtime, non-realtime, or both. Non-realtime obliges the two
  extra methods.
- Don't paint pixels before `load()` is called.
- **Schema drift**: the bundled schema (matching EBU's repo and examples) is newer than
  the live `$schema` URL and allows `actionDurations`/`thumbnails`; the live URL does
  not yet. For maximum portability, avoid those two unless asked. Details in
  `references/manifest-spec.md`.

## Reference files

- `references/manifest-spec.md` — every manifest field, the GDD data model and field
  types, step model, custom actions, render requirements, and the schema-drift detail.
- `references/component-interface.md` — every lifecycle/action method, signatures,
  return payloads, step targeting math, non-realtime methods, and animation timing.
- `references/brand-kit.md` — brand-kit structure, how to apply tokens, and provenance.
- `assets/schemas/` — the bundled EBU JSON Schema set used for offline validation.
- `assets/templates/` — the starting manifest, dependency-free component, and
  `brand-kit.json` template.
- `scripts/validate_ograf.py` — the validation + packaging gate.
- `scripts/check_brand.py` — advisory brand-consistency check against a kit.
