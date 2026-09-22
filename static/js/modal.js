// Reusable confirmation modal wiring. Call initConfirmModal once per modal
// instance on the page (trigger button -> shows overlay; cancel/backdrop/Esc -> hides it).
function initConfirmModal({ triggerId, overlayId, cancelId }) {
  const trigger = document.getElementById(triggerId);
  const overlay = document.getElementById(overlayId);
  const cancelBtn = document.getElementById(cancelId);
  if (!trigger || !overlay) return;

  const open = () => {
    overlay.hidden = false;
    requestAnimationFrame(() => overlay.classList.add('open'));
    document.body.style.overflow = 'hidden';
  };

  const close = () => {
    overlay.classList.remove('open');
    document.body.style.overflow = '';
    setTimeout(() => { overlay.hidden = true; }, 150);
  };

  trigger.addEventListener('click', open);
  if (cancelBtn) cancelBtn.addEventListener('click', close);

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) close();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !overlay.hidden) close();
  });
}
