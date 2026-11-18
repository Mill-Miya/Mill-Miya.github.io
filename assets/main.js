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
    if (archiveLabel) archiveLabel.hidden = !cards.some(card => !card.classList.contains("featured") && !card.classList.contains("is-locked") && !card.hidden);
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
    const sheetKind = document.getElementById("sheet-kind");
    const sheetTags = document.getElementById("sheet-tags");
    const sheetVisual = document.getElementById("sheet-visual");
    const sheetActions = document.getElementById("sheet-actions");
    const sheetCounter = document.getElementById("sheet-counter");
    const sheetPosition = document.getElementById("sheet-position");
    const sheetVisualIndex = document.getElementById("sheet-visual-index");
    const closeButton = document.getElementById("sheet-close");
    const prevButton = document.getElementById("sheet-prev");
    const nextButton = document.getElementById("sheet-next");
    let activeCard = null;
    let lastOpener = null;
    const eligible = () => cards.filter(card => !card.hidden && card.querySelector("[data-open-sheet]"));

    function openSheet(card, trigger) {
      if (!card || !card.querySelector("[data-open-sheet]")) return;
      if (!dialog.open && trigger instanceof HTMLElement) lastOpener = trigger;
      const selection = eligible();
      const current = selection.indexOf(card);
      if (current < 0) return;
      activeCard = card;
      dialog.dataset.theme = card.dataset.sheetId || "";
      sheetTitle.textContent = card.querySelector(".project-info h3")?.textContent?.trim() || "";
      sheetDescription.textContent = card.querySelector(".project-info > p")?.textContent?.trim() || "";
      sheetKind.textContent = card.querySelector(".project-year")?.textContent?.trim() || "PROJECT";
      const number = card.dataset.project || String(current + 1).padStart(2, "0");
      sheetCounter.textContent = "PROJECT / " + number.padStart(3, "0");
      const position = String(current + 1).padStart(2, "0") + " / " + String(selection.length).padStart(2, "0");
      sheetPosition.textContent = position;
      sheetVisualIndex.textContent = position;
      const art = card.querySelector(".project-art")?.cloneNode(true);
      if (art) {
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
