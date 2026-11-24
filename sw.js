/* عامل خدمة بسيط لتمكين تثبيت الموقع على الشاشة الرئيسية.
   لا يخزّن شيئًا: كل الطلبات (الصفحة والصوت والبث) تذهب للشبكة كما هي. */
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', () => {});
