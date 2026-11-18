/* Static portfolio. No external requests, analytics, cookies or local storage. */
(() => {
  "use strict";
  const buttons = [...document.querySelectorAll("[data-filter]")];
  const cards = [...document.querySelectorAll("[data-project]")];
  const count = document.querySelector("#visible-count");
  const category = (card, filter) => filter === "all" || (card.dataset.tags || "").split(/\s+/).includes(filter);

  function applyFilter(filter) {
    let total = 0;
    for (const card of cards) {
      const visible = category(card, filter);
      card.hidden = !visible;
      if (visible) total += 1;
    }
    const featuredLabel = document.querySelector("#featured-group-label");
    const archiveLabel = document.querySelector("#archive-group-label");
    if (featuredLabel) featuredLabel.hidden = !cards.some(card => card.classList.contains("featured") && !card.hidden);
    if (archiveLabel) archiveLabel.hidden = !cards.some(card => !card.classList.contains("featured") && !card.classList.contains("is-locked") && !card.classList.contains("is-physical") && !card.hidden);
    const physicalLabel = document.querySelector("#physical-group-label");
    if (physicalLabel) physicalLabel.hidden = !cards.some(card => card.classList.contains("is-physical") && !card.hidden);
    const lockedLabel = document.querySelector("#locked-group-label");
    if (lockedLabel) lockedLabel.hidden = !cards.some(card => card.classList.contains("is-locked") && !card.hidden);
    for (const button of buttons) {
      const active = button.dataset.filter === filter;
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", String(active));
    }
    if (count) count.textContent = String(total).padStart(2, "0");
  }
  for (const button of buttons) {
    button.addEventListener("click", () => applyFilter(button.dataset.filter || "all"));
  }
  applyFilter("all");


  // Lightweight, accessible work sheets. Content is derived solely from visible public cards.
  const dialog = document.getElementById("project-sheet");
  if (dialog && typeof dialog.showModal === "function") {
    const sheetTitle = document.getElementById("sheet-title");
    const sheetDescription = document.getElementById("sheet-description");
    const sheetExtra = document.getElementById("sheet-extra");
    const sheetKind = document.getElementById("sheet-kind");
    const sheetTags = document.getElementById("sheet-tags");
    const sheetVisual = document.getElementById("sheet-visual");
    const sheetVisualBottom = dialog.querySelector(".sheet-visual-bottom");
    const sheetVisualBrand = sheetVisualBottom?.lastElementChild;
    const motionButton = document.createElement("button");
    motionButton.type = "button";
    motionButton.className = "sheet-motion-play";
    motionButton.textContent = "REPLAY";
    motionButton.setAttribute("aria-label", "作品アニメーションを再生");
    motionButton.hidden = true;
    // Keep replay in the image panel's bottom-right caption row, not over the art.
    sheetVisualBottom?.appendChild(motionButton);
    const sheetCopySide = dialog.querySelector(".sheet-copy-side");
    const sheetActions = document.getElementById("sheet-actions");
    const sheetCounter = document.getElementById("sheet-counter");
    const sheetPosition = document.getElementById("sheet-position");
    const sheetVisualIndex = document.getElementById("sheet-visual-index");
    const closeButton = document.getElementById("sheet-close");
    const prevButton = document.getElementById("sheet-prev");
    const nextButton = document.getElementById("sheet-next");
    let activeCard = null;
    let lastOpener = null;
    let motionTimer = null;
    // One-shot concept motions: each source card is cloned into its work sheet.
    const motions = {
      "diy-equatorial-mount": {
        selector: ".art-eqmount", duration: 6400,
        finishAnimation: "eq-target-acquire", finishTarget: "eq-target-field"
      },
      sorava: {
        selector: ".art-sorava", duration: 7200,
        finishAnimation: "sorava-guest-receive", finishTarget: "sorava-guest-received"
      },
      "wallpipe-ar": {
        selector: ".art-wallpipe", duration: 7200, loop: true
      }
    };
    const activeMotion = () => motions[activeCard?.dataset.sheetId] || null;
    const motionAllowed = () => !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    function resetSheetMotion() {
      if (motionTimer !== null) {
        window.clearTimeout(motionTimer);
        motionTimer = null;
      }
      for (const art of sheetVisual.querySelectorAll(".art-eqmount, .art-sorava, .art-wallpipe")) {
        art.classList.remove("is-playing", "is-hovering", "is-complete");
      }
    }
    function finishSheetMotion(art) {
      if (!art?.classList.contains("is-playing")) return;
      // A completed CSS motion is authoritative; preserve the final visual pose.
      art.classList.add("is-complete");
      art.classList.remove("is-playing");
      if (motionTimer !== null) {
        window.clearTimeout(motionTimer);
        motionTimer = null;
      }
    }
    function playSheetMotion() {
      const motion = activeMotion();
      const art = motion && sheetVisual.querySelector(motion.selector);
      if (!dialog.open || !art || !motionAllowed()) return;
      resetSheetMotion();
      // Restart exactly one cycle even when replaying the same open sheet.
      void art.getBoundingClientRect().width;
      art.classList.add("is-playing");
      // Safety fallback if the browser suppresses animationend (e.g. hidden tab).
      if (!motion.loop) motionTimer = window.setTimeout(() => finishSheetMotion(art), motion.duration + 250);
    }
    motionButton.addEventListener("click", playSheetMotion);
    // On listing cards, hover starts a single cycle even with the transparent
    // sheet-opening button above the image. In work sheets it autoplays instead.
    const listingArts = [];
    for (const [id, motion] of Object.entries(motions)) {
      const media = document.querySelector(`.project-card[data-sheet-id="${id}"] .project-media`);
      const art = media?.querySelector(motion.selector);
      if (!media || !art) continue;
      listingArts.push(art);
      media.addEventListener("pointerenter", event => {
        if (event.pointerType === "mouse" && motionAllowed() &&
            window.matchMedia("(hover:hover) and (pointer:fine)").matches) {
          art.classList.remove("is-complete");
          art.classList.add("is-hovering");
        }
      });
      media.addEventListener("pointerleave", () => {
        art.classList.remove("is-hovering", "is-complete");
      });
    }
    const eligible = () => cards.filter(card => !card.hidden && card.querySelector("[data-open-sheet]"));

    function openSheet(card, trigger) {
      if (!card || !card.querySelector("[data-open-sheet]")) return;
      resetSheetMotion();
      for (const listingArt of listingArts) {
        listingArt.classList.remove("is-hovering", "is-complete");
      }
      if (!dialog.open && trigger instanceof HTMLElement) lastOpener = trigger;
      const selection = eligible();
      const current = selection.indexOf(card);
      if (current < 0) return;
      activeCard = card;
      dialog.dataset.theme = card.dataset.sheetId || "";
      sheetTitle.textContent = card.querySelector(".project-info h3")?.textContent?.trim() || "";
      const details = card.querySelector("template.project-sheet-detail");
      sheetDescription.textContent = card.querySelector(".project-info > p")?.textContent?.trim() || "";
      sheetDescription.hidden = Boolean(details);
      sheetExtra.replaceChildren();
      if (details) sheetExtra.appendChild(details.content.cloneNode(true));
      sheetExtra.hidden = !details;
      sheetKind.textContent = card.querySelector(".project-year")?.textContent?.trim() || "PROJECT";
      const number = card.dataset.project || String(current + 1).padStart(2, "0");
      sheetCounter.textContent = "PROJECT / " + number.padStart(3, "0");
      const position = String(current + 1).padStart(2, "0") + " / " + String(selection.length).padStart(2, "0");
      sheetPosition.textContent = position;
      sheetVisualIndex.textContent = position;
      const art = card.querySelector(".project-art")?.cloneNode(true);
      if (art) {
        const motion = motions[card.dataset.sheetId];
        if (motion && !motion.loop) {
          art.addEventListener("animationend", event => {
            if (event.animationName === motion.finishAnimation &&
                event.target.classList.contains(motion.finishTarget)) {
              finishSheetMotion(art);
            }
          });
          // Work sheets never depend on pointer position.
          // Direct opening and NEXT/PREV both initiate one full cycle.
        }
        // SVG identifiers must be unique when the original art remains in the listing.
        for (const node of art.querySelectorAll("[id]")) {
          const original = node.id;
          const replacement = "sheet-" + original;
          for (const element of art.querySelectorAll("*")) {
            for (const attr of element.attributes) {
              if (attr.value.includes("url(#" + original + ")")) {
                element.setAttribute(attr.name, attr.value.replaceAll("url(#" + original + ")", "url(#" + replacement + ")"));
              }
            }
          }
          node.id = replacement;
        }
        sheetVisual.replaceChildren(art);
      } else {
        sheetVisual.replaceChildren();
      }
      const showMotion = Boolean(motions[card.dataset.sheetId]) && motionAllowed();
      motionButton.hidden = !showMotion;
      motionButton.textContent = motions[card.dataset.sheetId]?.loop ? "RESTART" : "REPLAY";
      motionButton.setAttribute("aria-label", `${sheetTitle.textContent} のアニメーションを再生`);
      if (sheetVisualBrand) sheetVisualBrand.hidden = showMotion;
      // Each sheet starts at the beginning of its own right-side content.
      if (sheetCopySide) sheetCopySide.scrollTop = 0;
      sheetTags.replaceChildren(...[...card.querySelectorAll(".tag-row span")].map(tag => tag.cloneNode(true)));
      const live = card.querySelector(".project-links a[href]");
      sheetActions.replaceChildren();
      if (live) {
        const link = live.cloneNode(true);
        link.textContent = "Open live site ↗";
        sheetActions.append(link);
      }
      prevButton.disabled = selection.length < 2;
      nextButton.disabled = selection.length < 2;
      if (!dialog.open) dialog.showModal();
      closeButton.focus();
      // Play exactly once when an animated sheet opens, including navigation
      // from another sheet. Static artwork stays static; reduced-motion is honored.
      if (showMotion) {
        requestAnimationFrame(() => {
          if (dialog.open && activeCard === card) playSheetMotion();
        });
      }
    }

    function moveSheet(direction) {
      const selection = eligible();
      if (!activeCard || selection.length < 2) return;
      const index = selection.indexOf(activeCard);
      if (index === -1) return;
      openSheet(selection[(index + direction + selection.length) % selection.length]);
    }

    for (const card of cards) {
      for (const trigger of card.querySelectorAll("[data-open-sheet]")) {
        trigger.addEventListener("click", () => openSheet(card, trigger));
      }
    }
    closeButton.addEventListener("click", () => dialog.close());
    prevButton.addEventListener("click", () => moveSheet(-1));
    nextButton.addEventListener("click", () => moveSheet(1));
    dialog.addEventListener("click", event => {
      if (event.target === dialog) dialog.close();
    });
    dialog.addEventListener("close", () => {
      resetSheetMotion();
      activeCard = null;
      if (lastOpener?.isConnected && !lastOpener.closest("[hidden]")) lastOpener.focus();
      lastOpener = null;
    });
    document.addEventListener("keydown", event => {
      if (!dialog.open || event.altKey || event.ctrlKey || event.metaKey) return;
      if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
        event.preventDefault();
        moveSheet(event.key === "ArrowLeft" ? -1 : 1);
      }
    });
  }
  const year = document.querySelector("#footer-year");
  if (year) year.textContent = String(new Date().getFullYear());
})();
