/* عامل خدمة ترتيل (2026-11-28): تثبيت الموقع تطبيقًا يعمل بدون إنترنت.
   - الصفحات وملفات البيانات: من الشبكة أولًا (فيصل أي تحديث للموقع فورًا)، والنسخة المحفوظة عند انقطاع الإنترنت.
   - الملفات الثابتة (الخطوط والصور والسكربتات والمصحف): من المحفوظ فورًا ثم تُحدَّث في الخلفية.
   - التلاوات: لا يُخزَّن منها شيء تلقائيًا. ما يحفظه المستخدم (offline.js) يُشغَّل من الجهاز، مع دعم التقديم والتأخير (Range).
     وما لم يُحفظ يذهب للشبكة كما كان تمامًا (files.trtel.vip ثم الأرشيف).
   - البث المباشر (radio.trtel.vip وlive.trtel.vip) لا يمر على التخزين أبدًا. */
const V = 'v4';
// RUN ثابت الاسم: لا تضيع الصفحات التي زارها المستخدم عند كل تحديث لعامل الخدمة، وحجمه محدود بـ trim
const SHELL = 'trtel-shell-' + V, RUN = 'trtel-run-v3', AUDIO = 'trtel-audio-v1', KEEP = 'trtel-keep-v1';   // KEEP: المصحف المحفوظ بطلب المستخدم
const ARCH = 'https://archive.org/download/', SRV = 'https://files.trtel.vip/a/';
const CORE = ['./', 'index.html', 'offline.html', 'mushaf.html', 'surahs.html', 'reciters.html', 'manifest.webmanifest', 'offline.js',
  'icon-192.png', 'icon-512.png', 'logo512.jpg?v=2', 'playlist.json', 'stations.json', 'lists.json', 'links.json',
  'mushaf/len.json', 'mushaf/meta.json', 'mushaf/uthmanic_hafs_v22.ttf'];

const BASE = new URL('./', self.location).href;
const abs = u => new URL(u, BASE).href;

self.addEventListener('install', e => {
  e.waitUntil(caches.open(SHELL).then(c => Promise.all(CORE.map(u => c.add(new Request(abs(u), { cache: 'reload' })).catch(() => {})))).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith('trtel-') && k !== SHELL && k !== RUN && k !== AUDIO && k !== KEEP).map(k => caches.delete(k))))
    .then(() => self.clients.claim()).then(loadKeys).then(() => trim(true)));
});

/* مفاتيح التلاوات المحفوظة في الذاكرة: لنقرر فورًا هل نتدخل في طلب الصوت أم نتركه للشبكة كما هو */
let SAVED = null;
const loadKeys = () => caches.open(AUDIO).then(c => c.keys()).then(ks => { SAVED = new Set(ks.map(r => r.url)); }).catch(() => { SAVED = new Set(); });
loadKeys();
self.addEventListener('message', e => {
  const m = e.data || {};
  if (m.k === 'saved') { if (!SAVED) SAVED = new Set(); (m.add || []).forEach(u => SAVED.add(u)); (m.del || []).forEach(u => SAVED.delete(u)); }
  else if (m.k === 'reload') loadKeys();
  else if (m.k === 'warm' && Array.isArray(m.urls)) e.waitUntil(caches.open(RUN).then(c => Promise.all(m.urls.map(u => caches.match(u, { ignoreSearch: true }).then(r => r || c.add(u)).catch(() => {})))));
});

const audioKey = u => u.startsWith(SRV) ? ARCH + u.slice(SRV.length) : u.startsWith(ARCH) ? u : null;

async function serveAudio(req, key) {
  const c = await caches.open(AUDIO), r = await c.match(key);
  if (!r) return fetch(req);
  const size = +r.headers.get('content-length') || 0, type = r.headers.get('content-type') || 'audio/mpeg';
  const range = /bytes=(\d*)-(\d*)/.exec(req.headers.get('range') || '');
  if (!range) { const b = await r.blob(); return new Response(b, { status: 200, headers: { 'Content-Type': type, 'Content-Length': b.size, 'Accept-Ranges': 'bytes' } }); }
  const blob = await r.blob(), n = blob.size || size;
  let a = range[1] === '' ? Math.max(0, n - (+range[2] || 0)) : +range[1], z = range[1] !== '' && range[2] !== '' ? Math.min(+range[2], n - 1) : n - 1;
  if (a >= n) return new Response(null, { status: 416, headers: { 'Content-Range': 'bytes */' + n } });
  const part = blob.slice(a, z + 1);
  return new Response(part, { status: 206, statusText: 'Partial Content',
    headers: { 'Content-Type': type, 'Content-Length': part.size, 'Content-Range': `bytes ${a}-${z}/${n}`, 'Accept-Ranges': 'bytes' } });
}

