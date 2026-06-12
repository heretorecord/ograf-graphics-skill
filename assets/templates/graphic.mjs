/**
 * OGraf Graphic — dependency-free template.
 *
 * This is a complete, valid OGraf v1 Web Component with NO external libraries.
 * Animation is done with CSS transitions; data binding is plain DOM.
 * Replace the marked sections to build a specific graphic.
 *
 * Interface reference: references/component-interface.md
 *
 * @typedef {Object} LoadParams
 * @property {unknown} data
 * @property {"realtime"|"non-realtime"} renderType
 * @property {Object} renderCharacteristics
 */
class Graphic extends HTMLElement {
  constructor() {
    super();
    // Shadow DOM keeps the graphic's CSS isolated from the renderer's page styles.
    this.root = this.attachShadow({ mode: "open" });
    this.state = {}; // current data (the public state model in manifest.schema)
    this.isVisible = false;
  }

  /**
   * Called once when the Renderer has loaded the Graphic into the DOM.
   * Build the DOM/CSS here and apply initial data — but stay hidden until playAction().
   * @param {LoadParams} params
   */
  async load(params) {
    if (params.renderType !== "realtime") {
      // This template only supports realtime. For non-realtime support, see
      // references/component-interface.md and set supportsNonRealTime:true in the manifest.
      throw new Error("Only realtime rendering is supported by this graphic");
    }

    // ---- DOM + styles -----------------------------------------------------
    // The 1920x1080 stage with a transparent background is the broadcast convention.
    // Position content inside the title-safe area (~5% inset) so it isn't cropped.
    this.root.innerHTML = `
      <style>
        :host {
          position: absolute;
          inset: 0;
          width: 1920px;
          height: 1080px;
          overflow: hidden;
          /* No background — broadcast graphics composite over video. */
          font-family: "Arial", "Helvetica Neue", sans-serif;
        }
        .lower-third {
          position: absolute;
          left: 96px;            /* 5% title-safe inset */
          bottom: 108px;         /* ~10% from the bottom */
          padding: 16px 32px;
          background: #c8102e;   /* broadcast-safe red */
          color: #ffffff;
          border-radius: 4px;
          /* Animate in from the left + fade. */
          transform: translateX(-40px);
          opacity: 0;
          transition: transform 600ms cubic-bezier(.22,1,.36,1), opacity 400ms ease;
        }
        :host(.visible) .lower-third { transform: translateX(0); opacity: 1; }
        .name  { font-size: 56px; font-weight: 700; line-height: 1.1; }
        .title { font-size: 32px; font-weight: 400; opacity: .9; margin-top: 4px; }
      </style>
      <div class="lower-third" part="container">
        <div class="name"></div>
        <div class="title"></div>
      </div>
    `;
    this.els = {
      name: this.root.querySelector(".name"),
      title: this.root.querySelector(".title"),
    };

    // Apply initial data without animating.
    this._applyData(params.data || {});
    return { statusCode: 200 };
  }

  /** Renderer is removing the Graphic — release everything. */
  async dispose() {
    this.root.innerHTML = "";
    this.els = null;
    return { statusCode: 200 };
  }

  /**
   * Animate the Graphic IN (and step through, for multi-step graphics).
   * This single-step template just reveals the content.
   */
  async playAction(params) {
    this.classList.add("visible");
    this.isVisible = true;
    await this._waitForTransition(this.root.querySelector(".lower-third"));
    // stepCount is 1 here, so transitioning past the only step goes to the end -> undefined.
    return { statusCode: 200, currentStep: undefined };
  }

  /** Animate the Graphic OUT. */
  async stopAction(params) {
    this.classList.remove("visible");
    this.isVisible = false;
    await this._waitForTransition(this.root.querySelector(".lower-third"));
    return { statusCode: 200 };
  }

  /** Update the data while on air (e.g. correct a name). */
  async updateAction(params) {
    this._applyData(params.data || {});
    return { statusCode: 200 };
  }

  /** No custom actions in this template. */
  async customAction(params) {
    return { statusCode: 400, statusMessage: `No custom action "${params.id}"` };
  }

  // ---- helpers ------------------------------------------------------------
  _applyData(data) {
    this.state = { ...this.state, ...data };
    if (!this.els) return;
    if (this.state.name != null) this.els.name.textContent = this.state.name;
    if (this.state.title != null) this.els.title.textContent = this.state.title;
  }

  _waitForTransition(el) {
    return new Promise((resolve) => {
      let done = false;
      const finish = () => { if (!done) { done = true; resolve(); } };
      el.addEventListener("transitionend", finish, { once: true });
      // Safety timeout in case no transition fires.
      setTimeout(finish, 800);
    });
  }
}

export default Graphic;
