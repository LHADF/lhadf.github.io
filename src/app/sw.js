/* Cervus — service worker: la app abre sin conexión.
   armar.py completa la versión (huella del index.html) y la lista de archivos que se guardan al instalar.
   - La página: primero la red (para que llegue lo nuevo); sin red, la guardada.
   - Las horas (laudes.js?v=…) y los íconos: lo guardado, porque la huella cambia si cambian.
   - Las imágenes del día y las fuentes: lo guardado, y se renueva por detrás. */
const VERSION = '__VERSION__';
const APP = 'cervus-' + VERSION, FUENTES = 'cervus-fuentes', ILU = 'cervus-ilu';
const PRECARGA = __PRECARGA__;

self.addEventListener('install', e => {
  e.waitUntil(caches.open(APP).then(c => c.addAll(PRECARGA)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(ks => Promise.all(ks.filter(k => k.startsWith('cervus-') && k !== APP && k !== FUENTES && k !== ILU).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

const guardar = (cache, req, res) => { if (res && (res.ok || res.type === 'opaque')) { const r = res.clone(); caches.open(cache).then(c => c.put(req, r)); } return res; };

// Primero la red, con plazo: si tarda o falla, lo guardado
function primeroRed(req) {
  const red = fetch(req).then(r => guardar(APP, './', r));
  const plazo = new Promise(ok => setTimeout(ok, 4000));
  return Promise.race([red.catch(() => null), plazo.then(() => null)])
    .then(r => r || caches.match('./').then(g => g || red));
}

// Lo guardado; si no está, la red (y se guarda)
const primeroCache = (req, cache) => caches.match(req).then(g => g || fetch(req).then(r => guardar(cache, req, r)));

// Lo guardado al instante, y se renueva por detrás
function renovar(req, cache) {
  const red = fetch(req).then(r => guardar(cache, req, r)).catch(() => null);
  return caches.match(req).then(g => g || red.then(r => r || Response.error()));
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const u = new URL(req.url);
  if (req.mode === 'navigate' && u.origin === location.origin) return e.respondWith(primeroRed(req));
  if (u.hostname === 'fonts.googleapis.com' || u.hostname === 'fonts.gstatic.com') return e.respondWith(renovar(req, FUENTES));
  if (u.origin !== location.origin) return;
  if (u.pathname.includes('/ilu/')) return e.respondWith(renovar(req, ILU));
  e.respondWith(primeroCache(req, APP));
});
