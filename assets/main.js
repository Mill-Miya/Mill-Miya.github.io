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
    if (archiveLabel) archiveLabel.hidden = !cards.some(card => !card.classList.contains("featured") && !card.hidden);
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
  const year = document.querySelector("#footer-year");
  if (year) year.textContent = String(new Date().getFullYear());
})();
