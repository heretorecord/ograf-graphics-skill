# OGraf Web Component Interface (v1)

The `main` JS file MUST `export default` a `class` that `extends HTMLElement`.
The Renderer instantiates it as a custom element, calls `load()`, waits for the
returned Promise, then drives it with action methods, and finally `dispose()`.

All action methods return `Promise<ReturnPayload | undefined>`. A resolved
`undefined` is treated as `{ statusCode: 200 }`. `ReturnPayload` fields:
`statusCode` (HTTP-like; 2xx ok, 4xx/5xx error), optional `statusMessage`,
optional `result`.

## Required methods (all graphics)

### `load({ data, renderType, renderCharacteristics })`
Called once after the element is in the DOM. Build DOM/CSS, load resources, apply
initial `data`. **Do not paint until `load()`** — not in the constructor or
`connectedCallback()`. Resolve when ready to receive actions. This enables
load-and-play: `load({data}).then(() => playAction())`. Throw if `renderType` is
unsupported.

### `dispose()`
Tear down: clear DOM, free resources, cancel timers/animations. Resolve when done.

### `playAction({ goto?, delta?, skipAnimation? })`
Animate in / advance steps. Target step:
- `goto` given and ≥ 0 → that absolute step.
- otherwise → current step + `delta` (delta defaults to 1; from the start state,
  current is treated as -1, so `delta:1` → step 0).
- target ≥ `stepCount` → transition to the **end**.

Resolve to `{ statusCode, currentStep }`. `currentStep` is the step after this call,
or `undefined` when at the end / for `stepCount: 0`. For long/looping animations,
resolve early (after the in-animation) rather than waiting for the loop.

### `stopAction({ skipAnimation? })`
Animate out / go to the end. Resolve when no longer displayed.

### `updateAction({ data, skipAnimation? })`
Apply a (possibly partial) data update to the live graphic. Merge into current state.

### `customAction({ id, payload, skipAnimation? })`
Run a graphic-specific action whose `id` matches one in the manifest's
`customActions`. Return a 4xx payload for unknown ids.

`skipAnimation` defaults to `false`; when `true` the method MUST jump to the end
state with no animation. Methods may be called before a previous call's Promise
resolves — queue, abort, or skip ahead, but don't silently ignore them.

## Additional methods (only if `supportsNonRealTime: true`)

### `goToTime({ timestamp })`
Jump to `timestamp` (ms) and render that frame. Resolve when the frame is ready.

### `setActionsSchedule({ schedule })`
`schedule` is an array of `{ timestamp, action }`, where `action.type` is one of
`playAction`/`stopAction`/`updateAction`/`customAction` with matching `params`.
Store the schedule and play it deterministically against `goToTime()`. Replaces any
previous schedule. Resolve on receipt (don't wait for execution).

For non-realtime, drive everything from a deterministic timeline so any frame can be
rendered from `(initial data + schedule + timestamp)` alone — never from wall-clock
time. (A library like GSAP with a paused timeline + `seek()` is one way; a pure
function of `timestamp` is another.)

## Skeleton

```js
class Graphic extends HTMLElement {
  constructor() { super(); this.root = this.attachShadow({ mode: "open" }); }
  async load({ data, renderType }) { /* build DOM, apply data */ return { statusCode: 200 }; }
  async dispose() { this.root.innerHTML = ""; return { statusCode: 200 }; }
  async playAction(p) { /* animate in */ return { statusCode: 200, currentStep: undefined }; }
  async stopAction(p) { /* animate out */ return { statusCode: 200 }; }
  async updateAction({ data }) { /* merge + reflect */ return { statusCode: 200 }; }
  async customAction({ id }) { return { statusCode: 400, statusMessage: `No action ${id}` }; }
}
export default Graphic;
```

## Animation timing

Resolve action Promises when the graphic is *ready for the next action* — generally
when the in/out animation finishes. With CSS transitions, await `transitionend`
(with a safety timeout). With the Web Animations API, await `animation.finished`.
Keep state in JS so `updateAction()` mid-animation stays consistent.
