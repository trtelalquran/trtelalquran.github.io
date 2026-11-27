// مهارة أليكسا «تلاوات من القرآن» — تشغّل ملفات الأرشيف بنفس ترتيب وموضع مشغّل الموقع المتزامن
const Alexa = require('ask-sdk-core');
const https = require('https');

const PLAYLIST_URL = 'https://trtelalquran.github.io/playlist.json';
const ICON = 'https://trtelalquran.github.io/logo512.jpg';
let PL = null, cum = [], total = 0, epoch = 0, loadedAt = 0;

function getJSON(url, depth = 0) {
  return new Promise((resolve, reject) => {
    https.get(url, { headers: { 'User-Agent': 'alexa-skill' } }, res => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location && depth < 5) {
        res.resume(); return resolve(getJSON(new URL(res.headers.location, url).toString(), depth + 1));
      }
      let b = ''; res.setEncoding('utf8');
      res.on('data', c => b += c); res.on('end', () => { try { resolve(JSON.parse(b)); } catch (e) { reject(e); } });
    }).on('error', reject);
  });
}

async function playlist() {
  if (PL && Date.now() - loadedAt < 3600e3) return PL;
  try {
    const j = await getJSON(PLAYLIST_URL);
    let s = 0; cum = j.items.map(it => { const c = s; s += it.d; return c; });
    PL = j; total = s; epoch = Date.parse(j.epoch) / 1000; loadedAt = Date.now();
  } catch (e) { if (!PL) throw e; }
  return PL;
}

function livePos() {
  const pos = ((Date.now() / 1000 - epoch) % total + total) % total;
  let lo = 0, hi = cum.length - 1;
  while (lo < hi) { const mid = (lo + hi + 1) >> 1; if (cum[mid] <= pos) lo = mid; else hi = mid - 1; }
  return [lo, Math.floor((pos - cum[lo]) * 1000)];
}

// المصدر: السيرفر أولًا (s) ثم الأرشيف (a) إذا فشل الملف
const SERVER_PREFIX = 'https://files.trtel.vip/a/';
const ARCHIVE_PREFIX = 'https://archive.org/download/';
const urlOf = (i, src) => { const u = PL.items[i].u; return src === 'a' || !u.startsWith(ARCHIVE_PREFIX) ? u : SERVER_PREFIX + u.slice(ARCHIVE_PREFIX.length); };
const srcOf = tk => /^q\d+a/.test(String(tk || '')) ? 'a' : 's';
const startOf = tk => { const m = String(tk || '').match(/@(\d+)$/); return m ? +m[1] : 0; };
const tokenOf = (i, src, off) => 'q' + i + (src || 's') + (off ? '@' + off : '');
const idxOf = t => { const n = parseInt(String(t || '').replace(/^q/, ''), 10); return isNaN(n) ? -1 : n; };

