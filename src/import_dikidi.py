"""
Забирає з публічних сторінок DIKIDI усе, що салон веде там сам:
  data/services.json — усі послуги: категорія, назва, ціна, тривалість, id для прямого запису
  data/masters.json  — майстри: ім'я, посада, опис, фото, хороші відгуки (4–5★)
  data/company.json  — рейтинг салону на DIKIDI

Салон додає/видаляє послуги, міняє ціни й майстрів у своєму кабінеті DIKIDI,
а цей скрипт (автоматично за розкладом) переносить зміни на сайт.

  python3 src/import_dikidi.py
"""
import html
import json
import os
import re
import sys
import time
import urllib.request

COMPANY = "estoria_beauty_studio_1164912"
BASE = f"https://dikidi.net/ru/profile/{COMPANY}"
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "data"))
SKIP_ROLES = r"(?i)администратор|admin|менеджер|manager|ресепшн|reception"


def fetch(url) -> str:
    headers = {"User-Agent": "Mozilla/5.0 (site sync)", "Accept-Language": "ru"}
    for attempt in range(3):
        try:
            try:
                import requests  # має власні сертифікати (certifi)
                r = requests.get(url, headers=headers, timeout=40)
                r.raise_for_status()
                return r.text
            except ImportError:
                req = urllib.request.Request(url, headers=headers)
                return urllib.request.urlopen(req, timeout=40).read().decode("utf-8")
        except Exception:
            if attempt == 2:
                raise
            time.sleep(3)
    return ""


def grab(pattern, text, default=""):
    m = re.search(pattern, text, re.S)
    return m.group(1) if m else default


def clean(t):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t))).strip()


def parse_services(page):
    cats = dict(re.findall(r'<option value="(\d+)">([^<]+)</option>', page))
    rows = []
    for block in page.split('<div class="service" ')[1:]:
        name = html.unescape(grab(r'data-name="([^"]*)"', block)).strip()
        sid = grab(r"ss_s=(\d+)", block)
        if not (name and sid):
            continue
        rows.append({
            "category": html.unescape(cats.get(grab(r'data-category="(\d+)"', block), "Другое")).strip(),
            "name": name,
            "price": clean(grab(r'class="price">(.*?)</div>', block)),
            "time": clean(grab(r'class="time">(.*?)</div>', block)),
            "id": sid,
        })
    return rows


def ld_objects(page):
    out = []
    for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S):
        try:
            out.append(json.loads(m))
        except ValueError:
            pass
    return out


def parse_master(mid):
    page = fetch(f"{BASE}/master/{mid}")
    person = next((o for o in ld_objects(page) if o.get("@type") == "Person"), {})
    reviews = []
    for block in page.split('<div class="review ')[1:]:
        stars_px = int(grab(r"--stars:\s*(\d+)px", block, "0") or 0)
        rating = round(stars_px / 26) if stars_px else 0
        text = clean(grab(r'<div class="text">(.*?)</div>\s*</div>', block))
        if rating >= 4 and len(text) > 15:
            reviews.append({"author": clean(grab(r'class="username">(.*?)</span>', block)) or "Гость",
                            "date": clean(grab(r'class="date">(.*?)</div>', block)), "rating": rating, "text": text})
    image = person.get("image", "")
    return {
        "id": mid,
        "name": person.get("name", "").strip(),
        "role": (person.get("jobTitle") or "").strip(),
        "description": (person.get("description") or "").strip(),
        "photo": image if image and "assets/images" not in image else "",
        "reviews": reviews,
    }


def main():
    os.makedirs(DATA, exist_ok=True)
    services = parse_services(fetch(f"{BASE}/services"))
    if len(services) < 5:
        sys.exit("DIKIDI віддав підозріло мало послуг — дані не оновлюю, щоб не зламати сайт.")
    json.dump(services, open(os.path.join(DATA, "services.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    profile = fetch(BASE)
    ids = list(dict.fromkeys(re.findall(r'/profile/(?:\w+_)?\d+/master/(\d+)" draggable="false" data-testid="CompanyMediaCard\.Link"', profile)))
    if not ids:  # старий дизайн сторінки DIKIDI
        ids = list(dict.fromkeys(re.findall(rf'/profile/{COMPANY}/master/(\d+)"', profile)))
    masters = []
    for mid in ids:
        m = parse_master(mid)
        if m["name"] and not re.search(SKIP_ROLES, m["role"]):
            masters.append(m)
    if masters:
        json.dump(masters, open(os.path.join(DATA, "masters.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    company = {}
    for o in ld_objects(profile):
        agg = o.get("aggregateRating") if isinstance(o, dict) else None
        if agg:
            company = {"rating": agg.get("ratingValue"), "count": agg.get("ratingCount") or agg.get("reviewCount")}
    if not company:
        r = re.search(r">\s*(\d[.,]\d)\s*<.{0,400}?(\d+)\s*оцен", profile, re.S)
        if r:
            company = {"rating": r.group(1).replace(",", "."), "count": r.group(2)}
    json.dump(company, open(os.path.join(DATA, "company.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(f"DIKIDI: послуг {len(services)}, майстрів {len(masters)} ({', '.join(m['name'] for m in masters)}), рейтинг {company}")


if __name__ == "__main__":
    main()