// سقف للمحفوظ التلقائي (الصفحات والملفات الثابتة): عند تجاوزه يُحذف الأقدم. المحفوظ بطلب المستخدم (AUDIO وKEEP) لا يُمس.
const MAXRUN = 1500; let puts = 0;
async function trim(force) {
  if (!force && ++puts % 40) return;
  try { const c = await caches.open(RUN), ks = await c.keys(); if (ks.length > MAXRUN) await Promise.all(ks.slice(0, ks.length - MAXRUN + 300).map(k => c.delete(k))); } catch (e) {}
}
const put = (name, key, r) => caches.open(name).then(c => c.put(key, r)).then(() => name === RUN && trim()).catch(() => {});
// رد جاء بعد تحويل (301) لا يقبله المتصفح جوابًا لطلب تنقل من المحفوظ: نعيد بناءه بلا علامة التحويل
const clean = r => !r.redirected ? r : r.blob().then(b => new Response(b, { status: r.status, statusText: r.statusText, headers: r.headers }));

const timeout = (p, ms) => new Promise((ok, no) => { const t = setTimeout(() => no(new Error('timeout')), ms); p.then(v => { clearTimeout(t); ok(v); }, e => { clearTimeout(t); no(e); }); });
const pageKey = u => { const x = new URL(u); x.search = ''; x.hash = ''; if (x.pathname.endsWith('/')) x.pathname += 'index.html'; return x.href; };

async function fromCache(key) { return (await caches.match(key, { ignoreSearch: true })) || null; }

// الصفحات: الشبكة أولًا (مع مهلة إن كانت عندنا نسخة)، ثم المحفوظ، ثم صفحة «تحميلاتي»
async function page(e) {
  const key = pageKey(e.request.url), have = await fromCache(key);
  const net = fetch(e.request).then(r => { if (r.ok && r.type === 'basic') { const cp = r.clone(); Promise.resolve(clean(cp)).then(x => put(RUN, key, x)); } return r; });
  try { return await (have ? timeout(net, 6000) : net); }
  catch (err) {
    if (have) return clean(have);
    return (await fromCache(abs('offline.html'))) || new Response('<meta charset="utf-8"><p dir="rtl">لا يوجد اتصال بالإنترنت.</p>', { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
  }
}
// البيانات المتغيرة (json): الشبكة أولًا ثم المحفوظ
async function data(e) {
  const h = await caches.match(e.request, { ignoreSearch: !new URL(e.request.url).search });
  const net = fetch(e.request).then(r => { if (r.ok) put(RUN, e.request, r.clone()); return r; });
  try { return await (h ? timeout(net, 8000) : net); }   // شبكة بطيئة جدًا: لا تعلق الصفحة ما دام عندنا نسخة
  catch (err) { if (h) { e.waitUntil(net.catch(() => {})); return h; } throw err; }
}
// الثابت: المحفوظ فورًا، ويُحدَّث في الخلفية
async function swr(e) {
  const h = await caches.match(e.request);
  const keep = /\/(mushaf|quran-tr)\//.test(new URL(e.request.url).pathname) && h && await caches.open(KEEP).then(c => c.match(e.request)).catch(() => null);
  const net = fetch(e.request).then(r => { if (r.ok || r.type === 'opaque') put(keep ? KEEP : RUN, e.request, r.clone()); return r; });
  if (h) { e.waitUntil(net.catch(() => {})); return h; }
  try { return await net; }
  catch (err) { const o = await caches.match(e.request, { ignoreSearch: true }); if (o) return o; throw err; }   // نسخة أقدم من الملف نفسه أفضل من لا شيء
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const u = req.url;
  const ak = audioKey(u);
  if (ak) { // تلاوة: من الجهاز إن حُفظت، وإلا تُترك للشبكة كما هي
    if (SAVED && !SAVED.has(ak)) return;
    e.respondWith(serveAudio(req, ak).catch(() => fetch(req)));
    return;
  }
  const url = new URL(u);
  if (url.origin === self.location.origin) {
    if (req.mode === 'navigate') return e.respondWith(page(e));
    const p = url.pathname;
    if (/\.(mp3|m4a|aac|m3u|txt|xml)$/i.test(p)) return;                        // القوائم وروابط التحميل كما هي
    // ملفات المصحف والترجمات ثابتة (تتغير نادرًا): من المحفوظ فورًا
    if (/\/(mushaf|quran-tr)\//.test(p) || /\.(png|jpe?g|svg|ico|ttf|woff2?|webmanifest)$/i.test(p) || (/\.(js|css)$/i.test(p) && url.search)) return e.respondWith(swr(e));
    if (/\.(json|js|css|html)$/i.test(p)) return e.respondWith(data(e));
    return;
  }
  if (url.hostname === 'fonts.googleapis.com' || url.hostname === 'fonts.gstatic.com') return e.respondWith(swr(e));
});
