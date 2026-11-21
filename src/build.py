"""
Збирає сайт Estoria з даних:
  data/services.json  — повний прайс з DIKIDI (оновлюється src/import_dikidi.py)
  data/reviews.json   — відгуки з Google (оновлюються ../../get_reviews.py)
Спільні шапка, підвал і стилі — тут і в site/style.css.

  python3 src/build.py   ->  site/index.html, services.html, masters.html, reviews.html, contacts.html
"""
import html
import json
import os
import re
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
SITE = os.path.join(ROOT, "site")
e = lambda s: html.escape(str(s or ""), quote=True)

BOOK = "https://dikidi.net/1164912"
REC_SERVICE = "https://dikidi.net/ru/record/1164912?st_m=2&ss_s={}"
REC_MASTER = "https://dikidi.net/ru/record/1164912?st_m=1&sm_m={}"
MAPS = "https://maps.google.com/?cid=1621410800725523999"
WA = "https://wa.me/35795772751"
VIBER = "viber://chat?number=%2B35795772751"
TEL, PHONE = "+35795772751", "+357 95 772751"
IG = "https://instagram.com/estoria_limassol"
# Адреса сайту: потрібна для картинки-превʼю в месенджерах (там потрібне повне посилання). Змінити, коли підключимо домен.
SITE_URL = "https://estoria-site.pages.dev"
MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]

