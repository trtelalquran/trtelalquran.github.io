# صفحة إذاعة «تلاوات من القرآن» (ويب ثابت)

تعمل كإذاعة في متصفح المستمع بلا سيرفر بث: كل الزوار يسمعون السورة نفسها في اللحظة نفسها
(الموضع = (الوقت الآن − epoch) باقي القسمة على مجموع المدد)، والصوت من archive.org مباشرة.

## الملفات
- `index.html` — الصفحة كاملة (مشغّل، مشاركة، روابط، تحميل).
- `playlist.json` — من radio.m3u بنفس الترتيب والمدد (958 عنصرًا ≈ 13.7 يومًا للدورة).
- `downloads.json` — 38 قارئًا: عدد الملفات والحجم ورابط الصفحة وZIP (`archive.org/compress/<id>`).
- `links.json` — روابطنا؛ عدّلها هنا، والرابط الفارغ لا يظهر.
- `logo512.jpg`, `logo1200.jpg` — الشعار.
- `build_playlist_json.py` — يعيد بناء playlist.json وdownloads.json من الأرشيف: `python build_playlist_json.py`

## النشر على GitHub Pages
1. أنشئ مستودعًا عامًا وارفع محتويات هذا المجلد إلى جذره.
2. Settings ← Pages ← Deploy from branch ← main / root.
3. المستودع: `trtelalquran.github.io` والرابط https://trtelalquran.github.io/ (og:image وcanonical مضبوطان عليه مسبقًا). ملف `.nojekyll` موجود.

## ملاحظات
- لا تغيّر `epoch` في playlist.json بعد النشر (يغيّر موضع البث للجميع).
- إذا تغيّرت radio.m3u أعد تشغيل السكربت وارفع playlist.json الجديد.
- التجربة محليًا: `python -m http.server 8765` داخل المجلد ثم افتح http://127.0.0.1:8765
