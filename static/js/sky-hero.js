// Live sky widget: real clock + day/night lighting + lightweight CSS-only
// drifting cloud layers reacting to live weather. Used by both the
// admin/analyst dashboard (fixed to Karachi) and the public weather page
// (any searched location).
//
// This used to render a real WebGL volumetric cloud field via Vanta.js /
// Three.js, but that meant continuous per-frame 3D geometry + shading on
// the GPU for as long as the page was open -- too heavy on modest hardware
// and integrated GPUs (noticeable fan/heat and jank elsewhere on the page).
// Plain CSS transform/opacity animations composite almost for free.

function karachiNow() {
  // Asia/Karachi is UTC+5, no DST.
  const utc = new Date(Date.now());
  const karachiMs = utc.getTime() + utc.getTimezoneOffset() * 60000 + 5 * 3600000;
  return new Date(karachiMs);
}

// The dashboard is always Karachi; the public page shows the viewer's own
// local clock (close enough for whatever place they searched).
function updateClock(useKarachiTime) {
  const now = useKarachiTime ? karachiNow() : new Date();
  const timeEl = document.getElementById('clockTime');
  const dateEl = document.getElementById('clockDate');
  if (!timeEl || !dateEl) return now.getHours();

  const hh = String(now.getHours()).padStart(2, '0');
  const mm = String(now.getMinutes()).padStart(2, '0');
  timeEl.textContent = `${hh}:${mm}`;

  const options = { weekday: 'long', month: 'long', day: 'numeric' };
  dateEl.textContent = now.toLocaleDateString('en-US', options);

  return now.getHours();
}

function isNightHour(hour) {
  return hour < 6 || hour >= 19;
}

// Clear-sky CSS gradients (no cloud layer -- a clear sky shouldn't show
// cloud shapes at all). Day = bright blue with a warm sun glow in one
// corner; night = deep navy with a cool moon glow.
const CLEAR_SKY_GRADIENTS = {
  day: 'radial-gradient(circle at 75% 20%, #f0ece5 0%, #d8d3ce 8%, #9599ab 35%, #5c5f78 68%, #31304d 100%)',
  night: 'radial-gradient(circle at 75% 20%, #33445f 0%, #16233d 22%, #0c1a30 55%, #060e1f 100%)',
};

function paintSky(hero, isNight, condition) {
  const bgFallback = {
    day: '#6fa3c2',
    night: '#0c1a30',
  };
  hero.classList.toggle('is-night', isNight);
  hero.classList.toggle('is-day', !isNight);
  hero.classList.toggle('is-clear', condition === 'clear');
  hero.classList.toggle('is-storm', condition === 'storm');

  if (condition === 'clear') {
    hero.style.background = CLEAR_SKY_GRADIENTS[isNight ? 'night' : 'day'];
  } else {
    hero.style.background = bgFallback[isNight ? 'night' : 'day'];
  }
}

// Respect the OS-level "reduce motion" accessibility setting -- skip the
// drifting cloud animation (still show static cloud shapes) if set.
const PREFERS_REDUCED_MOTION = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

function initCssClouds(condition) {
  const target = document.getElementById('vantaClouds');
  if (!target) return;

  target.classList.remove('clouds-cloudy', 'clouds-rain', 'clouds-storm');
  target.classList.toggle('clouds-animated', !PREFERS_REDUCED_MOTION);

  // Clear sky: no cloud shapes at all -- the CSS gradient shows through.
  if (condition === 'clear') return;

  const bucket = (condition === 'rain' || condition === 'storm') ? condition : 'cloudy';
  target.classList.add('clouds-' + bucket);
}

function renderStars(isNight) {
  const layer = document.getElementById('stars');
  if (!layer) return;
  layer.classList.toggle('visible', isNight);
  if (layer.dataset.built) return;

  const count = 40;
  for (let i = 0; i < count; i++) {
    const star = document.createElement('div');
    star.className = 'star';
    star.style.left = Math.random() * 100 + '%';
    star.style.top = Math.random() * 75 + '%';
    star.style.animationDelay = (Math.random() * 3).toFixed(2) + 's';
    layer.appendChild(star);
  }
  layer.dataset.built = 'true';
}

function renderRain(show) {
  const layer = document.getElementById('rainLayer');
  if (!layer) return;
  layer.innerHTML = '';
  if (!show) return;

  const count = 35;
  for (let i = 0; i < count; i++) {
    const drop = document.createElement('div');
    drop.className = 'raindrop';
    drop.style.left = Math.random() * 100 + '%';
    drop.style.height = 14 + Math.random() * 14 + 'px';
    drop.style.animationDuration = 0.6 + Math.random() * 0.5 + 's';
    drop.style.animationDelay = Math.random() * 1.5 + 's';
    layer.appendChild(drop);
  }
}

let lightningTimer = null;

function stopLightning() {
  if (lightningTimer) {
    clearTimeout(lightningTimer);
    lightningTimer = null;
  }
}

function scheduleLightning(hero) {
  const flash = document.getElementById('lightningFlash');
  if (!flash) return;

  const strike = () => {
    flash.classList.add('flash');
    setTimeout(() => flash.classList.remove('flash'), 180);
    // Occasional quick double-flash for realism.
    if (Math.random() < 0.35) {
      setTimeout(() => {
        flash.classList.add('flash');
        setTimeout(() => flash.classList.remove('flash'), 120);
      }, 260);
    }
    lightningTimer = setTimeout(strike, 3000 + Math.random() * 6000);
  };

  lightningTimer = setTimeout(strike, 1500 + Math.random() * 3000);
}

function renderLightning(show, hero) {
  stopLightning();
  if (show) scheduleLightning(hero);
}

function applySkyState(hero) {
  const useKarachiTime = hero.dataset.clock !== 'local';
  const hour = updateClock(useKarachiTime);
  const isNight = hero.dataset.isDay === 'false' || (hero.dataset.isDay === undefined && isNightHour(hour));
  const condition = hero.dataset.condition || 'cloudy';

  paintSky(hero, isNight, condition);
  initCssClouds(condition);
  renderStars(isNight && condition !== 'storm');
  renderRain(condition === 'rain' || condition === 'storm');
  renderLightning(condition === 'storm', hero);
}

// options.apiUrl: endpoint to auto-poll for weather refreshes (defaults to
// the dashboard's fixed-location endpoint). Pass null to disable auto-poll
// when the page drives weather data itself (e.g. the public search page).
function initSkyHero(options = {}) {
  const hero = document.getElementById('skyHero');
  if (!hero) return;

  const apiUrl = options.apiUrl === undefined ? '/dashboard/api/weather' : options.apiUrl;

  applySkyState(hero);
  setInterval(() => applySkyState(hero), 30000);

  if (apiUrl) {
    setInterval(async () => {
      try {
        const res = await fetch(apiUrl);
        const data = await res.json();
        hero.dataset.condition = data.condition;
        hero.dataset.isDay = data.is_day ? 'true' : 'false';
        applySkyState(hero);
      } catch (e) {
        // silent: keep last known state
      }
    }, 600000);
  }

  window.addEventListener('beforeunload', stopLightning);
}