// ---------- النصوص لكل لغة ----------
const TXT = {
  ar: { name: 'تلاوات من القرآن', start: 'تلاوات من القرآن الكريم.', help: 'هذه إذاعة تلاوات من القرآن الكريم على مدار الساعة. قل: شغّل، أو التالي، أو إيقاف. هل تريد الاستماع؟',
        bye: '', err: 'عذرًا، تعذّر تشغيل التلاوات الآن. حاول بعد قليل.', fallback: 'يمكنك قول: شغّل، أو التالي، أو إيقاف.' },
  en: { name: 'Quran Recitations', start: 'Recitations from the Holy Quran.', help: 'This is a 24 hour station of Holy Quran recitations. Say play, next, or stop. Would you like to listen?',
        bye: '', err: 'Sorry, the recitations could not be played right now. Please try again shortly.', fallback: 'You can say play, next, or stop.' },
  fr: { name: 'Récitations du Coran', start: 'Récitations du Saint Coran.', help: 'Ceci est une radio de récitations du Saint Coran, vingt-quatre heures sur vingt-quatre. Dites jouer, suivant ou stop. Voulez-vous écouter ?',
        bye: '', err: 'Désolé, impossible de lancer les récitations pour le moment. Réessayez plus tard.', fallback: 'Vous pouvez dire jouer, suivant ou stop.' },
  es: { name: 'Recitaciones del Corán', start: 'Recitaciones del Sagrado Corán.', help: 'Esta es una radio de recitaciones del Sagrado Corán las veinticuatro horas. Di reproducir, siguiente o para. ¿Quieres escuchar?',
        bye: '', err: 'Lo siento, no se pueden reproducir las recitaciones ahora. Inténtalo más tarde.', fallback: 'Puedes decir reproducir, siguiente o para.' },
  de: { name: 'Koran Rezitationen', start: 'Rezitationen aus dem Heiligen Koran.', help: 'Dies ist ein Radio mit Rezitationen des Heiligen Korans rund um die Uhr. Sage abspielen, weiter oder stopp. Möchtest du zuhören?',
        bye: '', err: 'Entschuldigung, die Rezitationen können gerade nicht abgespielt werden. Bitte versuche es später.', fallback: 'Du kannst abspielen, weiter oder stopp sagen.' },
  it: { name: 'Recitazioni del Corano', start: 'Recitazioni del Sacro Corano.', help: 'Questa è una radio di recitazioni del Sacro Corano ventiquattro ore su ventiquattro. Di riproduci, successivo o stop. Vuoi ascoltare?',
        bye: '', err: 'Spiacente, non è possibile riprodurre le recitazioni ora. Riprova più tardi.', fallback: 'Puoi dire riproduci, successivo o stop.' },
  pt: { name: 'Recitações do Alcorão', start: 'Recitações do Sagrado Alcorão.', help: 'Esta é uma rádio de recitações do Sagrado Alcorão vinte e quatro horas por dia. Diga tocar, próxima ou parar. Quer ouvir?',
        bye: '', err: 'Desculpe, não foi possível tocar as recitações agora. Tente novamente mais tarde.', fallback: 'Você pode dizer tocar, próxima ou parar.' },
  hi: { name: 'क़ुरआन तिलावत', start: 'पवित्र क़ुरआन की तिलावत।', help: 'यह पवित्र क़ुरआन की चौबीस घंटे की तिलावत का रेडियो है। चलाओ, अगला या रुको कहें। क्या आप सुनना चाहेंगे?',
        bye: '', err: 'माफ़ कीजिए, अभी तिलावत नहीं चल सकी। थोड़ी देर बाद कोशिश करें।', fallback: 'आप चलाओ, अगला या रुको कह सकते हैं।' },
  ja: { name: 'コーラン朗誦', start: '聖クルアーンの朗誦です。', help: 'これは聖クルアーンの朗誦を二十四時間流すラジオです。再生、次、停止と言ってください。聴きますか？',
        bye: '', err: '申し訳ありません。今は朗誦を再生できません。後でもう一度お試しください。', fallback: '再生、次、停止と言えます。' },
  nl: { name: 'Koran Recitaties', start: 'Recitaties uit de Heilige Koran.', help: 'Dit is een radio met recitaties van de Heilige Koran, dag en nacht. Zeg afspelen, volgende of stop. Wil je luisteren?',
        bye: '', err: 'Sorry, de recitaties kunnen nu niet worden afgespeeld. Probeer het later opnieuw.', fallback: 'Je kunt afspelen, volgende of stop zeggen.' },
};
const t = h => TXT[(Alexa.getLocale(h.requestEnvelope) || 'en').slice(0, 2)] || TXT.en;

function meta(h, i) {
  const it = PL.items[i];
  return { title: it.t, subtitle: (it.r || '') + ' — ' + t(h).name, art: { sources: [{ url: ICON }] }, backgroundImage: { sources: [{ url: ICON }] } };
}

async function playAt(h, i, offsetMs, speak, src) {
  await playlist();
  const rb = h.responseBuilder;
  if (speak) rb.speak(speak);
  rb.addAudioPlayerPlayDirective('REPLACE_ALL', urlOf(i, src), tokenOf(i, src, offsetMs), offsetMs || 0, null, meta(h, i));
  if (!type(h).startsWith('PlaybackController.')) rb.withShouldEndSession(true);
  return rb.getResponse();
}
async function playLive(h, speak) { await playlist(); const [i, off] = livePos(); return playAt(h, i, off, speak); }

const type = h => Alexa.getRequestType(h.requestEnvelope);
const intent = (h, ...names) => type(h) === 'IntentRequest' && names.includes(Alexa.getIntentName(h.requestEnvelope));
const curIdx = h => { const ap = h.requestEnvelope.context && h.requestEnvelope.context.AudioPlayer; return ap ? idxOf(ap.token) : -1; };

const Launch = { canHandle: h => type(h) === 'LaunchRequest' || intent(h, 'PlayIntent', 'AMAZON.ResumeIntent', 'AMAZON.StartOverIntent', 'AMAZON.YesIntent')
                   || type(h) === 'PlaybackController.PlayCommandRequest',
  handle: h => playLive(h, type(h) === 'LaunchRequest' || intent(h, 'PlayIntent') ? t(h).start : null) };

const Next = { canHandle: h => intent(h, 'AMAZON.NextIntent') || type(h) === 'PlaybackController.NextCommandRequest',
  handle: async h => { await playlist(); const c = curIdx(h); const i = c < 0 ? livePos()[0] + 1 : c + 1; return playAt(h, i % PL.items.length, 0); } };

