// Intake interactions: submit feedback, auto-advance, date reveal, issue CTA.
(function () {
  'use strict';

  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Address form: button says what's happening.
  var addressForm = document.querySelector('[data-address-form]');
  if (addressForm) {
    addressForm.addEventListener('submit', function () {
      var btn = addressForm.querySelector('button[type="submit"]');
      if (btn) {
        btn.disabled = true;
        btn.textContent = 'Checking address\u2026';
      }
    });
  }

  // Address typeahead. Suggestions come from our own server route — no
  // credentials in the browser. If the route returns nothing (demo mode,
  // no subscription, outage), the input simply behaves like a plain field.
  var suggestWrap = document.querySelector('[data-suggest]');
  if (suggestWrap && window.fetch) {
    var input = suggestWrap.querySelector('input');
    var list = suggestWrap.querySelector('.suggest-list');
    var suggestStatus = document.querySelector('[data-suggest-status]');
    var items = [];
    var active = -1;
    var debounceTimer = null;
    var controller = null;

    var setSuggestStatus = function (message) {
      if (suggestStatus) suggestStatus.textContent = message || '';
    };

    var close = function () {
      list.hidden = true;
      list.innerHTML = '';
      items = [];
      active = -1;
      input.setAttribute('aria-expanded', 'false');
      input.removeAttribute('aria-activedescendant');
    };

    var select = function (index) {
      if (index < 0 || index >= items.length) return;
      input.value = items[index];
      close();
      input.focus();
    };

    var setActive = function (index) {
      active = index;
      Array.prototype.forEach.call(list.children, function (li, i) {
        li.setAttribute('aria-selected', String(i === index));
      });
      if (index >= 0) {
        input.setAttribute('aria-activedescendant', 'suggest-opt-' + index);
        if (list.children[index].scrollIntoView) {
          list.children[index].scrollIntoView({ block: 'nearest' });
        }
      } else {
        input.removeAttribute('aria-activedescendant');
      }
    };

    var render = function (suggestions) {
      close();
      if (!suggestions.length) {
        setSuggestStatus('No suggestions right now — type your full address and we\u2019ll validate it when you continue.');
        return;
      }
      setSuggestStatus('');
      items = suggestions;
      suggestions.forEach(function (text, i) {
        var li = document.createElement('li');
        li.id = 'suggest-opt-' + i;
        li.setAttribute('role', 'option');
        li.setAttribute('aria-selected', 'false');
        li.textContent = text;
        // mousedown so selection wins over the input's blur.
        li.addEventListener('mousedown', function (event) {
          event.preventDefault();
          select(i);
        });
        list.appendChild(li);
      });
      list.hidden = false;
      input.setAttribute('aria-expanded', 'true');
    };

    input.addEventListener('input', function () {
      window.clearTimeout(debounceTimer);
      var query = input.value.trim();
      if (query.length < 4) {
        close();
        setSuggestStatus('');
        return;
      }
      debounceTimer = window.setTimeout(function () {
        if (controller) controller.abort();
        controller = window.AbortController ? new AbortController() : null;
        fetch('/api/address-suggestions?q=' + encodeURIComponent(query), {
          signal: controller ? controller.signal : undefined
        })
          .then(function (response) { return response.ok ? response.json() : { suggestions: [] }; })
          .then(function (data) {
            render((data.suggestions || []).map(function (s) { return s.display; }));
          })
          .catch(function () { /* typeahead is best-effort */ });
      }, 250);
    });

    input.addEventListener('keydown', function (event) {
      if (list.hidden) return;
      if (event.key === 'ArrowDown') {
        event.preventDefault();
        setActive(active + 1 >= items.length ? 0 : active + 1);
      } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        setActive(active - 1 < 0 ? items.length - 1 : active - 1);
      } else if (event.key === 'Enter' && active >= 0) {
        event.preventDefault();
        select(active);
      } else if (event.key === 'Escape') {
        close();
      }
    });

    input.addEventListener('blur', function () {
      window.setTimeout(close, 120);
    });
  }

  // Question screens: selecting an option advances after a beat.
  var questionForm = document.querySelector('[data-question-form]');
  if (questionForm) {
    questionForm.querySelectorAll('input[type="radio"]').forEach(function (radio) {
      radio.addEventListener('change', function () {
        window.setTimeout(function () {
          questionForm.requestSubmit();
        }, reducedMotion ? 0 : 180);
      });
    });

    var dateToggle = questionForm.querySelector('[data-date-toggle]');
    var dateReveal = questionForm.querySelector('[data-date-reveal]');
    if (dateToggle && dateReveal) {
      dateToggle.addEventListener('click', function () {
        dateReveal.hidden = !dateReveal.hidden;
        dateToggle.setAttribute('aria-expanded', String(!dateReveal.hidden));
        if (!dateReveal.hidden) {
          var input = dateReveal.querySelector('input');
          if (input) input.focus();
        }
      });
    }
  }

  // Issue picker: CTA text reflects state — the empty path never feels like failure.
  var issuesForm = document.querySelector('[data-issues-form]');
  if (issuesForm) {
    var cta = issuesForm.querySelector('[data-issues-cta]');
    var update = function () {
      var count = issuesForm.querySelectorAll('input[name="issues"]:checked').length;
      var custom = issuesForm.querySelector('input[name="custom_issue"]');
      var hasCustom = custom && custom.value.trim().length > 0;
      if (cta) {
        cta.textContent = count > 0 || hasCustom
          ? 'Add these and build my plan'
          : 'Nothing to add \u2014 build my plan';
      }
    };
    issuesForm.addEventListener('change', update);
    issuesForm.addEventListener('input', update);
    update();
  }
})();
