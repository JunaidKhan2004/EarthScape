// Live sky widget: real clock + day/night lighting + a real WebGL
// volumetric cloud field (Vanta.js / Three.js) reacting to live weather.
// Used by both the admin/analyst dashboard (fixed to Karachi) and the
// public weather page (any searched location).

let vantaEffect = null;

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

// Vanta's CLOUDS effect takes numeric hex colors (0xRRGGBB), not CSS strings.
const SKY_PALETTES = {
  day: {
    clear: { skyColor: 0x5fb1d6, cloudColor: 0xffffff, cloudShadowColor: 0x9fb3bd, sunColor: 0xffcf5c, sunGlareColor: 0xff9d4d, sunlightColor: 0xffe8b0, speed: 1.1 },
    cloudy: { skyColor: 0x7d94a0, cloudColor: 0xe7edee, cloudShadowColor: 0x62727a, sunColor: 0xd8c8a8, sunGlareColor: 0xb7a487, sunlightColor: 0xcfd9db, speed: 1.4 },
    rain: { skyColor: 0x4c5c68, cloudColor: 0xb7c1c6, cloudShadowColor: 0x35424a, sunColor: 0x9aa6ac, sunGlareColor: 0x808f96, sunlightColor: 0x99a7ac, speed: 1.9 },
    storm: { skyColor: 0x2c3742, cloudColor: 0x808d94, cloudShadowColor: 0x1c242b, sunColor: 0x6b767c, sunGlareColor: 0x565f66, sunlightColor: 0x6d787d, speed: 2.4 },
  },
  night: {
    clear: { skyColor: 0x0c1a30, cloudColor: 0x24344c, cloudShadowColor: 0x081120, sunColor: 0xbfd0e8, sunGlareColor: 0x8fa3c2, sunlightColor: 0x33445f, speed: 0.7 },
    cloudy: { skyColor: 0x121e2a, cloudColor: 0x33465a, cloudShadowColor: 0x0a121b, sunColor: 0x7f93a8, sunGlareColor: 0x5c6d80, sunlightColor: 0x384a5c, speed: 1.0 },
    rain: { skyColor: 0x0a121c, cloudColor: 0x293846, cloudShadowColor: 0x050a10, sunColor: 0x5b6b78, sunGlareColor: 0x475462, sunlightColor: 0x2c3946, speed: 1.6 },
    storm: { skyColor: 0x05090e, cloudColor: 0x1c262f, cloudShadowColor: 0x02050a, sunColor: 0x3d4750, sunGlareColor: 0x2f3841, sunlightColor: 0x202932, speed: 2.1 },
  },
};

// Clear-sky CSS gradients (no VANTA clouds -- a clear sky shouldn't show
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

function initVantaClouds(isNight, condition) {
  const target = document.getElementById('vantaClouds');
  if (!target || typeof VANTA === 'undefined') return;

  // Clear sky: no cloud shapes at all -- tear down VANTA and let the CSS
  // gradient show through instead.
  if (condition === 'clear') {
    if (vantaEffect) {
      vantaEffect.destroy();
      vantaEffect = null;
    }
    return;
  }

  const period = isNight ? 'night' : 'day';
  const palette = (SKY_PALETTES[period] && SKY_PALETTES[period][condition]) || SKY_PALETTES[period].cloudy;

  if (vantaEffect) {
    vantaEffect.setOptions(palette);
    return;
  }

  vantaEffect = VANTA.CLOUDS({
    el: target,
    mouseControls: false,
    touchControls: false,
    gyroControls: false,
    minHeight: 200,
    minWidth: 200,
    backgroundAlpha: 1,
    // Render at a lower internal resolution -- VANTA's WebGL cloud field is
    // the heaviest thing on this page (continuous per-frame 3D geometry),
    // and dropping scale cuts GPU load a lot with almost no visible
    // difference once it's blurred/composited into the page.
    scale: 0.65,
    scaleMobile: 0.55,
    ...palette,
  });
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
  initVantaClouds(isNight, condition);
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

  window.addEventListener('beforeunload', () => {
    if (vantaEffect) vantaEffect.destroy();
    stopLightning();
  });
}
