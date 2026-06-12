# OGraf Manifest Reference (v1)

The manifest is a JSON file whose name **must** end with `.ograf.json`. It is the
entry point for the Graphic; everything else is referenced from it.

## Required fields

| Field | Type | Notes |
|---|---|---|
| `$schema` | string | MUST be exactly `https://ograf.ebu.io/v1/specification/json-schemas/graphics/schema.json`. This doubles as the OGraf version marker. |
| `id` | string | Unique. No `/`. Reverse-domain notation recommended, e.g. `com.acme.lower-third`. |
| `name` | string | Display name. |
| `main` | string | Path to the JS file exporting the Web Component, relative to the manifest. |
| `supportsRealTime` | boolean | Live/real-time rendering. |
| `supportsNonRealTime` | boolean | Post-production rendering. If `true`, the JS MUST implement `goToTime()` and `setActionsSchedule()`. A Graphic MUST support at least one of the two modes. |

## Optional fields

| Field | Type | Notes |
|---|---|---|
| `version` | string | Should be alphabetically sortable, e.g. `1.0.0`. |
| `description` | string | Longer description. |
| `author` | object | MUST contain `name`; MAY contain `email`, `url`. No other keys (except `v_*`). |
| `schema` | object (GDD) | The public state model — the shape of `data` passed to `load()`/`updateAction()`. See below. |
| `customActions` | Action[] | Each needs `id` + `name`; optional `description` and `schema` (or `schema: null`). |
| `stepCount` | integer ≥ -1 | See step model. Default 1. |
| `renderRequirements` | object[] | At least one must be met. Keys: `resolution.width/height`, `frameRate`, `accessToPublicInternet`. |
| `actionDurations` | object[] | Static animation durations in ms. (See schema-drift note.) |
| `thumbnails` | object[] | `file` + optional `resolution`. (See schema-drift note.) |

Any vendor-specific field MUST be prefixed `v_` (e.g. `v_editor`). The schema is
strict (`additionalProperties: false`): unknown top-level fields fail validation.

## Schema-drift note (important)

The **published** schema at the `$schema` URL currently lags the EBU repo's `main`
branch. The repo (and the bundled copy this skill validates against) includes
`actionDurations`, `thumbnails`, `engine` requirements, and GDD `hidden`/`order` —
the live URL does not yet.

Consequence: a manifest using `actionDurations`/`thumbnails` validates against the
bundled (current) schema and the official examples, but a tool dereferencing the
**live** URL may reject it. For maximum portability across renderers today, prefer
the required fields plus `schema`/`version`/`author`/`stepCount`, and only add
`actionDurations`/`thumbnails` when the user asks or the target renderer supports them.

## The `schema` (GDD) data model

`schema` is a JSON-Schema-style object describing the Graphic's editable data.
Each property has a `type` (`string`/`number`/`integer`/`boolean`/`array`/`object`)
and may include `title`, `default`, `gddType` (e.g. `color-rrggbb`), `pattern`,
`hidden` (omit from GUI labels), and `order` (UI sort). Example:

```json
"schema": {
  "type": "object",
  "properties": {
    "headline": { "type": "string", "title": "Headline", "default": "Breaking News" },
    "color":    { "type": "string", "gddType": "color-rrggbb", "pattern": "^#[0-9a-f]{6}$", "default": "#c8102e" }
  }
}
```

The keys here are exactly the fields your Web Component reads from `params.data`.

### Field types (what to expose for editing)

When you ask the user which fields to expose, map each to a GDD property:

| You want | `type` | Extra |
|---|---|---|
| Single-line text | `string` | `default` |
| Multi-line text | `string` | `gddType: "multi-line"` |
| Number (decimals) | `number` | `default`, optional `min`/`max` |
| Whole number | `integer` | `default` |
| On/off toggle | `boolean` | `default` |
| Colour | `string` | `gddType: "color-rrggbb"`, `pattern: "^#[0-9a-f]{6}$"` |
| Image / file path | `string` | `gddType: "single-line"`; component resolves path or URL |
| Fixed set of choices | `string` | `enum: ["a","b","c"]`, `default` |
| Repeating rows (e.g. a list) | `array` | `items: { type: "object", properties: {…} }` |

Give every property a `title` (the GUI label) and a `default`. Use `order` to control
GUI ordering and `hidden: true` for values you compute but don't want operators editing.
Expose only what an operator realistically changes; bake everything else into the component.

## Step model (`stepCount`)

| `stepCount` | Meaning |
|---|---|
| `0` | No steps — plays in, then auto-animates out. |
| `1` or `undefined` | One paused state; `playAction()` reveals, `stopAction()` ends. |
| `>1` | Multiple steps; call `playAction()` to advance between them. |
| `-1` | Dynamic/unknown step count. |

Steps are zero-based. When the target step ≥ `stepCount`, transition to the end
(report `currentStep: undefined`).

## Multiple graphics in one package

A folder MAY contain several `*.ograf.json` files; each is an independent Graphic.
Useful when graphics share resources (fonts, images).