# ---------------------------------------------------------------- услуги
CATEGORIES = [  # (категория в DIKIDI, якорь, название, пояснение, фото)
    ("Nails / Ногти", "nails", "Маникюр и педикюр", "Покрытие гель-лаком, френч, наращивание и комплексы в четыре руки.", "img/photo8.webp"),
    ("Brows", "brows", "Брови", "Коррекция, окрашивание и ламинирование.", "img/brows-2.webp"),
    ("Lashes / Ресницы", "lashes", "Ресницы", "Ламинирование, окрашивание и наращивание от классики до 4D.", "img/photo2.webp"),
    ("Hair / Волосы", "hair", "Волосы", "Стрижки, сложное окрашивание, блонд и уход Davines и Olaplex.", "img/hair-1.webp"),
    ("Face massage", "face", "Массаж лица", "Лифтинг, лимфодренаж, буккальный и баночный массаж, гуаша.", "img/face-1.webp"),
    ("Массажи, Тело / Massages, Body", "body", "Массаж тела", "Расслабляющий, терапевтический, спортивный, антицеллюлитный массаж и абонементы.", "img/massage-2.webp"),
    ("Спа Процедуры/ Spa Procedures", "spa", "СПА-процедуры", "Обёртывания, скрабы и программы с массажем.", "img/spa-1.webp"),
]
HAIR_GROUPS = [  # порядок проверки; на странице группы идут в порядке HAIR_ORDER
    ("Стрижки", r"стриж|чёлк|челк|филировк|haircut"),
    ("Укладки", r"уклад|прическ|сушк|styling"),
    ("Уход и восстановление", r"уход|davines|olaplex|лечени|пилинг|кератин|полировк|восстановл|консультац"),
    ("Окрашивание и блонд", r"."),
]
HAIR_ORDER = ["Стрижки", "Укладки", "Окрашивание и блонд", "Уход и восстановление"]
NAME_FIX = [  # (регулярка по исходному названию, русское название, английское)
    (r"5 процедур по 1ч\. Антицеллюлитный", "Антицеллюлитный массаж, абонемент: 5 процедур по 1 часу", "Anti-cellulite massage, 5 × 1 h"),
    (r"5 процедур по 1ч\. Расслабляющий", "Расслабляющий массаж, абонемент: 5 процедур по 1 часу", "Relax massage, 5 × 1 h"),
    (r"5 процедур по 30 мин\. Массаж спины", "Массаж спины, абонемент: 5 процедур по 30 минут", "Back massage, 5 × 30 min"),
    (r"10 процедур по 1, 30ч\. Лимфо", "Лимфодренажный массаж, абонемент: 10 процедур по 1,5 часа", "Lymphatic drainage massage, 10 × 1.5 h"),
    (r"10 процедур по 1ч\. Лимфо", "Лимфодренажный массаж, абонемент: 10 процедур по 1 часу", "Lymphatic drainage massage, 10 × 1 h"),
    (r"10 процедур по 1ч\.30мин\. Терапевт", "Терапевтический массаж, абонемент: 10 процедур по 1,5 часа", "Therapeutic massage, 10 × 1.5 h"),
    (r'Davines - "Heart of Glass"', "Уход Davines Heart of Glass: сияние блонда", "Davines Heart of Glass"),
    (r'Davines - "Nourishing"', "Уход Davines Nourishing: глубокое восстановление", "Davines Nourishing"),
    (r'Davines - "Replumping"', "Уход Davines Replumping: увлажнение, питание, восстановление", "Davines Replumping"),
    (r'Davines -"Oi"', "Уход Davines OI: интенсивное питание", "Davines OI"),
    (r"^Стрижка кончиков под машинку", "Стрижка кончиков машинкой", "Ends trim with clippers"),
    (r"^Удаление трещин", "Удаление трещин и мозолей (сложные стопы)", "Cracked heels and calluses"),
    (r"^Лимфодренажный массаж/Limphatic", "Лимфодренажный массаж", "Lymphatic drainage massage"),
    (r"^Общий Глубокий Массаж", "Глубокий массаж всего тела + скраб + обёртывание", "Deep tissue massage + body scrub + body wrap"),
    (r"^Обертывание \+ скраб \(Body", "Обёртывание + скраб", "Body wrap + body scrub"),
    (r"^Лимфодренажный \(Detox\)", "Лимфодренажный detox-массаж + скраб + обёртывание", "Detox lymphatic massage + scrub + wrap"),
    (r"^Мощное жиросжигающие", "Жиросжигающее обёртывание + скраб + массаж", "Fat-burning body wrap + scrub + massage"),
    (r"^Педикюр женский без покрытия", "Педикюр без покрытия", "Women's pedicure"),
    (r"^Facial lymphatic drainage / 5", "Лимфодренажный массаж лица, абонемент на 5 сеансов", "Facial lymphatic drainage, 5 sessions"),
    (r"^Gua sha.*1 session", "Массаж лица гуаша + маска", "Gua sha face massage + mask"),
    (r"^Gua sha.*5 sessions", "Массаж лица гуаша + маска, абонемент на 5 сеансов", "Gua sha face massage + mask, 5 sessions"),
    (r"^Sculptural Face Lift massage / 5", "Скульптурный массаж лица, абонемент на 5 сеансов", "Sculptural face lift massage, 5 sessions"),
    (r"^Sculptural Face Lift massage$", "Скульптурный массаж лица", "Sculptural face lift massage"),
    (r"^Airtouch", "Airtouch: пряди выдуваются феном", "Airtouch"),
    (r"^Balayazh.*?(\d\d)cm", "Балаяж, шатуш или мелирование + окрашивание корней + тонирование, {} см", "Balayage / shatush + roots + toning, {} cm"),
    (r"^Strands in the top zone.*?(\d\d) cm", "Пряди в топ-зоне, контуринг + тонирование, {} см", "Top-zone strands, contouring + toning, {} cm"),
    (r"^Hair toning (\d\d)cm", "Тонирование, {} см", "Hair toning, {} cm"),
    (r"^Monochromatic coloring (\d\d)cm", "Однотонное окрашивание, {} см", "Monochromatic coloring, {} cm"),
    (r"^Out of the black", "Выход из чёрного: светлее на 3–4 тона", "Out of the black"),
    (r"^Super blonde", "Super blonde: осветление на 70% и более", "Super blonde"),
    (r"^Wash and blow-dry", "Мойка, сушка и укладка на брашинг", "Wash and blow-dry"),
    (r"^Bangs haircut", "Стрижка чёлки", "Bangs haircut"),
    (r"^Bob haircut", "Стрижка каре", "Bob haircut"),
    (r"^Haircut cascade", "Стрижка каскад", "Cascade haircut"),
    (r"^Haircut ends with scissors", "Стрижка кончиков ножницами", "Ends trim with scissors"),
    (r"^Hot tool styling", "Укладка горячим инструментом", "Hot tool styling"),
    (r"^Pixie haircut", "Женская короткая стрижка пикси", "Pixie haircut"),
    (r"^Dye hair roots BLONDE", "Окрашивание корней для блонда", "Root colour for blonde"),
    (r"^Dye hair roots", "Окрашивание корней", "Root colour"),
    (r"^Scalp peeling", "Пилинг кожи головы", "Scalp peeling"),
    (r"^Olaplex", "Уход Olaplex", "Olaplex hair treatment"),
    (r"^Лечение волос", "Лечение волос и кожи головы (Orising, Davines)", "Hair and scalp treatment"),
    (r"^Укрепление ногтей", "Маникюр + укрепление ногтей гелем + снятие", "Manicure with builder gel"),
    (r"^Мужская стрижка", "Мужская стрижка: классическая, площадка, спортивная, детская", "Men's haircut"),
    (r"^Массаж для БЕРЕМЕННЫХ", "Массаж для беременных", "Pregnancy massage"),
    (r"Горячими камнями", "Массаж горячими камнями", "Hot stone massage"),
    (r"^Кератин", "Кератин для волос", "Keratin treatment"),
    (r"^Консультация", "Консультация мастера", "Consultation"),
]


def tidy(s):
    s = re.sub(r"\s*\+\s*", " + ", s)
    s = re.sub(r"\(\s+", "(", re.sub(r"\s+\)", ")", s))
    s = re.sub(r'"([^"]+)"', r"«\1»", s)
    s = re.sub(r"\s+", " ", s).strip(" /-")
    s = re.sub(r"\+ ([А-ЯЁ])(?=[а-яё])", lambda m: "+ " + m.group(1).lower(), s)  # «+ Скраб» -> «+ скраб»
    for a, b in (("бертыван", "бёртыван"), ("бъемн", "бъёмн"), ("гель лак", "гель-лак"), ("против отеков", "против отёков")):
        s = s.replace(a, b)
    return s[:1].upper() + s[1:]


