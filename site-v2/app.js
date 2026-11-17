/* Work catalogue only. No network requests, analytics, storage, or accounts. */
(() => {
  'use strict';
  const entries = Array.from(document.querySelectorAll('[data-project]'));
  const controls = Array.from(document.querySelectorAll('[data-filter]'));
  const count = document.getElementById('visible-count');
  const featured = document.getElementById('featured-work');
  const archive = document.getElementById('archive');
  const empty = document.getElementById('empty-message');

  function filterWork(category) {
    let visible = 0;
    for (const entry of entries) {
      const tags = (entry.dataset.category || '').split(/\s+/);
      const allowed = category === 'all' || tags.includes(category);
      entry.hidden = !allowed;
      if (allowed) visible += 1;
    }
    for (const control of controls) {
      const selected = control.dataset.filter === category;
      control.classList.toggle('is-active', selected);
      control.setAttribute('aria-pressed', String(selected));
    }
    if (count) count.textContent = String(visible).padStart(2, '0');
    if (featured) featured.hidden = !featured.querySelector('[data-project]:not([hidden])');
    if (archive) {
      const hasArchive = Boolean(archive.querySelector('[data-project]:not([hidden])'));
      archive.classList.toggle('archive-is-empty', !hasArchive);
    }
    if (empty) empty.hidden = visible !== 0;
  }

  for (const control of controls) {
    control.addEventListener('click', () => filterWork(control.dataset.filter || 'all'));
  }
  filterWork('all');

  const year = document.getElementById('year');
  if (year) year.textContent = String(new Date().getFullYear());

  const revealTargets = document.querySelectorAll('[data-reveal]');
  if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const observer = new IntersectionObserver((items) => {
      for (const item of items) {
        if (item.isIntersecting) {
          item.target.classList.add('is-revealed');
          observer.unobserve(item.target);
        }
      }
    }, { threshold: 0.12, rootMargin: '0px 0px 48px 0px' });
    revealTargets.forEach(node => observer.observe(node));
  } else {
    revealTargets.forEach(node => node.classList.add('is-revealed'));
  }
})();