const Prev = { canHandle: h => intent(h, 'AMAZON.PreviousIntent') || type(h) === 'PlaybackController.PreviousCommandRequest',
  handle: async h => { await playlist(); const c = curIdx(h); const i = (c < 0 ? livePos()[0] : c) - 1; return playAt(h, (i + PL.items.length) % PL.items.length, 0); } };

const Stop = { canHandle: h => intent(h, 'AMAZON.PauseIntent', 'AMAZON.StopIntent', 'AMAZON.CancelIntent', 'AMAZON.NoIntent')
                 || type(h) === 'PlaybackController.PauseCommandRequest',
  handle: h => { const rb = h.responseBuilder.addAudioPlayerStopDirective().addAudioPlayerClearQueueDirective('CLEAR_ENQUEUED');
    if (!type(h).startsWith('PlaybackController.')) rb.withShouldEndSession(true); return rb.getResponse(); } };

const Unsupported = { canHandle: h => intent(h, 'AMAZON.LoopOnIntent', 'AMAZON.LoopOffIntent', 'AMAZON.ShuffleOnIntent', 'AMAZON.ShuffleOffIntent', 'AMAZON.RepeatIntent'),
  handle: h => h.responseBuilder.speak(t(h).fallback).withShouldEndSession(true).getResponse() };

const Help = { canHandle: h => intent(h, 'AMAZON.HelpIntent'), handle: h => h.responseBuilder.speak(t(h).help).reprompt(t(h).help).getResponse() };
const Fallback = { canHandle: h => intent(h, 'AMAZON.FallbackIntent', 'AMAZON.NavigateHomeIntent'),
  handle: h => h.responseBuilder.speak(t(h).fallback).reprompt(t(h).fallback).getResponse() };

const NearlyFinished = { canHandle: h => type(h) === 'AudioPlayer.PlaybackNearlyFinished',
  handle: async h => { await playlist(); const c = idxOf(h.requestEnvelope.request.token); const n = ((c < 0 ? livePos()[0] : c) + 1) % PL.items.length;
    return h.responseBuilder.addAudioPlayerPlayDirective('ENQUEUE', urlOf(n, 's'), tokenOf(n, 's'), 0, h.requestEnvelope.request.token, meta(h, n)).getResponse(); } };

const Failed = { canHandle: h => type(h) === 'AudioPlayer.PlaybackFailed',
  handle: async h => { await playlist(); const r = h.requestEnvelope.request; const c = idxOf(r.token);
    console.log('FAILED', r.token, r.error && r.error.message);
    // فشل ملف السيرفر: نفس الملف من الأرشيف من نفس الموضع
    if (c >= 0 && c < PL.items.length && srcOf(r.token) === 's') {
      const cur = (r.currentPlaybackState && r.currentPlaybackState.token === r.token && r.currentPlaybackState.offsetInMilliseconds) || 0;
      const off = Math.max(cur, startOf(r.token));
      return h.responseBuilder.addAudioPlayerPlayDirective('REPLACE_ALL', urlOf(c, 'a'), tokenOf(c, 'a', off), off, null, meta(h, c)).getResponse();
    }
    const n = ((c < 0 ? 0 : c) + 1) % PL.items.length;
    return h.responseBuilder.addAudioPlayerPlayDirective('REPLACE_ALL', urlOf(n, 's'), tokenOf(n, 's'), 0, null, meta(h, n)).getResponse(); } };

const AudioEvents = { canHandle: h => type(h).startsWith('AudioPlayer.') || type(h).startsWith('PlaybackController.'), handle: h => h.responseBuilder.getResponse() };
const SessionEnded = { canHandle: h => type(h) === 'SessionEndedRequest', handle: h => h.responseBuilder.getResponse() };
const SysException = { canHandle: h => type(h) === 'System.ExceptionEncountered', handle: h => h.responseBuilder.getResponse() };

const Errors = { canHandle: () => true, handle: (h, e) => { console.log('ERR', e && e.stack);
  if (type(h).startsWith('AudioPlayer.') || type(h).startsWith('PlaybackController.')) return h.responseBuilder.getResponse();
  return h.responseBuilder.speak(t(h).err).withShouldEndSession(true).getResponse(); } };

exports.handler = Alexa.SkillBuilders.custom()
  .addRequestHandlers(Launch, Next, Prev, Stop, Unsupported, Help, Fallback, NearlyFinished, Failed, AudioEvents, SessionEnded, SysException)
  .addErrorHandlers(Errors)
  .withCustomUserAgent('trtelalquran/v1')
  .lambda();