def clean_name(raw):
    tag = ""
    if re.match(r"(?i)offer", raw):
        tag = "Акция"
    if re.match(r"(?i)new", raw):
        tag = "Новинка"
    base = re.sub(r"(?i)^(offer|new)!*\s*/?\s*", "", raw).strip()
    if re.search(r"(?i)абонемент|sessions", base):
        tag = "Абонемент"
    for pat, ru, en in NAME_FIX:
        m = re.search(pat, base)
        if m:
            g = m.groups()
            return (ru.format(*g) if g else ru), (en.format(*g) if g else en), tag
    parts = [p.strip() for p in re.split(r"\s*/\s*", base) if p.strip()]
    ru = [p for p in parts if re.search(r"[А-Яа-яЁё]", p)]
    en = [p for p in parts if not re.search(r"[А-Яа-яЁё]", p)]
    ru_s = " / ".join(ru) if ru else base
    if len(ru) > 1 and all(len(p) < 25 for p in ru):  # «Дневная/вечерняя укладка»
        ru_s = "/".join(ru)
    ru_s = re.sub(r"(?i)^абонемент:\s*", "Абонемент: ", ru_s)
    return tidy(ru_s), tidy(" / ".join(en)), tag


def fmt_price(p):
    return p.replace(" EUR", " €")


def fmt_time(t):
    return t.replace(" м", " мин").replace("ч", "ч")


# ---------------------------------------------------------------- мастера
# Список мастеров, должности, описания и фото приходят из DIKIDI (data/masters.json).
# Здесь только направления на сайте и фото работ по каждому направлению.
DIRECTIONS = [  # якорь, название, слова в должности мастера, фото работ (src, подпись)
    ("nails", "Маникюр и педикюр", r"ногт|маник|педик|nail",
     [("img/photo8.webp", "Нюдовый маникюр с мерцанием"), ("img/photo10.webp", "Миндальный маникюр с сухоцветами"),
      ("img/photo4.webp", "Розовый педикюр"), ("img/photo7.webp", "Педикюр с дизайном")]),
    ("brows", "Брови и ресницы", r"бров|ресниц|л[эа]ш|lash|brow",
     [("img/brows-2.webp", "Брови до и после"), ("img/photo2.webp", "Ламинирование ресниц"),
      ("img/brows-1.webp", "Ламинирование и коррекция бровей, до и после"), ("img/lashes-2.webp", "Ресницы до и после")]),
    ("hair", "Волосы", r"парикмах|колорист|стилист|hair|барбер|barber",
     [("img/hair-1.webp", "Сложное окрашивание"), ("img/hair-4.webp", "Блонд в технике AirTouch"),
      ("img/hair-3.webp", "Окрашивание AirTouch"), ("img/hair-6.webp", "Окрашивание и стрижка, до и после")]),
    ("massage", "Массаж и СПА", r"массаж|massage|спа|spa|косметолог|cosmet",
     [("img/massage-1.webp", "Массаж тела"), ("img/face-1.webp", "Массаж лица и тела"), ("img/spa-1.webp", "Комплексный массаж"), ("img/massage-2.webp", "Терапевтический массаж")]),
    ("other", "Другие мастера", r".", []),
]
LAT = dict(zip("абвгдезиклмнопрстуфхцы", "abvgdeziklmnoprstufhcy"))
CYR = {v: k for k, v in LAT.items()}


def load_masters():
    path = os.path.join(ROOT, "data", "masters.json")
    masters = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else []
    for m in masters:
        role = m.get("role") or "Мастер"
        role = ROLE_RU.get(role.strip().lower(), role)  # посада англійською з DIKIDI → російською
        if re.search(r"[А-Яа-я]", role):
            role = role[:1].upper() + role[1:].lower()
        m["role_display"] = role
        m["direction"] = next(slug for slug, _, pat, _ in DIRECTIONS if re.search(pat, role.lower()))
        original = m["name"].strip()
        m["name"] = display_name(original)
        stems = set()
        for nm in (original, m["name"]):
            first = re.split(r"[\s.]", nm)[0]
            stem = first[:-1] if len(first) > 4 and first[-1].lower() in "аяьaei" else first
            low = stem.lower().replace("ё", "е")
            stems.add(low)
            stems.add("".join((LAT if re.search(r"[а-я]", low) else CYR).get(c, c) for c in low))
        m["pattern"] = r"(?i)\b(" + "|".join(re.escape(s) for s in sorted(stems) if s) + ")"
    return masters


ROLE_RU = {"massage therapist": "Массажист", "masseur": "Массажист", "masseuse": "Массажист",
           "nail master": "Мастер ногтевого сервиса", "manicurist": "Мастер ногтевого сервиса",
           "hairdresser": "Парикмахер", "colorist": "Колорист", "brow master": "Мастер-бровист",
           "lash maker": "Лэшмейкер", "cosmetologist": "Косметолог", "administrator": "Администратор"}


# Як ім'я майстра показувати на сайті: в DIKIDI буває латиницею або з ініціалом прізвища
NAME_DISPLAY = {"Olga": "Ольга", "Alena": "Алёна", "Алена": "Алёна", "Daria": "Дарья", "Elena": "Елена",
                "Maria": "Мария", "Liliya": "Лилия", "Lilia": "Лилия", "Andriana": "Андриана"}


def img_size(src):
    """Справжні розміри фото, щоб сторінка не стрибала під час завантаження."""
    try:
        from PIL import Image
        with Image.open(os.path.join(ROOT, "site", src)) as im:
            return im.size
    except Exception:
        return (600, 750)


def display_name(name):
    name = re.sub(r"\s+[A-ZА-ЯЁ]\.?$", "", name.strip())  # «Olga M.» → «Olga»
    return " ".join(NAME_DISPLAY.get(w, w) for w in name.split())


