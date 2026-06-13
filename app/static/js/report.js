// Report interactions: one-open accordion, plan reveal, chip explainers.
(function () {
  'use strict';

  // One orchestrated reveal on first render.
  var stagger = document.querySelector('.reveal-stagger');
  if (stagger) {
    stagger.querySelectorAll('.horizon-item').forEach(function (item, index) {
      item.style.setProperty('--reveal-index', String(index));
    });
    window.requestAnimationFrame(function () {
      stagger.classList.add('revealed');
    });
  }

  // Action cards: one open at a time.
  var cards = Array.prototype.slice.call(
    document.querySelectorAll('details[data-action-card]')
  );
  cards.forEach(function (card) {
    card.addEventListener('toggle', function () {
      if (!card.open) return;
      cards.forEach(function (other) {
        if (other !== card) other.open = false;
      });
    });
  });

  // Provenance chips: tap shows a one-line explainer.
  document.querySelectorAll('.chip[data-explainer]').forEach(function (chip) {
    chip.setAttribute('role', 'button');
    chip.setAttribute('tabindex', '0');
    var toggle = function () {
      var existing = chip.nextElementSibling;
      if (existing && existing.classList.contains('chip-pop')) {
        existing.remove();
        return;
      }
      document.querySelectorAll('.chip-pop').forEach(function (pop) {
        pop.remove();
      });
      var pop = document.createElement('span');
      pop.className = 'chip-pop';
      pop.textContent = chip.getAttribute('data-explainer');
      chip.insertAdjacentElement('afterend', pop);
    };
    chip.addEventListener('click', toggle);
    chip.addEventListener('keydown', function (event) {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        toggle();
      }
    });
  });
})();
