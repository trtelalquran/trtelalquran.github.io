/* ترتيل بدون إنترنت (2026-11-28): حفظ التلاوات على الجهاز، والمفضلة، والمشاركة، وآخر موضع استماع.
   ملف مشترك تستخدمه الصفحة الرئيسية وصفحات القرّاء والسور وصفحة «تحميلاتي» (offline.html).
   - التلاوة المحفوظة تُخزَّن في Cache Storage («trtel-audio-v1») بمفتاح رابط الأرشيف، ويشغّلها sw.js من الجهاز.
   - البيانات الصغيرة في localStorage: off:items (المحفوظ)، off:groups (القوائم)، fav (المفضلة)، off:pos (المواضع).
   النصوص: العربية والإنجليزية هنا، وباقي اللغات في i18n/o/<code>.js (يبنيها build_seo_pages.py من i18n/src/<code>.json → o). */
(function () {
  if (window.TrtelOff) return;
  const ARCH = 'https://archive.org/download/', SRV = 'https://files.trtel.vip/a/', AUDIO = 'trtel-audio-v1';
  const me = document.currentScript && document.currentScript.src;
  const BASE = me ? new URL('./', me).href : new URL('/', location.href).href;   // جذر الموقع
  const LG = (document.documentElement.lang || 'ar').split('-')[0];
  if (!/offline\.html$/.test(location.pathname)) try { localStorage.setItem('lastLang', LG); } catch (e) {}   // لغة «تحميلاتي» = آخر لغة تصفّح بها
  const ls = {
    get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { v == null ? localStorage.removeItem(k) : localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  };

  /* ---------- النصوص ---------- */
  const AR = {
    save: 'حفظ للاستماع بدون إنترنت', saved: 'محفوظة على جهازك، اضغط للحذف', saving: 'جارٍ الحفظ…', queued: 'في انتظار الحفظ',
    saveAll: 'حفظ الكل للاستماع بدون إنترنت', savedAll: 'كلها محفوظة على جهازك', confirmAll: 'حفظ {n} تلاوة على جهازك ({mb})؟ تبقى متاحة بدون إنترنت حتى تحذفها.',
    favAdd: 'أضف للمفضلة', favDel: 'احذف من المفضلة', share: 'مشاركة', shareT: 'مشاركة التلاوة', shareNow: 'مشاركة عبر التطبيقات',
    copyLink: 'نسخ رابط التلاوة', copyMp3: 'نسخ رابط ملف mp3', sendFile: 'إرسال ملف mp3', saveFile: 'تنزيل ملف mp3', copied: 'تم النسخ', close: 'إغلاق',
    my: 'تحميلاتي', offline: 'أنت غير متصل بالإنترنت، وتحميلاتك تعمل كالمعتاد.', openMy: 'افتح تحميلاتي',
    quota: 'امتلأت المساحة المتاحة للحفظ. احذف بعض التحميلات ثم أعد المحاولة.', fail: 'تعذّر حفظ «{t}»، سنعيد المحاولة لاحقًا.', fileWait: 'جارٍ تجهيز الملف…',
    delQ: 'حذف {n} تلاوة من جهازك؟', delOne: 'حذف من الجهاز', mb: 'ميجا', gb: 'جيجا', nRec: '{n} تلاوة', done: 'تم حفظ {n} تلاوة على جهازك',
    pageLead: 'ما تحفظه هنا يعمل بدون إنترنت. يستمر الحفظ ما دامت صفحة من ترتيل مفتوحة، ويكمل تلقائيًا عند فتحها مرة أخرى.',
    space: 'مساحة التحميلات: {u}', free: 'المتاح للحفظ: نحو {f}', resume: 'متابعة الاستماع', savedH: 'المحفوظ على جهازك', favH: 'المفضلة',
    favEmpty: 'اضغط ♡ بجانب أي تلاوة في صفحات القرّاء والسور لتجدها هنا.', favSave: 'حفظ المفضلة بدون إنترنت',
    emptyH: 'لم تحفظ شيئًا بعد', emptyD: 'افتح صفحة قارئ أو مصحف أو سورة، واضغط ⬇ بجانب أي تلاوة، أو «حفظ الكل».',
    addFrom: 'أضف من:', navRec: 'القرّاء والمصاحف والتراويح', navSur: 'السور', playAll: 'تشغيل', delAll: 'حذف القائمة', open: 'صفحة القائمة',
    waiting: '{n} في الانتظار', errN: '{n} تعذّر حفظها', retry: 'إعادة المحاولة', play: 'تشغيل', prev: 'السابق', next: 'التالي',
    mushafH: 'المصحف والتفسير', mushafD: 'صفحات المصحف والتفسير والبحث (نحو 7 ميجا)، ومعها ترجمة المعاني المختارة في لغتك.',
    mushafBtn: 'حفظ المصحف بدون إنترنت', mushafOk: 'المصحف محفوظ على جهازك', mushafP: 'جارٍ حفظ المصحف… {p}%', mushafGo: 'افتح المصحف', mushafRe: 'تحديث',
    installH: 'ثبّت ترتيل تطبيقًا', installD: 'يفتح بنافذة مستقلة وأيقونة على سطح المكتب أو الشاشة الرئيسية، ويعمل بدون إنترنت، ويصله كل تحديث للموقع تلقائيًا.', installBtn: 'تثبيت',
    radioNote: 'الإذاعة المباشرة تحتاج اتصالًا بالإنترنت.', live: 'الإذاعة المباشرة', brand: 'ترتيل'
  };
  const EN = {
    save: 'Save for offline listening', saved: 'Saved on your device, tap to remove', saving: 'Saving…', queued: 'Waiting to save',
    saveAll: 'Save all for offline listening', savedAll: 'All saved on your device', confirmAll: 'Save {n} recitations on your device ({mb})? They stay available offline until you remove them.',
    favAdd: 'Add to favourites', favDel: 'Remove from favourites', share: 'Share', shareT: 'Share recitation', shareNow: 'Share via apps',
    copyLink: 'Copy recitation link', copyMp3: 'Copy mp3 file link', sendFile: 'Send mp3 file', saveFile: 'Download mp3 file', copied: 'Copied', close: 'Close',
    my: 'My downloads', offline: 'You are offline. Your downloads still work.', openMy: 'Open my downloads',
    quota: 'Storage is full. Remove some downloads and try again.', fail: 'Could not save “{t}”. We will retry later.', fileWait: 'Preparing the file…',
    delQ: 'Remove {n} recitations from your device?', delOne: 'Remove from device', mb: 'MB', gb: 'GB', nRec: '{n} recitations', done: '{n} recitations saved on your device',
    pageLead: 'What you save here works without internet. Saving continues while any Tartil page is open, and resumes when you open one again.',
    space: 'Downloads use {u}', free: 'Available for saving: about {f}', resume: 'Continue listening', savedH: 'Saved on your device', favH: 'Favourites',
    favEmpty: 'Tap ♡ next to any recitation on the reciter and surah pages to find it here.', favSave: 'Save favourites for offline',
    emptyH: 'Nothing saved yet', emptyD: 'Open a reciter, Mushaf or surah page and tap ⬇ next to a recitation, or “Save all”.',
    addFrom: 'Add from:', navRec: 'Reciters, Mushafs and Tarawih', navSur: 'Surahs', playAll: 'Play', delAll: 'Remove list', open: 'List page',
    waiting: '{n} waiting', errN: '{n} could not be saved', retry: 'Retry', play: 'Play', prev: 'Previous', next: 'Next',
    mushafH: 'Mushaf and tafsir', mushafD: 'The Mushaf pages, tafsir and search (about 7 MB), with the translation of meanings chosen for your language.',
    mushafBtn: 'Save the Mushaf for offline', mushafOk: 'The Mushaf is saved on your device', mushafP: 'Saving the Mushaf… {p}%', mushafGo: 'Open the Mushaf', mushafRe: 'Update',
    installH: 'Install Tartil as an app', installD: 'Opens in its own window with an icon on your desktop or home screen, works offline, and gets every site update automatically.', installBtn: 'Install',
    radioNote: 'The live radio needs an internet connection.', live: 'Live radio', brand: 'Tartil'
  };
  let D = LG === 'ar' ? AR : Object.assign({}, EN, (window.TRL && window.TRL.o) || window.TRO || {});
  const T = (k, m) => String(D[k] ?? EN[k] ?? k).replace(/\{(\w+)\}/g, (x, n) => m && m[n] != null ? m[n] : '');
  const size = b => b >= 1e9 ? (b / 1e9).toFixed(1) + ' ' + T('gb') : Math.max(1, Math.round(b / 1e6)) + ' ' + T('mb');
  if (LG !== 'ar' && !(window.TRL && window.TRL.o) && !window.TRO && LG !== 'en') {   // نصوص اللغة عند الحاجة
    const s = document.createElement('script'); s.src = BASE + 'i18n/o/' + LG + '.js'; s.async = true;
    s.onload = () => { if (window.TRO) { D = Object.assign({}, EN, window.TRO); onChange({ k: 'lang' }); } }; document.head.appendChild(s);
  }

  /* ---------- عامل الخدمة ---------- */
  const swOk = 'serviceWorker' in navigator && (location.protocol === 'https:' || location.hostname === 'localhost');
  if (swOk && !navigator.serviceWorker.controller) navigator.serviceWorker.register(BASE + 'sw.js').catch(() => {});
  const canSave = swOk && 'caches' in window;   // بدون عامل الخدمة أو Cache Storage (تصفح خاص في بعض المتصفحات) لا نعرض الحفظ أصلًا
  const tellSW = m => { if (!swOk) return; navigator.serviceWorker.ready.then(r => r.active && r.active.postMessage(m)).catch(() => {}); };
  // صفحات اللغة الأساسية تُحفظ مسبقًا لتفتح بدون إنترنت ولو لم تُزر (الرئيسية والمصحف وتحميلاتي ونصوص اللغة)
  if (navigator.onLine && window === top) setTimeout(() => { const R = BASE + (LG === 'ar' ? '' : LG + '/');
    tellSW({ k: 'warm', urls: [R + 'index.html', R + 'mushaf.html', R + 'surahs.html', R + 'reciters.html', BASE + 'offline.html'].concat(LG === 'ar' ? [] : [BASE + 'i18n/' + LG + '.js', BASE + 'i18n/o/' + LG + '.js']) }); }, 2000);

  /* ---------- البيانات ---------- */
  const canon = u => u && u.indexOf(SRV) === 0 ? ARCH + u.slice(SRV.length) : u;
  const items = () => ls.get('off:items', {}), groups = () => ls.get('off:groups', {});
  const setItems = v => ls.set('off:items', v), setGroups = v => ls.set('off:groups', v);
  const favs = () => ls.get('fav', []);
  const isFav = u => favs().some(x => x.u === u);
  const state = u => (items()[u] || {}).st || '';     // q | ok | err
  let bc = null; try { bc = new BroadcastChannel('trtel-off'); bc.onmessage = e => onChange(e.data); } catch (e) {}
  const listeners = [];
  function onChange(m) { paintAll(); listeners.forEach(f => { try { f(m || {}); } catch (e) {} }); }
  const changed = m => { onChange(m); if (bc) try { bc.postMessage(m || {}); } catch (e) {} };

  function toggleFav(t) {
    let f = favs(); const i = f.findIndex(x => x.u === t.u);
    if (i >= 0) f.splice(i, 1); else f.unshift({ u: t.u, t: t.t, r: t.r || '', d: t.d || 0, pg: t.pg || '', at: Date.now() });
    ls.set('fav', f.slice(0, 1000)); changed({ k: 'fav' });
  }

  /* حفظ مجموعة تلاوات: g معرّف القائمة (مسار صفحتها، أو fav، أو one) */
  function save(list, g, gname, gpg) {
    // داخل تطبيق أندرويد: إن عرّف التطبيق TrtelApp.save يتولى التنزيل بمشغّله ومخزنه، ونتوقف هنا (يعيد false ليتركه للمتصفح)
    if (window.TrtelApp && typeof TrtelApp.save === 'function') { const r = TrtelApp.save(list.map(t => Object.assign({}, t, { u: canon(t.u) || t.u })), g, gname, gpg); if (r !== false) return typeof r === 'number' ? r : list.length; }
    if (!canSave) return 0;
    const it = items(), gs = groups(); let n = 0;
    list.forEach(t => { const u = canon(t.u); if (!u) return; const o = it[u] || {};
      o.t = t.t || o.t || ''; o.r = t.r || o.r || ''; o.d = t.d || o.d || 0; o.pg = t.pg || o.pg || ''; o.gs = Array.from(new Set([...(o.gs || []), g]));
      if (o.st !== 'ok') { o.st = 'q'; o.at = Date.now(); n++; } it[u] = o; });
    Object.values(it).forEach(o => { if (o.st === 'err' && o.full) { o.st = 'q'; o.tries = 0; delete o.full; } });   // طلب حفظ جديد: نجرّب معه ما أوقفه امتلاء التخزين
    const old = gs[g] || {};
    gs[g] = { name: gname || old.name || g, pg: gpg || old.pg || '', at: old.at || Date.now(), us: Array.from(new Set([...(old.us || []), ...list.map(t => canon(t.u))])) };
    setItems(it); setGroups(gs); changed({ k: 'q' });
    if (navigator.storage && navigator.storage.persist) navigator.storage.persist().catch(() => {});
    run(); return n;
  }

  /* حذف: مع g تُحذف القائمة وتبقى تلاواتها المحفوظة ضمن قوائم أخرى، وبدونه تُحذف التلاوات من الجهاز ومن كل القوائم */
  async function remove(us, g) {
    const it = items(), gs = groups(), gone = [];
    if (g) { delete gs[g]; us.forEach(u => { const o = it[u]; if (!o) return; o.gs = (o.gs || []).filter(x => x !== g); if (!o.gs.length) gone.push(u); }); }
    else us.forEach(u => { if (it[u]) gone.push(u); });
    gone.forEach(u => delete it[u]);
    let again = false; if (gone.length) Object.values(it).forEach(o => { if (o.st === 'err' && o.full) { o.st = 'q'; o.tries = 0; delete o.full; again = true; } });   // فُرّغت مساحة: يكمل ما أوقفه امتلاء التخزين
    Object.keys(gs).forEach(k => { gs[k].us = (gs[k].us || []).filter(u => it[u]); if (!gs[k].us.length) delete gs[k]; });
    setItems(it); setGroups(gs);
    const c = await caches.open(AUDIO).catch(() => null); if (c) for (const u of gone) await c.delete(u).catch(() => {});
    tellSW({ k: 'saved', del: gone }); changed({ k: 'del' }); if (again) run();
  }

  /* ---------- التنزيل: واحد بعد واحد (اثنان معًا)، ويكمل عند العودة لأي صفحة من ترتيل ---------- */
  let running = false; const prog = {};
  async function fetchAudio(u, signal) {
    const tries = [SRV + u.slice(ARCH.length), u];
    let last, gone = 0;
    for (const x of tries) { try { const r = await fetch(x, { mode: 'cors', credentials: 'omit', cache: 'no-store', signal }); if (r.ok && r.body) return r; last = new Error(r.status); if (r.status === 404 || r.status === 410) gone++; } catch (e) { last = e; if (signal && signal.aborted) break; } }
    if (gone === tries.length && last) last.gone = true;   // غير موجود في المصدرين: لا فائدة من إعادة المحاولة تلقائيًا
    throw last || new Error('fetch');
  }
  const STALL = 45000, sleep = ms => new Promise(r => setTimeout(r, ms));
  const quotaErr = () => { const e = new Error('quota'); e.name = 'QuotaExceededError'; return e; };
  async function dl1(u) {
    // مهلة توقف: إن لم تصل بيانات 45 ثانية نقطع الطلب ليُعاد لاحقًا بدل أن يعلّق الطابور كله
    const ac = new AbortController(); let wd = setTimeout(() => ac.abort(), STALL);
    const kick = () => { clearTimeout(wd); wd = setTimeout(() => ac.abort(), STALL); };
    try {
      const r = await fetchAudio(u, ac.signal), len = +r.headers.get('content-length') || 0; let got = 0, tk = 0; kick();
      // لا نبدأ ملفًا لا تكفيه المساحة الباقية
      if (len && navigator.storage && navigator.storage.estimate) { const e = await navigator.storage.estimate().catch(() => null); if (e && e.quota && e.quota - (e.usage || 0) < len + 5e6) { ac.abort(); throw quotaErr(); } }
      const c = await caches.open(AUDIO);
      const h = { 'Content-Type': r.headers.get('content-type') || 'audio/mpeg' }; if (len) h['Content-Length'] = String(len);
      let body = r.body;
      if (body.pipeThrough && typeof TransformStream === 'function') body = body.pipeThrough(new TransformStream({ transform(ch, ctl) { kick(); got += ch.byteLength; prog[u] = len ? got / len : 0; if (Date.now() - tk > 500) { tk = Date.now(); paintProg(u); if (bc) try { bc.postMessage({ k: 'p', u, p: prog[u] }); } catch (e) {} } ctl.enqueue(ch); } }));
      else clearTimeout(wd);   // متصفح قديم بلا TransformStream: نحفظ بلا نسبة تقدم
      await c.put(u, new Response(body, { headers: h }));
      if (!got) { const m = await c.match(u); got = m ? (await m.blob()).size : 0; }
      if (!got || (len && got < len)) { await c.delete(u); throw new Error('short'); }
      return got;
    } finally { clearTimeout(wd); }
  }
  async function loop() {
    let ok = 0;
    for (;;) {
      const it = items(), q = Object.keys(it).filter(u => it[u].st === 'q').sort((a, b) => (it[a].at || 0) - (it[b].at || 0));
      if (!q.length) break;
      const batch = q.slice(0, 2);
      const res = await Promise.all(batch.map(u => dl1(u).then(n => ({ u, n }), e => ({ u, e }))));
      const now = items(); let bad = 0;
      for (const x of res) {
        delete prog[x.u]; const o = now[x.u]; if (!o) { if (!x.e) caches.open(AUDIO).then(c => c.delete(x.u)); continue; }
        if (x.e) {
          if (x.e && (x.e.name === 'QuotaExceededError' || /quota/i.test(String(x.e)))) {
            // امتلأ التخزين: نوقف كل المنتظر (لا نعيد تنزيله مع كل فتح صفحة)، ويكمل بعد حذف شيء أو بزر «إعادة المحاولة»
            Object.values(now).forEach(v => { if (v.st === 'q') { v.st = 'err'; v.full = 1; } }); setItems(now); toast(T('quota')); changed({ k: 'err' }); return ok; }
          o.tries = (o.tries || 0) + 1; o.at = Date.now(); bad = Math.max(bad, o.tries);
          if (!navigator.onLine) { setItems(now); return ok; }   // انقطع الإنترنت: يكمل لاحقًا
          if (x.e.gone || o.tries >= 3) { o.st = 'err'; if (x.e.gone) o.gone = 1; toast(T('fail', { t: o.t })); }
        } else { o.st = 'ok'; o.sz = x.n; o.tries = 0; delete o.full; delete o.gone; o.done = Date.now(); ok++; tellSW({ k: 'saved', add: [x.u] }); }
      }
      setItems(now); changed({ k: 'ok' });
      if (bad) await sleep(Math.min(30000, 4000 * bad));   // تمهّل قبل إعادة المحاولة على شبكة متعثرة
    }
    return ok;
  }
  function run() {
    if (running || !canSave) return; running = true;
    const go = () => loop().then(n => { if (n) toast(T('done', { n })); }).catch(() => {}).finally(() => { running = false; });
    // قفل واحد بين كل التبويبات: إن كان تبويب آخر ينزّل ننتظر دورنا، فإن أُغلق ذاك التبويب أكملنا نحن ما بقي
    if (navigator.locks && navigator.locks.request) navigator.locks.request('trtel-dl', go).catch(() => { running = false; });
    else go();
  }
  addEventListener('online', () => { const it = items(); let f = false; Object.values(it).forEach(o => { if (o.st === 'err' && !o.full && !o.gone) { o.st = 'q'; o.tries = 0; f = true; } }); if (f) setItems(it); run(); banner(); });
  addEventListener('offline', banner);
  setTimeout(run, 1500);
  // تحقق أن المحفوظ موجود فعلًا (قد يمسح المتصفح التخزين)
  async function verify() {
    if (!canSave) return;
    const c = await caches.open(AUDIO), ks = new Set((await c.keys()).map(r => r.url)), it = items(); let f = false;
    Object.keys(it).forEach(u => { if (it[u].st === 'ok' && !ks.has(u)) { it[u].st = 'q'; f = true; } });
    if (f) { setItems(it); changed({ k: 'q' }); run(); }
  }

  /* ---------- المشاركة ---------- */
  let tm; function toast(t) {
    let e = document.getElementById('toast') || document.getElementById('otoast');
    if (!e) { e = document.createElement('div'); e.id = 'otoast'; e.className = 'otoast'; document.body.appendChild(e); }
    e.textContent = t; e.hidden = false; clearTimeout(tm); tm = setTimeout(() => e.hidden = true, 3200);
  }
  function copy(t) {
    const done = () => toast(T('copied'));
    const legacy = () => { const a = document.createElement('textarea'); a.value = t; a.style.cssText = 'position:fixed;opacity:0'; document.body.appendChild(a); a.select(); try { document.execCommand('copy'); done(); } catch (e) { toast(t); } a.remove(); };
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(t).then(done, legacy); else legacy();
  }
  const fname = t => (t.t + (t.r ? ' - ' + t.r : '')).replace(/[\\/:*?"<>|]+/g, ' ').slice(0, 120) + '.mp3';
  async function fileOf(t) {
    const u = canon(t.u), c = await caches.open(AUDIO).catch(() => null), h = c && await c.match(u);
    const r = h || await fetchAudio(u); const b = await r.blob();
    return new File([b], fname(t), { type: 'audio/mpeg' });
  }
  function share(t) {
    const u = canon(t.u), link = t.pg || u, txt = t.t + (t.r ? ' · ' + t.r : '');
    const sh = document.createElement('div'); sh.className = 'oshade';
    const canShare = !!navigator.share, canFiles = !!(navigator.canShare && window.File);
    sh.innerHTML = '<div class="osheet" role="dialog" aria-modal="true"><h3></h3><p class="osub"></p><div class="obtns">' +
      (canShare ? '<button type="button" data-a="sh"></button>' : '') + '<button type="button" data-a="cl"></button><button type="button" data-a="cm"></button>' +
      '<button type="button" data-a="fi"></button></div><button type="button" class="ox" data-a="x"></button></div>';
    sh.querySelector('h3').textContent = T('shareT'); sh.querySelector('.osub').textContent = txt;
    const lab = { sh: T('shareNow'), cl: T('copyLink'), cm: T('copyMp3'), fi: canFiles ? T('sendFile') : T('saveFile'), x: T('close') };
    sh.querySelectorAll('[data-a]').forEach(b => b.textContent = lab[b.dataset.a]);
    if (link === u) sh.querySelector('[data-a="cm"]').remove();
    const close = () => { sh.remove(); removeEventListener('keydown', esc); }, esc = e => { if (e.key === 'Escape') close(); };
    addEventListener('keydown', esc);
    sh.onclick = async e => {
      const b = e.target.closest('[data-a]'); if (e.target === sh) return close(); if (!b) return;
      const a = b.dataset.a;
      if (a === 'x') return close();
      if (a === 'sh') { close(); navigator.share({ title: txt, text: txt, url: link }).catch(() => {}); return; }
      if (a === 'cl') { close(); copy(txt + '\n' + link); return; }
      if (a === 'cm') { close(); copy(u); return; }
      if (a === 'fi') {
        b.disabled = true; b.textContent = T('fileWait');
        try {
          const f = await fileOf(t);
          if (canFiles && navigator.canShare({ files: [f] })) { close(); await navigator.share({ files: [f], title: txt, text: txt }).catch(() => {}); return; }
          const x = URL.createObjectURL(f), a2 = document.createElement('a'); a2.href = x; a2.download = f.name; document.body.appendChild(a2); a2.click(); a2.remove();
          setTimeout(() => URL.revokeObjectURL(x), 60000); close();
        } catch (err) { close(); const a2 = document.createElement('a'); a2.href = u; a2.download = ''; a2.target = '_blank'; a2.rel = 'noopener'; document.body.appendChild(a2); a2.click(); a2.remove(); }
      }
    };
    document.body.appendChild(sh); (sh.querySelector('.obtns button') || sh).focus();
  }

  /* ---------- أزرار التلاوات في صفحات القرّاء والسور ---------- */
  const IC = {
    heart: '<svg viewBox="0 0 24 24"><path d="M12 20s-7-4.4-9.2-8.6C1.3 8.4 3 5 6.3 5c2 0 3.2 1.1 3.9 2.2.4.6 1.2.6 1.6 0C12.5 6.1 13.7 5 15.7 5 19 5 20.7 8.4 19.2 11.4 17 15.6 12 20 12 20z"/></svg>',
    down: '<svg viewBox="0 0 24 24"><path d="M12 4v11M7.5 10.5 12 15l4.5-4.5M5 19h14"/></svg>',
    ok: '<svg viewBox="0 0 24 24"><path d="M5 12.5 10 17l9-10"/></svg>',
    share: '<svg viewBox="0 0 24 24"><circle cx="18" cy="5.5" r="2.5"/><circle cx="6" cy="12" r="2.5"/><circle cx="18" cy="18.5" r="2.5"/><path d="m8.2 10.8 7.6-4.1M8.2 13.2l7.6 4.1"/></svg>'
  };
  const pageUrl = () => location.href.split('#')[0].split('?')[0];
  const groupName = () => { const h = document.querySelector('h1'); return h ? h.textContent.trim() : document.title; };
  function trackOf(li, i) {
    const b = li.querySelector('.t b'), sm = li.querySelector('.t small'), u = li.dataset.u;
    const extra = sm ? [...sm.childNodes].map(n => n.textContent).join('').split(' · ') : [];
    const dur = (extra[0] || '').trim().split(':').reduce((a, x) => a * 60 + (+x || 0), 0);
    const inSurah = /\/surah\/\d+\.html$/.test(location.pathname);
    const title = b ? b.textContent.trim() : '';
    // في صفحة القارئ: العنوان اسم التلاوة والقارئ عنوان الصفحة؛ وفي صفحة السورة: العنوان اسم القارئ
    return inSurah ? { u, t: groupName(), r: title, d: dur, pg: pageUrl() + '#n=' + (i + 1) } : { u, t: title, r: groupName(), d: dur, pg: pageUrl() + '#n=' + (i + 1) };
  }
  let lis = [];
  function enhance() {
    lis = [...document.querySelectorAll('ul.tr li[data-u]')];
    if (!lis.length) return;
    lis.forEach((li, i) => {
      li.dataset.n = i + 1;
      const box = document.createElement('span'); box.className = 'oact';
      box.innerHTML = `<button type="button" class="ob ofav">${IC.heart}</button>${canSave ? `<button type="button" class="ob osv">${IC.down}<i></i></button>` : ''}<button type="button" class="ob osh">${IC.share}</button>`;
      const dl = li.querySelector('.dl'); li.insertBefore(box, dl || null);
    });
    document.addEventListener('click', e => {
      const b = e.target.closest('.oact .ob'); if (!b) return;
      const li = b.closest('li'), t = trackOf(li, +li.dataset.n - 1);
      if (b.classList.contains('ofav')) toggleFav(t);
      else if (b.classList.contains('osh')) share(t);
      else { const s = state(canon(t.u)); if (s === 'ok' || s === 'q') remove([canon(t.u)]); else save([t], location.pathname, groupName(), pageUrl()); }
    });
    // زر «حفظ الكل» في صفحات القرّاء والمصاحف والتراويح
    if (canSave && /\/reciter\//.test(location.pathname)) {
      const chips = document.querySelector('.chips');
      if (chips) { const a = document.createElement('button'); a.type = 'button'; a.className = 'osaveall'; a.innerHTML = IC.down + '<span></span>'; chips.insertBefore(a, chips.firstChild);
        a.onclick = async () => {
          const all = lis.map(trackOf), left = all.filter(t => state(canon(t.u)) !== 'ok');
          if (!left.length) { location.href = BASE + 'offline.html'; return; }
          const mb = await listMb(); const est = mb ? size(mb * 1e6 * left.length / all.length) : '';
          if (!confirm(T('confirmAll', { n: left.length, mb: est }).replace(' ()', ''))) return;
          save(all, location.pathname, groupName(), pageUrl());
        }; }
    }
    // رابط بموضع تلاوة (#n=5): نبرزها
    const m = /#n=(\d+)/.exec(location.hash), li = m && lis[+m[1] - 1];
    if (li) { li.classList.add('on'); setTimeout(() => li.scrollIntoView({ block: 'center' }), 200); }
    paintAll();
  }
  async function listMb() {
    try { const L = await (await fetch(BASE + 'lists.json')).json(), slug = location.pathname.split('/').pop().replace('.html', '');
      for (const k of Object.keys(L)) for (const x of (Array.isArray(L[k]) ? L[k] : [])) if (x && x.m3u && x.m3u.endsWith('/' + slug + '.m3u')) return x.mb || 0; } catch (e) {}
    return 0;
  }
  function paintProg(u) { lis.forEach(li => { if (canon(li.dataset.u) === u) { const i = li.querySelector('.osv i'); if (i) i.style.setProperty('--p', Math.round((prog[u] || 0) * 100) + '%'); } }); }
  function paintAll() {
    if (!lis.length) return;
    const it = items(), f = new Set(favs().map(x => x.u)); let all = true;
    lis.forEach(li => {
      const u = canon(li.dataset.u), s = (it[u] || {}).st || '', fv = li.querySelector('.ofav'), sv = li.querySelector('.osv'), sh = li.querySelector('.osh');
      if (!fv) return;
      fv.classList.toggle('on', f.has(u)); fv.title = fv.ariaLabel = T(f.has(u) ? 'favDel' : 'favAdd'); fv.setAttribute('aria-pressed', f.has(u));
      if (sv) sv.dataset.s = s, sv.innerHTML = (s === 'ok' ? IC.ok : IC.down) + '<i></i>'; if (sv) sv.title = sv.ariaLabel = T(s === 'ok' ? 'saved' : s === 'q' ? 'saving' : 'save');
      sh.title = sh.ariaLabel = T('share');
      if (s !== 'ok') all = false; if (s === 'q') paintProg(u);
    });
    const a = document.querySelector('.osaveall'); if (a) { a.querySelector('span').textContent = T(all ? 'savedAll' : 'saveAll'); a.classList.toggle('on', all); }
  }

  /* ---------- آخر موضع استماع لكل تلاوة (مشغّل صفحات القرّاء والسور) ---------- */
  const pos = () => ls.get('off:pos', {});
  function setPos(u, t, d) {
    const p = pos(); if (!u) return;
    if (t < 15 || (d && d - t < 20)) delete p[u]; else p[u] = Math.floor(t);
    const ks = Object.keys(p); if (ks.length > 300) ks.slice(0, ks.length - 300).forEach(k => delete p[k]);
    ls.set('off:pos', p);
  }
  function trackPos(au, getU) {
    let last = 0;
    au.addEventListener('timeupdate', () => { if (Date.now() - last < 4000) return; last = Date.now(); setPos(canon(getU()), au.currentTime, au.duration); });
    au.addEventListener('pause', () => setPos(canon(getU()), au.currentTime, au.duration));
    au.addEventListener('ended', () => setPos(canon(getU()), 0, 0));
    au.addEventListener('loadedmetadata', () => { const p = pos()[canon(getU())]; if (p && p > 15 && (!au.duration || au.duration - p > 20) && au.currentTime < 2) try { au.currentTime = p; } catch (e) {} });
  }
  const bar = document.getElementById('bar'), bau = bar && bar.querySelector('audio');
  if (bau) trackPos(bau, () => bau.dataset.u);

  /* ---------- شريط «غير متصل» ---------- */
  function banner() {
    let b = document.getElementById('obanner');
    let shut = false; try { shut = !!sessionStorage.getItem('offBan'); } catch (e) {}
    if (navigator.onLine || shut || window !== top || /offline\.html$/.test(location.pathname)) { if (b) b.remove(); return; }
    if (!b) { b = document.createElement('div'); b.id = 'obanner'; b.className = 'obanner'; b.setAttribute('role', 'status'); document.body.appendChild(b); }
    b.innerHTML = '<span></span><a></a><button type="button">×</button>'; b.children[0].textContent = T('offline'); b.children[1].textContent = T('openMy'); b.children[1].href = BASE + 'offline.html';
    b.children[2].ariaLabel = T('close'); b.children[2].onclick = () => { try { sessionStorage.setItem('offBan', '1'); } catch (e) {} b.remove(); };
  }

  /* ---------- التنسيق ---------- */
  const css = `.oact{display:inline-flex;gap:4px;flex:none}.ob{width:30px;height:30px;border-radius:50%;border:1px solid var(--line,#dccfae);background:transparent;color:var(--mut,#7d6f52);display:grid;place-items:center;cursor:pointer;padding:0;position:relative}
.ob svg{width:16px;height:16px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}.ob:hover{color:var(--ink,#22303f);border-color:var(--gold,#a8873a)}
.ofav.on{color:#c0392b;border-color:#c0392b55}.ofav.on svg{fill:currentColor}.osv[data-s="ok"]{color:#2e7d32;border-color:#2e7d3266}
.osv[data-s="q"] i{position:absolute;inset:-1px;border-radius:50%;background:conic-gradient(var(--gold,#a8873a) var(--p,0%),transparent 0);-webkit-mask:radial-gradient(circle,transparent 13px,#000 13.5px);mask:radial-gradient(circle,transparent 13px,#000 13.5px)}
.osaveall{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--gold,#a8873a);background:var(--on,#22303f);color:var(--on-ink,#f5efe2);border-radius:999px;padding:4px 12px;font:500 14px inherit;font-family:inherit;cursor:pointer}
.osaveall svg{width:16px;height:16px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round}.osaveall.on{background:transparent;color:#2e7d32;border-color:#2e7d3266}
@media(max-width:520px){ul.tr li{flex-wrap:wrap;row-gap:4px}ul.tr li .t{flex:1 1 calc(100% - 50px)}.oact{order:3;margin-inline-start:44px}ul.tr .dl{order:4;margin-inline-start:auto}}
.oshade{position:fixed;inset:0;background:#0008;display:grid;place-items:end center;z-index:99;padding:12px}
.osheet{width:min(440px,100%);background:var(--bg2,#fbf6ea);color:var(--ink,#22303f);border:1px solid var(--line,#dccfae);border-radius:18px;padding:18px;font-family:inherit;box-shadow:0 10px 40px #0004}
.osheet h3{margin:0 0 2px;font-size:18px}.osub{margin:0 0 12px;color:var(--mut,#7d6f52);font-size:14px}.obtns{display:grid;gap:8px}
.obtns button,.ox{font:inherit;font-size:15px;padding:10px 12px;border-radius:12px;border:1px solid var(--line,#dccfae);background:var(--bg,#f5efe2);color:inherit;cursor:pointer;text-align:start}
.obtns button:first-child{background:var(--on,#22303f);color:var(--on-ink,#f5efe2);border-color:transparent}.ox{width:100%;margin-top:8px;text-align:center;background:transparent}
.obanner{position:fixed;inset-inline:12px;top:10px;z-index:98;display:flex;gap:10px;align-items:center;justify-content:center;flex-wrap:wrap;background:#7a4b00;color:#fff;border-radius:12px;padding:8px 14px;font-size:14px;box-shadow:0 6px 24px #0003}
.obanner a{color:#fff;font-weight:600}.obanner button{background:none;border:0;color:#fff;font-size:20px;line-height:1;cursor:pointer;padding:0 4px}.otoast{position:fixed;bottom:22px;left:50%;transform:translateX(-50%);background:#22303f;color:#fff;padding:9px 16px;border-radius:12px;z-index:100;font-size:14px;max-width:90vw}`;
  const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);

  window.TrtelOff = { save, remove, items, groups, favs, isFav, toggleFav, share, state, canon, size, T, D: () => D, on: f => listeners.push(f), prog, run, verify, canSave, trackPos, pos, setPos, copy, toast, BASE, AUDIO, ARCH, SRV, ls };
  const start = () => { enhance(); banner(); };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
