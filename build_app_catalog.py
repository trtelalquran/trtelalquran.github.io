#!/usr/bin/env python3
"""يبني app/catalog.json: فهرس المكتبة الذي يقرؤه تطبيق أندرويد (أندرويد أوتو).

المصادر: lists.json (الترتيب والأسماء)، all-urls.txt وstations.json (المصاحف الكاملة والتراويح)،
وlists/*.m3u (المصاحف غير المكتملة والقرّاء). يُشغَّل بعد أي تحديث للقوائم:
    python3 build_app_catalog.py
المسار p نسبي بعد download/، والتطبيق يشغّله من files.trtel.vip/a/ ثم archive.org احتياطًا.
"""
import json, os, re, urllib.parse, collections, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
PREFIX = "trtel-alquran-"


def load(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return json.load(f)


def rel(url):
    return urllib.parse.unquote(url.split("/download/", 1)[1])


def surah_title(fn):
    base = re.sub(r"\.mp3$", "", fn)
    base = re.sub(r"^\d{3}(-\d{3})?\s+", "", base)
    base = base.replace(" (جزء)", "")
    return base if base.startswith(("من ", "مختارات")) else "سورة " + base


def read_m3u(path, strip_suffix):
    items, title, dur = [], None, 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#EXTINF:"):
                d, _, t = line[8:].partition(",")
                dur = int(float(d)) if d.strip("-").replace(".", "").isdigit() else 0
                title = t
            elif line and not line.startswith("#"):
                t = title or surah_title(rel(line).split("/", 1)[1])
                t = re.sub(r"^سورة (?=(من |مختارات))", "", t)
                for suf in strip_suffix:
                    if suf and t.endswith(" - " + suf):
                        t = t[: -len(" - " + suf)]
                items.append({"t": t, "p": rel(line), "d": max(dur, 0)})
                title, dur = None, 0
    return items


def main():
    lists = load("lists.json")
    stations = load("stations.json")
    durs = {s["id"]: s["d"] for k in ("mushaf", "tarawih") for s in stations[k]}
    by_item = collections.OrderedDict()
    with open(os.path.join(ROOT, "all-urls.txt"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                p = rel(line)
                by_item.setdefault(p.split("/", 1)[0], []).append(p)

    def slug(entry):
        return entry["m3u"].rsplit("/", 1)[1][:-4]

    def from_urls(entry):
        sid = slug(entry)
        paths = sorted(by_item.get(PREFIX + sid, []))
        d = durs.get(sid, [])
        ok = len(d) == len(paths)
        return [{"t": surah_title(p.split("/", 1)[1]), "p": p, "d": d[i] if ok else 0}
                for i, p in enumerate(paths)]

    def from_m3u(entry, name):
        path = os.path.join(ROOT, "lists", slug(entry) + ".m3u")
        return read_m3u(path, [name, entry["name"]]) if os.path.exists(path) else []

    def reciter_of(entry):
        return entry["name"].split(" - ", 1)[1] if " - " in entry["name"] else entry["name"]

    sections = []

    groups = []
    for e in lists["mushaf"]:
        groups.append({"id": slug(e), "t": reciter_of(e), "s": e["name"].split(" - ")[0], "items": from_urls(e)})
    for e in lists["partial"]:
        groups.append({"id": slug(e), "t": reciter_of(e), "s": "مصحف غير مكتمل", "items": from_m3u(e, reciter_of(e))})
    sections.append({"id": "mushaf", "t": "المصاحف", "en": "Mushafs", "groups": groups})

    groups = []
    for e in sorted(lists["tarawih"], key=lambda x: -x.get("sort", 0)):
        year = re.search(r"(\d{4})هـ", e["name"])
        groups.append({"id": slug(e), "t": "تراويح " + (year.group(1) + "هـ" if year else e["name"]),
                       "s": "المسجد النبوي", "items": from_urls(e)})
    sections.append({"id": "tarawih", "t": "التراويح", "en": "Tarawih", "groups": groups})

    groups = []
    for e in lists["reciters"]:
        groups.append({"id": slug(e), "t": e["name"], "s": "", "items": from_m3u(e, e["name"])})
    sections.append({"id": "reciters", "t": "القرّاء", "en": "Reciters", "groups": groups})

    for s in sections:
        s["groups"] = [g for g in s["groups"] if g["items"]]
        for g in s["groups"]:
            if not g["s"]:
                g["s"] = f'{len(g["items"])} تلاوة'

    catalog = {
        "v": 1,
        "updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "radio": {"t": "إذاعة ترتيل", "s": "بث مباشر على مدار الساعة", "en": "Tartil Radio",
                  "urls": ["https://radio.trtel.vip/aac", "https://radio.trtel.vip"]},
        "bases": ["https://files.trtel.vip/a/", "https://archive.org/download/"],
        "art": "https://trtel.vip/logo1200.jpg",
        "sections": sections,
    }
    os.makedirs(os.path.join(ROOT, "app"), exist_ok=True)
    out = os.path.join(ROOT, "app", "catalog.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, separators=(",", ":"))
    n = sum(len(g["items"]) for s in sections for g in s["groups"])
    print(f"catalog.json: {len(sections)} sections, "
          f'{sum(len(s["groups"]) for s in sections)} groups, {n} items, {os.path.getsize(out)//1024} KB')
    for s in sections:
        zero = sum(1 for g in s["groups"] for i in g["items"] if not i["d"])
        print(" ", s["t"], len(s["groups"]), "مجموعة،", sum(len(g["items"]) for g in s["groups"]), "ملف، بلا مدة:", zero)


if __name__ == "__main__":
    main()
