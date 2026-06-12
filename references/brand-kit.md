# Brand Kits

A brand kit keeps a user's graphics visually consistent. It is a convention of this
skill, **not** part of the OGraf spec — renderers never see it. It only influences the
values you bake into a graphic at build time.

## Structure

See `assets/templates/brand-kit.json`. Fields:

| Field | Purpose |
|---|---|
| `id`, `name`, `version` | Identify the kit. Bump `version` when the look changes. |
| `colors` | Named palette: `accent`, `accentText`, `panel`, `panelText`, `muted`. Add more as needed. Hex `#rrggbb`. |
| `fonts` | `primary` font stack + `weightRegular` / `weightBold`. |
| `logo` | Path to a logo asset to bundle into graphics that need it. |
| `safeArea` | `insetX` / `insetY` in px — where content starts from the frame edge. |
| `motion` | `inMs`, `outMs`, `ease` — shared animation timing so graphics feel related. |
| `cornerRadius` | Default corner radius in px. |

A kit may carry extra fields; ignore ones you don't use.

## Applying a kit when building

1. **Map colours and fonts to CSS variables** at the top of `:host`, so the whole
   component reads from one place:
   ```css
   :host {
     --accent: #e10600; --accent-text: #fff;
     --panel: #0b0c10; --panel-text: #fff; --muted: #9aa0a6;
     --font: Arial, "Helvetica Neue", sans-serif;
     --radius: 6px; --ease: cubic-bezier(.16,1,.3,1);
   }
   ```
   Fill these from the kit. Use the variables everywhere instead of literal values.
2. **Use the kit's motion** (`inMs`/`outMs`/`ease`) for entrance/exit transitions, and
   the kit's `safeArea` for positioning, so every graphic moves and sits consistently.
3. **Seed field defaults** from the kit where it makes sense (e.g. an `accent` field
   defaults to the kit accent), keeping the self-default rule.
4. **Bundle the logo** into the graphic folder if the design uses it.
5. **Stamp provenance** in the manifest so a graphic records the look it follows:
   ```json
   "v_brand": { "id": "com.acme.brand", "version": "1.0.0" }
   ```
   `v_`-prefixed fields are allowed by the OGraf manifest schema and ignored by renderers.

## Persistence and reuse

Each conversation starts fresh, so the kit lives with the user, not the skill:
- Ask them to upload the kit at the start of a build; apply it; hand any updates back.
- If they created a kit in an earlier conversation, search past chats to recover it.
- If they have no kit but want consistency, generate one from the template, use it for
  this graphic, and give them the file to keep for next time.

## Checking consistency

`scripts/check_brand.py <graphic-folder> <brand-kit.json>` is advisory. It:
- scans the component for hex colours and flags any not in the kit palette;
- flags font stacks that don't match the kit's `primary`;
- confirms the manifest's `v_brand` matches the kit's `id`/`version`.

Warnings don't block delivery — sometimes a one-off colour is intentional — but resolve
them unless you have a reason to deviate.