def master_description(text):
    """Описание из DIKIDI: абзацы + пункты «-массаж» склеиваем в одну строку."""
    text = no_emoji(text)
    paras, items = [], []
    for line in [l.strip() for l in text.splitlines() if l.strip()]:
        if line.startswith("-"):
            items.append(line.lstrip("- ").strip())
        elif not re.match(r"(?i)работает по направлениям", line):
            paras.append(line)
    if items:
        paras.append("Направления: " + ", ".join(items) + ".")
    return "".join(f"<p>{e(p)}</p>" for p in paras)


def plural(n, one, few, many):
    n = int(n)
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


# ---------------------------------------------------------------- отзывы
def load_reviews():
    d = json.load(open(os.path.join(ROOT, "data", "reviews.json"), encoding="utf-8"))
    good = [r for r in d["reviews"] if (r.get("rating") or 0) >= 4 and len(r["text"]) > 30]
    return d, good


def ru_date(iso):
    y, m, dd = (int(x) for x in iso.split("-"))
    return f"{dd} {MONTHS[m - 1]} {y}"


def no_emoji(t):
    t = re.sub(r"[\U0001F000-\U0001FAFF☀-➿️‍]+", "", t)
    t = re.sub(r"[ \t]+([,.!?)])", r"\1", t)          # «хорошие ,» -> «хорошие,»
    t = re.sub(r"\([ \t]+", "(", t)
    t = re.sub(r"([,.!?])(?=[А-Яа-яA-Za-z])", r"\1 ", t)  # «Елене!Она» -> «Елене! Она»
    return re.sub(r"[ \t]{2,}", " ", t).strip()


def first_sentences(t, n=230):
    t = re.sub(r"\s+", " ", no_emoji(t))
    if len(t) <= n:
        return t
    cut = t[:n]
    k = max(cut.rfind(". "), cut.rfind("! "))
    return cut[:k + 1] if k > n * 0.45 else cut[:cut.rfind(" ")] + "…"


def paragraphs(t):
    return "".join(f"<p>{e(p.strip())}</p>" for p in re.split(r"\n\s*\n|\n", no_emoji(t)) if p.strip())


# ---------------------------------------------------------------- общие части
SYMBOLS = """  <svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false">
    <defs><g id="leaf"><path d="M0 0C6-5.5 16-6 24 0C16 6 6 5.5 0 0Z"/><path d="M2 0H21"/></g></defs>
    <symbol id="olive" viewBox="0 0 220 90">
      <g fill="none" stroke="currentColor" stroke-width=".9" stroke-linecap="round">
        <path d="M4 82C48 70 104 52 214 10"/>
        <use href="#leaf" transform="translate(30 74) rotate(-62)"/><use href="#leaf" transform="translate(38 73) rotate(28)"/>
        <use href="#leaf" transform="translate(62 64) rotate(-68)"/><use href="#leaf" transform="translate(72 63) rotate(22)"/>
        <use href="#leaf" transform="translate(98 53) rotate(-72)"/><use href="#leaf" transform="translate(108 51) rotate(18)"/>
        <use href="#leaf" transform="translate(134 39) rotate(-76)"/><use href="#leaf" transform="translate(144 37) rotate(12)"/>
        <use href="#leaf" transform="translate(168 26) rotate(-74)"/><use href="#leaf" transform="translate(178 24) rotate(8)"/>
        <use href="#leaf" transform="translate(203 14) rotate(-24)"/>
      </g>
      <g fill="currentColor"><ellipse cx="86" cy="66" rx="3.6" ry="4.6" transform="rotate(-20 86 66)"/><ellipse cx="156" cy="40" rx="3.6" ry="4.6" transform="rotate(-20 156 40)"/></g>
    </symbol>
    <symbol id="branch" viewBox="0 0 240 50">
      <g fill="none" stroke="currentColor" stroke-width=".9" stroke-linecap="round">
        <path d="M4 25H222"/><use href="#leaf" transform="translate(28 25) rotate(-48)"/><use href="#leaf" transform="translate(41 25) rotate(48)"/><use href="#leaf" transform="translate(58 25) rotate(-48)"/><use href="#leaf" transform="translate(71 25) rotate(48)"/><use href="#leaf" transform="translate(88 25) rotate(-48)"/><use href="#leaf" transform="translate(101 25) rotate(48)"/><use href="#leaf" transform="translate(118 25) rotate(-48)"/><use href="#leaf" transform="translate(131 25) rotate(48)"/><use href="#leaf" transform="translate(148 25) rotate(-48)"/><use href="#leaf" transform="translate(161 25) rotate(48)"/><use href="#leaf" transform="translate(178 25) rotate(-48)"/><use href="#leaf" transform="translate(191 25) rotate(48)"/><use href="#leaf" transform="translate(208 25) rotate(-48)"/><use href="#leaf" transform="translate(221 25) rotate(48)"/><use href="#leaf" transform="translate(214 25)"/>
      </g>
      <g fill="currentColor"><ellipse cx="84" cy="31" rx="3.4" ry="4.4"/><ellipse cx="156" cy="19" rx="3.4" ry="4.4"/></g>
    </symbol>
    <symbol id="corner" viewBox="0 0 48 48"><path d="M1 48V1h47M8 48V8h40" fill="none" stroke="currentColor" stroke-width="1"/><path d="M8 1l3.5 3.5L8 8 4.5 4.5z" fill="currentColor"/></symbol>
  </svg>"""

