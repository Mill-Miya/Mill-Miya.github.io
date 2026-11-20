/* Static portfolio. Appearance preferences stay in this browser. */
(() => {
  "use strict";
  const buttons = [...document.querySelectorAll("[data-filter]")];
  const cards = [...document.querySelectorAll("[data-project]")];
  const count = document.querySelector("#visible-count");
  const countUnit = document.querySelector("#project-count-unit");
  const grid = document.querySelector("#project-grid");
  const conceptEntry = document.querySelector("#concept-archive-entry");
  const category = (card, filter) => filter === "all" || (card.dataset.tags || "").split(/\s+/).includes(filter);

  function applyFilter(filter) {
    let total = 0;
    for (const card of cards) {
      const visible = category(card, filter);
      card.hidden = !visible;
      if (visible) total += 1;
    }
    // The concept archive is an optional appendix, not a work card.
    if (conceptEntry) conceptEntry.hidden = filter !== "all";
    const featuredLabel = document.querySelector("#featured-group-label");
    const archiveLabel = document.querySelector("#archive-group-label");
    if (featuredLabel) featuredLabel.hidden = !cards.some(card => card.classList.contains("featured") && !card.hidden);
    if (archiveLabel) archiveLabel.hidden = !cards.some(card => !card.classList.contains("featured") && !card.classList.contains("is-locked") && !card.classList.contains("is-physical") && !card.hidden);
    const physicalLabel = document.querySelector("#physical-group-label");
    if (physicalLabel) physicalLabel.hidden = !cards.some(card => card.classList.contains("is-physical") && !card.hidden);
    const lockedLabel = document.querySelector("#locked-group-label");
    if (lockedLabel) lockedLabel.hidden = !cards.some(card => card.classList.contains("is-locked") && !card.hidden);
    // Section numbers identify the three chapters; project counts are separate
    // and reflect the currently active filter.
    const visibleGroupCount = predicate => cards.filter(card => !card.hidden && predicate(card)).length;
    for (const [label, quantity] of [
      [featuredLabel, visibleGroupCount(card => card.classList.contains("featured"))],
      [archiveLabel, visibleGroupCount(card => !card.classList.contains("featured") && !card.classList.contains("is-physical"))],
      [physicalLabel, visibleGroupCount(card => card.classList.contains("is-physical"))]
    ]) {
      const counter = label?.querySelector("[data-group-count]");
      if (counter) counter.textContent = String(quantity).padStart(2, "0") + (quantity === 1 ? " PROJECT" : " PROJECTS");
    }
    for (const button of buttons) {
      const active = button.dataset.filter === filter;
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", String(active));
    }
    if (count) count.textContent = String(total).padStart(2, "0");
    if (countUnit) countUnit.textContent = total === 1 ? "PROJECT" : "PROJECTS";
    grid?.classList.toggle("is-single-project", total === 1);
  }
  for (const button of buttons) {
    button.addEventListener("click", () => applyFilter(button.dataset.filter || "all"));
  }
  applyFilter("all");

  const logoFrame = document.getElementById("hero-logo-frame");
  const logoReplay = document.getElementById("hero-logo-replay");
  const root = document.documentElement;
  const systemMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const motionAllowed = () => root.dataset.motionChoice === "full" ||
    (!systemMotion.matches && root.dataset.motionChoice !== "reduce");
  const themeChoice = document.getElementById("theme-choice");
  const motionChoice = document.getElementById("motion-choice");
  const systemTheme = window.matchMedia("(prefers-color-scheme: dark)");
  const themeColor = document.querySelector('meta[name="theme-color"]');

  const headerTheme = document.querySelector(".header-theme");
  const themeButtons = [...document.querySelectorAll("[data-header-theme]")];

  // Cycle only the site-wide editorial accent. Never override project color identities.
  const accentCycle = document.getElementById("accent-cycle");
  const accentAnnouncement = document.getElementById("accent-announcement");
  const accentOptions = [
    { key: "blue", name: "Sky Blue" },
    { key: "sage", name: "Sage Green" },
    { key: "copper", name: "Copper" },
    { key: "violet", name: "Violet" }
  ];
  function syncAccentLabel() {
    const current = root.dataset.accentChoice || "blue";
    const index = Math.max(0, accentOptions.findIndex(item => item.key === current));
    const next = accentOptions[(index + 1) % accentOptions.length];
    accentCycle?.setAttribute("aria-label",
      "Change accent color. Current: " + accentOptions[index].name + ". Next: " + next.name + ".");
    if (accentCycle) accentCycle.title = "Accent: " + accentOptions[index].name + " — click to change";
  }
  accentCycle?.addEventListener("click", () => {
    const current = root.dataset.accentChoice || "blue";
    const index = Math.max(0, accentOptions.findIndex(item => item.key === current));
    const next = accentOptions[(index + 1) % accentOptions.length];
    if (next.key === "blue") delete root.dataset.accentChoice;
    else root.dataset.accentChoice = next.key;
    try {
      if (next.key === "blue") localStorage.removeItem("mill-miya.accent");
      else localStorage.setItem("mill-miya.accent", next.key);
    } catch {
      // The current view still changes when storage is unavailable.
    }
    syncAccentLabel();
    if (accentAnnouncement) accentAnnouncement.textContent = "Accent color: " + next.name;
  });
  syncAccentLabel();

  function savePreference(attribute, storageKey, value) {
    if (value === "system") delete root.dataset[attribute];
    else root.dataset[attribute] = value;
    try {
      if (value === "system") localStorage.removeItem(storageKey);
      else localStorage.setItem(storageKey, value);
    } catch {
      // The current view still updates when storage is unavailable.
    }
  }

  function syncTheme() {
    const choice = root.dataset.themeChoice || "system";
    const effectiveTheme = choice === "system" ? (systemTheme.matches ? "dark" : "light") : choice;
    if (themeChoice) themeChoice.value = choice;
    for (const button of themeButtons) {
      button.setAttribute("aria-pressed", String(button.dataset.headerTheme === effectiveTheme));
    }
    if (themeColor) themeColor.content = getComputedStyle(document.body).backgroundColor;
    logoFrame?.contentWindow?.postMessage({
      channel: "mill-miya-r-logo", type: "theme", theme: effectiveTheme
    }, "*");
  }

  function setTheme(choice) {
    savePreference("themeChoice", "mill-miya.theme", choice);
    syncTheme();
  }

  for (const button of themeButtons) {
    button.addEventListener("click", () => setTheme(button.dataset.headerTheme));
  }
  themeChoice?.addEventListener("change", () => setTheme(themeChoice.value));
  if (motionChoice) {
    motionChoice.value = root.dataset.motionChoice || "system";
    motionChoice.addEventListener("change", () => {
      savePreference("motionChoice", "mill-miya.motion", motionChoice.value);
    });
  }
  if (themeChoice && motionChoice) document.querySelector(".site-preferences").hidden = false;
  systemTheme.addEventListener("change", syncTheme);
  syncTheme();
  if (headerTheme) headerTheme.hidden = false;

  function requestMotion() {
    if (motionAllowed()) return;
    savePreference("motionChoice", "mill-miya.motion", "full");
    if (motionChoice) {
      motionChoice.value = "full";
      motionChoice.dispatchEvent(new Event("change"));
    }
  }

  if (logoFrame && logoReplay) {
    const logoPanel = logoFrame.closest(".hero-visual");
    const channel = "mill-miya-r-logo";
    const sendLogoMessage = type => logoFrame.contentWindow?.postMessage({ channel, type }, "*");
    const spinTrigger = document.getElementById("hero-logo-spin");
    const spinCanvas = document.getElementById("hero-logo-spin-canvas");
    let spinner = null;
    let openingSpinPending = motionAllowed();
    let returnSpinPending = false;
    const currentLogoDark = () => {
      const choice = root.dataset.themeChoice || "system";
      return choice === "dark" || (choice === "system" && systemTheme.matches);
    };
    const redrawRestingLogo = () => {
      if (logoPanel.classList.contains("is-logo-3d-resting")) {
        spinner?.redrawResting?.(currentLogoDark());
      }
    };
    const finishSpin = (reason = "interrupted") => {
      // The still-visible face-on WebGL frame is the last animation frame.
      // Do not swap it for a separately rasterized SVG when motion ends.
      const retain3D = reason === "completed" &&
        logoPanel.classList.contains("is-logo-complete");
      logoPanel.classList.toggle("is-logo-3d-resting", retain3D);
      logoPanel.classList.remove("is-logo-spinning");
      if (spinTrigger) {
        spinTrigger.disabled = false;
        if (reason === "contextlost") spinTrigger.hidden = true;
      }
      if (retain3D) redrawRestingLogo();
    };
    const cancelSpin = () => {
      spinner?.stop();
      finishSpin();
    };
    const setLogoFinished = complete => {
      logoPanel.classList.toggle("is-logo-complete", complete);
      if (spinTrigger) spinTrigger.hidden = !complete;
      if (!complete) cancelSpin();
    };
    const playLogoSpin = (opening=false) => {
      if (!spinCanvas || !spinTrigger || !logoPanel.classList.contains("is-logo-complete") ||
          logoPanel.classList.contains("is-logo-spinning")) return;
      try {
        if (!spinner) spinner = window.createRLogoSpin?.(spinCanvas, finishSpin);
        if (!spinner) {
          spinTrigger.hidden = true; // WebGL2 unavailable: retain the original 2D mark.
          return;
        }
        const dark = currentLogoDark();
        spinTrigger.disabled = true;
        // Render the front-facing first 3D frame before hiding the SVG.
        // This avoids a blank frame at the start of the crossfade cycle.
        spinner.play(dark, opening ? 2400 : undefined);
        logoPanel.classList.add("is-logo-spinning");
      } catch (error) {
        console.warn("R logo 3D view is unavailable", error);
        finishSpin();
        spinTrigger.hidden = true;
      }
    };
    // Start rotating on the click itself, concurrently with the native smooth
    // scroll. Do not wait for arrival at the hero (or change hash navigation).
    // When the initial engraving is unfinished, start as soon as it completes.
    for (const link of document.querySelectorAll('a[href="#top"]')) {
      link.addEventListener("click", () => {
        if (!motionAllowed()) return;
        openingSpinPending = false;
        if (logoPanel.classList.contains("is-logo-complete")) {
          if (!logoPanel.classList.contains("is-logo-spinning")) playLogoSpin();
        } else {
          returnSpinPending = true;
        }
      });
    }

    const syncReplay = () => {
      const ready = logoPanel.classList.contains("is-logo-ready");
      logoReplay.hidden = !ready;
      logoFrame.contentWindow?.postMessage({ channel, type: "motion", allowed: motionAllowed() }, "*");
      if (!motionAllowed()) {
        openingSpinPending = false;
        returnSpinPending = false;
        cancelSpin();
        if (ready) sendLogoMessage("show-static");
      }
    };

    window.addEventListener("message", event => {
      if (event.source !== logoFrame.contentWindow || event.data?.channel !== channel) return;
      if (event.data.type === "ready") syncTheme();
      if (event.data.type === "started") setLogoFinished(false);
      if (event.data.type === "completed") {
        setLogoFinished(true);
        if (openingSpinPending) {
          openingSpinPending = false; // Never repeat the automatic 3D spin.
          // A newly requested return replaces the opening spin (not two spins).
          if (!returnSpinPending && motionAllowed()) playLogoSpin(true);
        }
        if (returnSpinPending) {
          returnSpinPending = false;
          if (motionAllowed()) playLogoSpin();
        }
      }
      if (event.data.type === "theme-applied") {
        logoPanel.classList.add("is-logo-ready");
        syncReplay();
      }
    });
    logoFrame.addEventListener("load", () => sendLogoMessage("status"));
    logoReplay.addEventListener("click", () => {
      openingSpinPending = false;
      setLogoFinished(false);
      requestMotion();
      sendLogoMessage("replay");
    });
    spinTrigger?.addEventListener("click", () => playLogoSpin());
    // The resting canvas remains responsive to dark mode and viewport changes.
    systemTheme.addEventListener("change", redrawRestingLogo);
    new MutationObserver(redrawRestingLogo).observe(root, {
      attributes: true, attributeFilter: ["data-theme-choice"]
    });
    if (typeof ResizeObserver !== "undefined") {
      new ResizeObserver(redrawRestingLogo).observe(spinCanvas);
    }
    window.addEventListener("resize", redrawRestingLogo, { passive: true });
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) redrawRestingLogo();
    });
    systemMotion.addEventListener("change", syncReplay);
    motionChoice?.addEventListener("change", syncReplay);
    sendLogoMessage("status");
  }

  // Show a discreet portrait shortcut only during regular reading.
  // Its opacity/visibility are transitioned in CSS; the link is not removed
  // from the DOM, so both fade-in and fade-out remain smooth.
  const mobileBackTop = document.getElementById("mobile-back-top");
  if (mobileBackTop) {
    const portrait = window.matchMedia("(max-width: 820px) and (orientation: portrait)");
    const footer = document.querySelector(".site-footer");
    let returningToTop = false;
    const syncBackTop = () => {
      if (window.scrollY <= 12) returningToTop = false;
      // The footer's own TOP action replaces this shortcut at page end.
      const footerInView = Boolean(footer && footer.getBoundingClientRect().top <= window.innerHeight);
      const visible = portrait.matches && !footerInView && !returningToTop &&
        window.scrollY >= Math.max(280, window.innerHeight * 0.75);
      mobileBackTop.classList.toggle("is-visible", visible);
      mobileBackTop.setAttribute("aria-hidden", String(!visible));
      mobileBackTop.tabIndex = visible ? 0 : -1;
    };
    // All top links (including the floating button) immediately fade it out,
    // before native smooth scrolling begins. It must not reappear en route.
    for (const link of document.querySelectorAll('a[href="#top"]')) {
      link.addEventListener("click", () => {
        returningToTop = true;
        syncBackTop();
      });
    }
    window.addEventListener("scroll", syncBackTop, { passive: true });
    window.addEventListener("scrollend", () => {
      // Also recover if a return scroll is interrupted before reaching top.
      returningToTop = false;
      syncBackTop();
    }, { passive: true });
    window.addEventListener("resize", syncBackTop, { passive: true });
    portrait.addEventListener("change", syncBackTop);
    syncBackTop();
  }

  // The orange index lands on the actual final punctuation in "N.O.V.A.".
  // The listing card and enlarged sheet use different layouts, so measure each.
  function alignNovaPeriod(art) {
    if (!art?.classList.contains("art-nova")) return;
    const orbit = art.querySelector(".nova-orbits");
    const period = art.querySelector(".nova-title-period");
    if (!orbit || !period) return;
    const outer = art.getBoundingClientRect();
    const target = period.getBoundingClientRect();
    const orbitWidth = orbit.offsetWidth;
    if (!outer.width || !outer.height || !target.width || !target.height || !orbitWidth) return;
    // Original orbiter: top:5%, 6px marker, rotated by 34 degrees.
    const radius = orbitWidth * .45 - 3;
    const angle = 34 * Math.PI / 180;
    const dotX = outer.left + outer.width * .5 + radius * Math.sin(angle);
    const dotY = outer.top + outer.height * .46 - radius * Math.cos(angle);
    art.style.setProperty("--nova-point-dx", (target.left + target.width * .5 - dotX).toFixed(3) + "px");
    art.style.setProperty("--nova-point-dy", (target.top + target.height * .5 - dotY).toFixed(3) + "px");
    art.classList.add("is-dot-aligned");
  }
  const novaResizeObserver = typeof ResizeObserver === "function"
    ? new ResizeObserver(entries => {
        for (const entry of entries) alignNovaPeriod(entry.target);
      })
    : null;
  function observeNova(art) {
    if (!art?.classList.contains("art-nova")) return;
    alignNovaPeriod(art);
    novaResizeObserver?.observe(art);
  }
  observeNova(document.querySelector('.project-card[data-sheet-id="nova"] .art-nova'));
  document.fonts?.ready.then(() => {
    document.querySelectorAll(".art-nova").forEach(alignNovaPeriod);
  });
  window.addEventListener("resize", () => {
    document.querySelectorAll(".art-nova").forEach(alignNovaPeriod);
  }, { passive: true });

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
    const sheetBody = dialog.querySelector(".sheet-body");
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
        selector: ".art-wallpipe", duration: 7200,
        finishAnimation: "wp-open-status", finishTarget: "wp-status-open"
      },
      nova: {
        selector: ".art-nova", duration: 6000,
        finishAnimation: "nova-panel-system-in", finishTarget: "nova-panel-system"
      },
      "university-ai": {
        selector: ".art-university", duration: 5500,
        finishAnimation: "up-toast-appear", finishTarget: "up-toast"
      }
    };
    const activeMotion = () => motions[activeCard?.dataset.sheetId] || null;
    function resetSheetMotion() {
      if (motionTimer !== null) {
        window.clearTimeout(motionTimer);
        motionTimer = null;
      }
      for (const art of sheetVisual.querySelectorAll(".art-eqmount, .art-sorava, .art-wallpipe, .art-nova, .art-university")) {
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
    motionButton.addEventListener("click", () => {
      requestMotion();
      playSheetMotion();
    });
    // Touch layouts play the artwork crossing the viewport center, once per visit.
    const centerPlayback = window.matchMedia("(max-width:760px), (hover:none), (any-pointer:coarse)");
    const listingMotions = [];
    const centeredMotions = new Set();
    let listingFrame = null;
    function resetListingMotion(entry) {
      window.clearTimeout(entry.timer);
      entry.timer = null;
      entry.art.classList.remove("is-playing", "is-hovering", "is-complete");
    }
    function finishListingMotion(entry) {
      if (!entry.art.classList.contains("is-playing")) return;
      window.clearTimeout(entry.timer);
      entry.timer = null;
      entry.art.classList.add("is-complete");
      entry.art.classList.remove("is-playing");
    }
    function updateCenteredMotion() {
      listingFrame = null;
      let next = [];
      if (centerPlayback.matches && motionAllowed() && !dialog.open && !document.hidden) {
        const headerBottom = document.querySelector(".site-header").getBoundingClientRect().bottom;
        const center = (window.innerHeight + Math.max(0, headerBottom)) / 2;
        // Extend the trigger band 12% above and below the usable viewport center.
        const range = (window.innerHeight - Math.max(0, headerBottom)) * .12;
        next = listingMotions.filter(entry => {
          const bounds = entry.art.getBoundingClientRect();
          return bounds.width > 0 && bounds.top <= center + range && bounds.bottom >= center - range;
        });
      }
      for (const entry of centeredMotions) {
        if (!next.includes(entry)) {
          resetListingMotion(entry);
          centeredMotions.delete(entry);
        }
      }
      for (const entry of next) {
        if (centeredMotions.has(entry)) continue;
        resetListingMotion(entry);
        void entry.art.getBoundingClientRect().width;
        centeredMotions.add(entry);
        entry.art.classList.add("is-playing");
        entry.timer = window.setTimeout(() => finishListingMotion(entry), entry.duration + 250);
      }
    }

    function scheduleCenteredMotion() {
      if (listingFrame === null) listingFrame = requestAnimationFrame(updateCenteredMotion);
    }
    for (const [id, motion] of Object.entries(motions)) {
      const media = document.querySelector(`.project-card[data-sheet-id="${id}"] .project-media`);
      const art = media?.querySelector(motion.selector);
      if (!media || !art) continue;
      const entry = { art, duration: motion.duration / 1.6, timer: null };
      listingMotions.push(entry);
      art.addEventListener("animationend", event => {
        if (event.animationName === motion.finishAnimation &&
            event.target.classList.contains(motion.finishTarget)) finishListingMotion(entry);
      });
      media.addEventListener("pointerenter", event => {
        if (!centerPlayback.matches && event.pointerType === "mouse" && motionAllowed() &&
            window.matchMedia("(hover:hover) and (pointer:fine)").matches) {
          art.classList.remove("is-complete");
          art.classList.add("is-hovering");
        }
      });
      media.addEventListener("pointerleave", () => {
        if (!centeredMotions.has(entry)) art.classList.remove("is-hovering", "is-complete");
      });
    }
    // Private previews use the same viewport trigger with their existing swing timing.
    for (const media of document.querySelectorAll(".project-media--locked")) {
      const entry = { art: media, duration: 1750, timer: null };
      listingMotions.push(entry);
      media.addEventListener("animationend", event => {
        if (event.animationName === "mm-lock-damped-swing") finishListingMotion(entry);
      });
    }
    window.addEventListener("scroll", scheduleCenteredMotion, { passive: true });
    window.addEventListener("resize", scheduleCenteredMotion, { passive: true });
    window.visualViewport?.addEventListener("resize", scheduleCenteredMotion, { passive: true });
    document.addEventListener("visibilitychange", scheduleCenteredMotion);
    centerPlayback.addEventListener("change", scheduleCenteredMotion);
    for (const button of buttons) button.addEventListener("click", scheduleCenteredMotion);
    function syncMotionPreference() {
      const allowed = motionAllowed();
      const showReplay = Boolean(activeMotion());
      if (!showReplay && document.activeElement === motionButton) closeButton.focus();
      motionButton.hidden = !showReplay;
      if (sheetVisualBrand) sheetVisualBrand.hidden = showReplay;
      if (!allowed) {
        resetSheetMotion();
        for (const entry of listingMotions) resetListingMotion(entry);
        centeredMotions.clear();
      }
      scheduleCenteredMotion();
    }
    systemMotion.addEventListener("change", syncMotionPreference);
    motionChoice?.addEventListener("change", syncMotionPreference);
    syncMotionPreference();

    const eligible = () => cards.filter(card => !card.hidden && card.querySelector("[data-open-sheet]"));

    function openSheet(card, trigger) {
      if (!card || !card.querySelector("[data-open-sheet]")) return;
      resetSheetMotion();
      for (const entry of listingMotions) resetListingMotion(entry);
      centeredMotions.clear();
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
      const oldNova = sheetVisual.querySelector(".art-nova");
      if (oldNova) novaResizeObserver?.unobserve(oldNova);
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
      syncMotionPreference();
      motionButton.textContent = motions[card.dataset.sheetId]?.loop ? "RESTART" : "REPLAY";
      motionButton.setAttribute("aria-label", `${sheetTitle.textContent} のアニメーションを再生`);
      // Each sheet starts at the beginning of its own right-side content.
      if (sheetBody) sheetBody.scrollTop = 0;
      if (sheetCopySide) sheetCopySide.scrollTop = 0;
      sheetTags.replaceChildren(...[...card.querySelectorAll(".tag-row span")].map(tag => tag.cloneNode(true)));
      const live = card.querySelector(".project-links a[href]");
      sheetActions.replaceChildren();
      if (live) {
        const link = live.cloneNode(true);
        sheetActions.append(link);
      }
      prevButton.disabled = selection.length < 2;
      nextButton.disabled = selection.length < 2;
      if (!dialog.open) dialog.showModal();
      observeNova(art);
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
      scheduleCenteredMotion();
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

