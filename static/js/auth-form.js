// Password visibility toggle + lightweight client-side validation.
// Server remains the source of truth; this only improves UX and catches
// obvious mistakes before submit.

function initPasswordToggle(inputId, toggleId) {
  const input = document.getElementById(inputId);
  const toggle = document.getElementById(toggleId);
  if (!input || !toggle) return;

  toggle.addEventListener('click', () => {
    const isHidden = input.type === 'password';
    input.type = isHidden ? 'text' : 'password';
    toggle.innerHTML = isHidden
      ? '<i data-lucide="eye-off"></i>'
      : '<i data-lucide="eye"></i>';
    if (window.lucide) lucide.createIcons();
  });
}

function scorePassword(value) {
  let score = 0;
  if (value.length >= 6) score++;
  if (value.length >= 10) score++;
  if (/[A-Z]/.test(value) && /[a-z]/.test(value)) score++;
  if (/[0-9]/.test(value)) score++;
  if (/[^A-Za-z0-9]/.test(value)) score++;
  return Math.min(score, 4);
}

function initPasswordStrength(inputId, barId) {
  const input = document.getElementById(inputId);
  const bar = document.getElementById(barId);
  if (!input || !bar) return;

  const colors = ['#f2857a', '#f2b06a', '#e8d15c', '#7fe0b3'];
  const widths = ['20%', '45%', '70%', '100%'];

  input.addEventListener('input', () => {
    if (!input.value) {
      bar.style.width = '0%';
      return;
    }
    const score = scorePassword(input.value);
    const idx = Math.max(score - 1, 0);
    bar.style.width = widths[idx];
    bar.style.background = colors[idx];
  });
}

function setFieldError(fieldWrapId, message) {
  const wrap = document.getElementById(fieldWrapId);
  if (!wrap) return;
  const errEl = wrap.querySelector('.field-error');
  const inputEl = wrap.querySelector('input, textarea');
  if (message) {
    if (errEl) {
      errEl.querySelector('span').textContent = message;
      errEl.classList.add('show');
    }
    if (inputEl) inputEl.classList.add('invalid');
  } else {
    if (errEl) errEl.classList.remove('show');
    if (inputEl) inputEl.classList.remove('invalid');
  }
}

// fieldIdPrefix: needed when a page has two forms sharing the same field
// `name`s (e.g. combined login/register both have name="email") so each
// form's field-wrap has a unique id like "field-login-email" instead of
// the default "field-email" both forms would otherwise collide on.
function initFormValidation(formId, rules, fieldIdPrefix = '') {
  const form = document.getElementById(formId);
  if (!form) return;

  const wrapId = (name) => `field-${fieldIdPrefix}${name}`;

  const validateField = (name) => {
    const rule = rules[name];
    if (!rule) return true;
    const input = form.querySelector(`[name="${name}"]`);
    if (!input) return true;
    const error = rule.validate(input.value, form);
    setFieldError(wrapId(name), error);
    return !error;
  };

  Object.keys(rules).forEach((name) => {
    const input = form.querySelector(`[name="${name}"]`);
    if (input) {
      input.addEventListener('blur', () => validateField(name));
      input.addEventListener('input', () => {
        const wrap = document.getElementById(wrapId(name));
        if (wrap && wrap.querySelector('.invalid')) validateField(name);
      });
    }
  });

  form.addEventListener('submit', (e) => {
    let valid = true;
    Object.keys(rules).forEach((name) => {
      if (!validateField(name)) valid = false;
    });
    if (!valid) e.preventDefault();
  });
}