CORNERS = ('<svg class="corner corner--tl"><use href="#corner"/></svg><svg class="corner corner--tr"><use href="#corner"/></svg>'
           '<svg class="corner corner--bl"><use href="#corner"/></svg><svg class="corner corner--br"><use href="#corner"/></svg>')
FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='32' "
           "fill='%234E0001'/%3E%3Ctext x='32' y='44' text-anchor='middle' font-family='Georgia,serif' font-style='italic' "
           "font-size='36' fill='%23FEEBA6'%3EE%3C/text%3E%3C/svg%3E")
NAV = [("services.html", "Услуги и цены"), ("masters.html", "Мастера и работы"), ("reviews.html", "Отзывы"), ("contacts.html", "Контакты")]
WA_ICON = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 18.2c-1.5 0-3-.4-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.3-.4.2-.4.7-1.4.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.7 11.8 11.8 0 0 0 4.5 4c1.7.7 2.3.8 3.2.6.5-.1 1.5-.6 1.7-1.2.2-.6.2-1.1.2-1.2-.1-.1-.3-.2-.5-.3z"/></svg>')
TEL_ICON = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25 11.4 11.4 0 0 0 3.6.57 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.25.2 2.45.57 3.57a1 1 0 0 1-.25 1z"/></svg>')

LD = {
    "@context": "https://schema.org", "@type": "BeautySalon", "name": "Estoria Beauty Salon", "telephone": TEL,
    "address": {"@type": "PostalAddress", "streetAddress": "Spiridonos Lamprou 13a", "addressLocality": "Limassol",
                "postalCode": "3106", "addressCountry": "CY"},
    "geo": {"@type": "GeoCoordinates", "latitude": 34.6879603, "longitude": 33.0573689},
    "openingHoursSpecification": [{"@type": "OpeningHoursSpecification",
                                   "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                                   "opens": "09:00", "closes": "20:00"}],
    "hasMap": MAPS, "sameAs": [IG, BOOK],
}


def layout(page, title, desc, body):
    current = ' aria-current="page"'
    nav = "\n".join(f'      <a href="{h}"{current if h == page else ""}>{t}</a>' for h, t in NAV)
    foot_nav = " ".join(f'<a href="{h}">{t}</a>' for h, t in NAV)
    ld = json.dumps(LD, ensure_ascii=False) if page == "index.html" else ""
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{e(title)}</title>
  <meta name="description" content="{e(desc)}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Estoria Beauty Salon">
  <meta property="og:title" content="{e(title)}">
  <meta property="og:description" content="{e(desc)}">
  <meta property="og:url" content="{SITE_URL}/{"" if page == "index.html" else page.removesuffix(".html")}">
  <meta property="og:image" content="{SITE_URL}/img/og-logo.jpg">
  <meta property="og:image:width" content="1080">
  <meta property="og:image:height" content="1080">
  <meta property="og:image:alt" content="Логотип Estoria beauty salon">
  <meta name="twitter:card" content="summary">
  <link rel="apple-touch-icon" href="img/apple-touch-icon.png">
  <meta name="theme-color" content="#4E0001">
  <link rel="icon" href="{FAVICON}">
  <!-- ДЕМО: сайт скрыт от поисковиков. Убрать, когда сайт станет официальным (и удалить robots.txt) -->
  <meta name="robots" content="noindex, nofollow">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Cormorant+SC:wght@400;500;600&family=Great+Vibes&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="style.css">
  {f'<script type="application/ld+json">{ld}</script>' if ld else ''}
</head>
<body class="page-{page.split('.')[0]}">
{SYMBOLS}
  <a class="skip" href="#main">Перейти к содержанию</a>

  <header class="header" id="header">
    <a href="index.html" class="brand" aria-label="Estoria Beauty Salon, на главную">
      <span class="brand__script">Estoria</span>
      <span class="brand__sub">beauty salon</span>
    </a>
    <nav class="nav" id="nav" aria-label="Разделы сайта">
{nav}
      <a class="btn btn--butter nav__book" href="{BOOK}" target="_blank" rel="noopener">Записаться онлайн</a>
    </nav>
    <a class="btn btn--butter header__book" href="{BOOK}" target="_blank" rel="noopener">Записаться онлайн</a>
    <button class="burger" id="burger" aria-label="Открыть меню" aria-expanded="false" aria-controls="nav"><span></span><span></span></button>
  </header>

  <main id="main">
{body}
  </main>

  <footer class="footer velvet scallop">
    <div class="seal" aria-hidden="true"><span>E</span></div>
    <span class="footer__script">Estoria</span>
    <span class="footer__sub">beauty salon</span>
    <svg class="olive olive--footer" aria-hidden="true"><use href="#olive"/></svg>
    <nav class="footer__nav" aria-label="Разделы сайта">{foot_nav}</nav>
    <p>Spiridonos Lamprou 13a, Лимассол, рядом с Trilogy. Ежедневно с 9:00 до 20:00. <a href="tel:{TEL}">{PHONE}</a></p>
    <p class="footer__small">Рейтинг и отзывы — из Google Карт, цены — из онлайн-записи DIKIDI. © <span id="year">{date.today().year}</span> Estoria Beauty Salon</p>
  </footer>

  <nav class="dock" aria-label="Быстрая запись">
    <a class="btn btn--butter" href="{BOOK}" target="_blank" rel="noopener">Записаться онлайн</a>
    <a class="dock__icon" href="{WA}" target="_blank" rel="noopener" aria-label="Написать в WhatsApp">{WA_ICON}</a>
    <a class="dock__icon" href="tel:{TEL}" aria-label="Позвонить">{TEL_ICON}</a>
  </nav>

  <script src="script.js"></script>
</body>
</html>
"""


def page_hero(title, lead, extra=""):
    return f"""    <section class="page-hero velvet">
      <svg class="olive olive--page-l" aria-hidden="true"><use href="#olive"/></svg>
      <svg class="olive olive--page-r" aria-hidden="true"><use href="#olive"/></svg>
      <h1 class="page-hero__title">{title}</h1>
      {f'<p class="page-hero__lead">{lead}</p>' if lead else ''}{extra}
      <div class="edge" aria-hidden="true"></div>
    </section>"""


# ---------------------------------------------------------------- страницы
def page_services(services):
    by_cat = {}
    for s in services:
        by_cat.setdefault(s["category"], []).append(s)
    cats = [c for c in CATEGORIES if c[0] in by_cat]  # категорию удалили в DIKIDI — не показываем
    for i, cat in enumerate(k for k in by_cat if k not in {c[0] for c in CATEGORIES}):
        ru = [p.strip() for p in re.split(r"/", cat) if re.search(r"[А-Яа-яЁё]", p)]  # новая категория из DIKIDI
        cats.append((cat, f"cat{i + 1}", tidy(ru[0] if ru else cat), "", None))
    tabs = "".join(f'<a href="#{slug}">{e(t)}</a>' for _, slug, t, _, _ in cats)
    sections = []
    for cat, slug, title, intro, photo in cats:
        rows = []
        for s in by_cat.get(cat, []):
            ru, en, tag = clean_name(s["name"])
            rows.append((ru, en, tag, s))
        if slug == "hair":
            groups = []
            used = set()
            for gname, pat in HAIR_GROUPS:
                g = [r for r in rows if r[3]["id"] not in used and re.search(pat, (r[0] + " " + r[1]).lower())]
                used |= {r[3]["id"] for r in g}
                if g:
                    groups.append((gname, g))
            groups.sort(key=lambda x: HAIR_ORDER.index(x[0]))
        else:
            plain = [r for r in rows if r[2] != "Абонемент"]
            subs = [r for r in rows if r[2] == "Абонемент"]
            groups = [("", plain)] + ([("Абонементы", subs)] if subs else [])

        def row_html(r):
            ru, en, tag, s = r
            tag_html = f'<span class="tag">{e(tag)}</span>' if tag and tag != "Абонемент" else ""
            search = e((ru + " " + en).lower())
            return f"""          <li class="price-row" data-search="{search}">
            <div class="price-row__name"><span class="price-row__ru">{e(ru)}</span>{tag_html}{f'<span class="price-row__en">{e(en)}</span>' if en and en.lower() != ru.lower() else ''}</div>
            <span class="price-row__time">{e(fmt_time(s["time"]))}</span>
            <span class="price-row__price">{e(fmt_price(s["price"]))}</span>
            <a class="price-row__book" href="{REC_SERVICE.format(s["id"])}" target="_blank" rel="noopener" aria-label="Записаться: {e(ru)}">Записаться</a>
          </li>"""

        body = []
        for gname, g in groups:
            if gname:
                body.append(f'        <h3 class="price-group">{e(gname)}</h3>')
            body.append('        <ul class="price-list">\n' + "\n".join(row_html(r) for r in g) + "\n        </ul>")
        photo_html = (f'<figure class="cat__photo"><img src="{photo}" alt="" width="600" height="750" loading="lazy"></figure>'
                      if photo else '<div class="cat__photo cat__photo--olive" aria-hidden="true"><svg class="olive"><use href="#olive"/></svg></div>')
        sections.append(f"""      <section class="cat" id="{slug}" aria-labelledby="{slug}-title">
        <header class="cat__head">
          {photo_html}
          <div>
            <h2 class="h2" id="{slug}-title">{e(title)}</h2>
            {f'<p class="cat__intro">{e(intro)}</p>' if intro else ''}
          </div>
        </header>
{chr(10).join(body)}
      </section>""")

    body = page_hero("Услуги и цены", f"{len(services)} процедур: от маникюра до СПА. Нажмите «Записаться» у нужной услуги — откроется онлайн-запись с уже выбранной процедурой.") + f"""
    <div class="pricelist">
      <aside class="pricelist__nav">
        <label class="search"><span class="visually-hidden">Поиск услуги</span>
          <input type="search" id="priceSearch" placeholder="Найти услугу, например «каре»" autocomplete="off">
        </label>
        <nav class="cats" aria-label="Категории услуг">{tabs}</nav>
      </aside>
      <div class="pricelist__body">
{chr(10).join(sections)}
        <p class="price-empty" id="priceEmpty" hidden>Такой услуги не нашлось. Напишите нам в <a href="{WA}" target="_blank" rel="noopener">WhatsApp</a> — подскажем.</p>
        <p class="price-note">Цены указаны по данным онлайн-записи. Для услуг с пометкой «от» итоговая стоимость зависит от длины и густоты волос — мастер назовёт её на консультации.</p>
      </div>
    </div>"""
    return layout("services.html", "Услуги и цены — Estoria Beauty Salon, Лимассол",
                  "Полный прайс Estoria Beauty Salon в Лимассоле: маникюр, педикюр, брови, ресницы, волосы, массаж и СПА с онлайн-записью.", body)


def page_masters(good, masters):
    sections, used_dirs = [], 0
    # Фото з DIKIDI показуємо лише тоді, коли воно є в усіх майстрів, інакше всім однакова буква-медальйон
    use_photos = all(m.get("photo") for m in masters)
    for slug, title, _, works in DIRECTIONS:
        group = [m for m in masters if m["direction"] == slug]
        if not group and not works:
            continue
        used_dirs += 1
        cards = []
        for m in group:
            quotes = [(first_sentences(r["text"], 200), f'{r["author"]}, DIKIDI') for r in m.get("reviews", [])]
            quotes += [(first_sentences(r["text"], 200), f'{r["author"]}, Google') for r in good if re.search(m["pattern"], r["text"])]
            q_html = "".join(f'<blockquote class="mq"><p>«{e(q)}»</p><footer>{e(a)}</footer></blockquote>' for q, a in quotes[:3])
            face = (f'<img class="medallion medallion--lg medallion--photo" src="{e(m["photo"])}" alt="{e(m["name"])}" loading="lazy">'
                    if use_photos else f'<div class="medallion medallion--lg" aria-hidden="true">{e(m["name"][:1])}</div>')
            cards.append(f"""          <article class="master" id="m{m["id"]}">
            {face}
            <div class="master__body">
              <h3 class="h3">{e(m["name"])}</h3>
              <p class="master__role">{e(m["role_display"])}</p>
              {f'<div class="master__bio">{master_description(m["description"])}</div>' if m.get("description") else ''}
              {q_html}
              <a class="btn btn--line-wine" href="{REC_MASTER.format(m["id"])}" target="_blank" rel="noopener">Записаться к мастеру</a>
            </div>
          </article>""")
        if works:
            figs = "".join(f'<figure class="work{" work--arch" if i % 2 == 0 else ""}"><img src="{src}" alt="{e(cap)}" width="{img_size(src)[0]}" height="{img_size(src)[1]}" loading="lazy"><figcaption>{e(cap)}</figcaption></figure>'
                           for i, (src, cap) in enumerate(works))
            gallery = f'        <div class="works-grid works-grid--{len(works)}">{figs}</div>'
        else:
            gallery = ""
        more = f'<a class="link" href="{IG}" target="_blank" rel="noopener">Больше работ в Instagram @estoria_limassol</a>'
        sections.append(f"""      <section class="dir" id="{slug}" aria-labelledby="{slug}-title">
        <header class="dir__head">
          <h2 class="h2" id="{slug}-title">{e(title)}</h2>
          <p>{more}</p>
        </header>
{gallery}
        <div class="masters-list">
{chr(10).join(cards)}
        </div>
      </section>""")
    tabs = "".join(f'<a href="#{s}">{e(t)}</a>' for s, t, _, _ in DIRECTIONS
                   if any(m["direction"] == s for m in masters) or (s != "other" and DIRECTIONS[[d[0] for d in DIRECTIONS].index(s)][3]))
    body = page_hero("Мастера и работы", "", f'\n      <nav class="cats cats--light" aria-label="Направления">{tabs}</nav>') + f"""
    <div class="masters-page">
{chr(10).join(sections)}
    </div>"""
    return layout("masters.html", "Мастера и работы — Estoria Beauty Salon, Лимассол",
                  "Мастера Estoria Beauty Salon: маникюр и педикюр, брови и ресницы, волосы, массаж. Работы и онлайн-запись к мастеру.", body)


def page_reviews(meta, good, company):
    cards = []
    for r in good:
        cards.append(f"""        <article class="review">
          <div class="review__stars" aria-label="Оценка {r["rating"]} из 5">{"★" * int(r["rating"])}</div>
          <div class="review__text">{paragraphs(r["text"])}</div>
          <footer><b>{e(r["author"])}</b><span>{ru_date(r["time"])}, Google</span></footer>
        </article>""")
    place = meta.get("place_id", "")
    write = f"https://search.google.com/local/writereview?placeid={place}" if place else MAPS
    rating = f'{meta.get("rating", 4.8):.1f}'.replace(".", ",")
    body = page_hero("Отзывы гостей", f"{rating} из 5 по {meta.get('count', 72)} отзывам в Google Картах. Здесь — отзывы с текстом, которые Google показывает для салона.",
                     f"""
      <div class="score-row">
        <div class="score"><b>{rating}</b><span class="stars">★★★★★</span><small>Google, {meta.get("count", 72)} {plural(meta.get("count", 72), "отзыв", "отзыва", "отзывов")}</small></div>
        {dikidi_score(company)}
      </div>""") + f"""
    <section class="reviews-page" aria-label="Отзывы">
      <div class="review-grid">
{chr(10).join(cards)}
      </div>
      <div class="reviews-page__actions">
        <a class="btn btn--wine" href="{MAPS}" target="_blank" rel="noopener">Все отзывы в Google Картах</a>
        <a class="btn btn--line-wine" href="{write}" target="_blank" rel="noopener">Оставить отзыв</a>
      </div>
    </section>"""
    return layout("reviews.html", "Отзывы — Estoria Beauty Salon, Лимассол",
                  "Отзывы гостей Estoria Beauty Salon в Лимассоле из Google Карт: 4,8 из 5.", body)


def dikidi_score(company):
    if not company.get("rating"):
        return ""
    r = f'{float(company["rating"]):.1f}'.replace(".", ",")
    c = int(company.get("count") or 0)
    return f'<div class="score"><b>{r}</b><span class="stars">★★★★★</span><small>DIKIDI, {c} {plural(c, "оценка", "оценки", "оценок")}</small></div>'


def page_contacts():
    body = page_hero("Контакты", "Spiridonos Lamprou 13a, Лимассол. Ориентир — комплекс Trilogy.") + f"""
    <section class="visit visit--page" aria-label="Контакты и карта">
      <div class="visit__text">
        <dl class="visit__list">
          <div><dt>Адрес</dt><dd>Spiridonos Lamprou 13a<br>Лимассол 3106<br>рядом с Trilogy</dd></div>
          <div><dt>Часы работы</dt><dd>Ежедневно<br>с 9:00 до 20:00</dd></div>
          <div><dt>Телефон</dt><dd><a href="tel:{TEL}">{PHONE}</a></dd></div>
          <div><dt>Мессенджеры</dt><dd><a href="{WA}" target="_blank" rel="noopener">WhatsApp</a>, <a href="{VIBER}">Viber</a></dd></div>
          <div><dt>Instagram</dt><dd><a href="{IG}" target="_blank" rel="noopener">@estoria_limassol</a></dd></div>
          <div><dt>Онлайн-запись</dt><dd><a href="{BOOK}" target="_blank" rel="noopener">DIKIDI</a></dd></div>
        </dl>
        <div class="visit__actions">
          <a class="btn btn--wine" href="{BOOK}" target="_blank" rel="noopener">Записаться онлайн</a>
          <a class="btn btn--line-wine" href="{MAPS}" target="_blank" rel="noopener">Проложить маршрут</a>
        </div>
      </div>
      <figure class="window window--map">
        <iframe title="Estoria на карте: Spiridonos Lamprou 13a, Лимассол" loading="lazy" src="https://maps.google.com/maps?q=34.6879603,33.0573689&amp;z=16&amp;output=embed"></iframe>
      </figure>
    </section>"""
    return layout("contacts.html", "Контакты — Estoria Beauty Salon, Лимассол",
                  "Адрес, телефон, часы работы и карта Estoria Beauty Salon: Spiridonos Lamprou 13a, Лимассол, рядом с Trilogy.", body)


def page_index(good, meta, masters, services):
    home = open(os.path.join(HERE, "home.html"), encoding="utf-8").read()
    picks = [r for r in good if 120 < len(r["text"])][:4]
    quotes = "\n".join(f"""          <blockquote class="quote{' is-active' if i == 0 else ''}"{'' if i == 0 else ' hidden'}>
            <p>{e(first_sentences(r["text"], 260))}</p>
            <footer>{e(r["author"])}, {ru_date(r["time"])}</footer>
          </blockquote>""" for i, r in enumerate(picks))
    medallions = "\n".join(f'        <li><a class="medallion" href="masters.html#m{m["id"]}">{e(m["name"])}</a></li>' for m in masters)
    by_id = {x["id"]: x for x in services}

    def service_items(token_ids):
        items = []
        for sid in token_ids.split(","):
            x = by_id.get(sid.strip())
            if x:  # услугу удалили в DIKIDI — просто не показываем
                items.append(f'<li>{e(clean_name(x["name"])[0])} <span>{e(fmt_price(x["price"]))}</span></li>')
        return "\n            ".join(items)
    home = re.sub(r"\{\{SERVICES:([\d,\s]+)\}\}", lambda mm: service_items(mm.group(1)), home)
    home = home.replace("{{SERVICE_COUNT}}", str(len(services)))
    home = (home.replace("{{QUOTES}}", quotes).replace("{{QCOUNT}}", str(len(picks)))
            .replace("{{MEDALLIONS}}", medallions).replace("{{BOOK}}", BOOK).replace("{{WA}}", WA)
            .replace("{{MAPS}}", MAPS).replace("{{RCOUNT}}", str(meta.get("count", 72))))
    return layout("index.html", "Estoria Beauty Salon — салон красоты в Лимассоле",
                  "Estoria Beauty Salon в Лимассоле: маникюр, педикюр, брови, ресницы, стрижки, окрашивание, массаж и СПА. "
                  "Ежедневно с 9:00 до 20:00, Spiridonos Lamprou 13a, рядом с Trilogy.", home)


def main():
    services = json.load(open(os.path.join(ROOT, "data", "services.json"), encoding="utf-8"))
    meta, good = load_reviews()
    masters = load_masters()
    cpath = os.path.join(ROOT, "data", "company.json")
    company = json.load(open(cpath, encoding="utf-8")) if os.path.exists(cpath) else {}
    pages = {
        "index.html": page_index(good, meta, masters, services),
        "services.html": page_services(services),
        "masters.html": page_masters(good, masters),
        "reviews.html": page_reviews(meta, good, company),
        "contacts.html": page_contacts(),
    }
    for name, content in pages.items():
        open(os.path.join(SITE, name), "w", encoding="utf-8").write(content)
    print(f"Готово: {', '.join(pages)} · послуг {len(services)} · відгуків {len(good)}")


if __name__ == "__main__":
    main()
