// Estoria: меню, карусель отзывов на главной, поиск по прайсу. Без библиотек.

// ---------- Меню ----------
const header = document.getElementById('header');
const burger = document.getElementById('burger');
function setMenu(open) {
  header.classList.toggle('is-open', open);
  burger.setAttribute('aria-expanded', String(open));
  burger.setAttribute('aria-label', open ? 'Закрыть меню' : 'Открыть меню');
  document.body.style.overflow = open ? 'hidden' : '';
}
burger.addEventListener('click', () => setMenu(!header.classList.contains('is-open')));
document.querySelectorAll('#nav a').forEach(a => a.addEventListener('click', () => setMenu(false)));
document.addEventListener('keydown', e => { if (e.key === 'Escape') setMenu(false); });

// ---------- Отзывы на главной ----------
const quotes = [...document.querySelectorAll('.quote')];
if (quotes.length) {
  const now = document.getElementById('qNow');
  let current = 0;
  const show = i => {
    current = (i + quotes.length) % quotes.length;
    quotes.forEach((q, k) => { q.hidden = k !== current; q.classList.toggle('is-active', k === current); });
    now.textContent = current + 1;
  };
  document.getElementById('qPrev').addEventListener('click', () => show(current - 1));
  document.getElementById('qNext').addEventListener('click', () => show(current + 1));
  let startX = null;
  const viewport = document.querySelector('.quotes__viewport');
  viewport.addEventListener('touchstart', e => { startX = e.touches[0].clientX; }, { passive: true });
  viewport.addEventListener('touchend', e => {
    if (startX === null) return;
    const dx = e.changedTouches[0].clientX - startX;
    if (Math.abs(dx) > 40) show(current + (dx < 0 ? 1 : -1));
    startX = null;
  });
}

// ---------- Поиск по прайсу ----------
const search = document.getElementById('priceSearch');
if (search) {
  const rows = [...document.querySelectorAll('.price-row')];
  const empty = document.getElementById('priceEmpty');
  search.addEventListener('input', () => {
    const q = search.value.trim().toLowerCase();
    let shown = 0;
    rows.forEach(r => { const hit = !q || r.dataset.search.includes(q); r.hidden = !hit; if (hit) shown++; });
    document.querySelectorAll('.cat').forEach(c => { c.hidden = !c.querySelector('.price-row:not([hidden])'); });
    document.querySelectorAll('.price-group').forEach(g => {
      const list = g.nextElementSibling;
      g.hidden = !list.querySelector('.price-row:not([hidden])');
    });
    empty.hidden = shown > 0;
  });
}

// ---------- Активная категория в меню прайса и мастеров ----------
const catLinks = [...document.querySelectorAll('.cats a')];
if (catLinks.length && 'IntersectionObserver' in window) {
  const io = new IntersectionObserver(entries => {
    entries.forEach(en => {
      if (!en.isIntersecting) return;
      catLinks.forEach(a => a.classList.toggle('is-active', a.getAttribute('href') === '#' + en.target.id));
    });
  }, { rootMargin: '-30% 0px -60% 0px' });
  catLinks.forEach(a => { const t = document.querySelector(a.getAttribute('href')); if (t) io.observe(t); });
}

// ---------- Фото: без меню «Сохранить изображение» и перетаскивания ----------
document.addEventListener('contextmenu', e => { if (e.target.closest('img, figure, .medallion')) e.preventDefault(); });
document.addEventListener('dragstart', e => { if (e.target.closest('img')) e.preventDefault(); });

// ---------- Літера в медальйоні майстра точно по центру кола ----------
// У рукописного шрифту літера має виноси й нахил, тому центруємо за її фактичними межами, а не за рядком.
function centerGlyphs() {
  const ctx = document.createElement('canvas').getContext('2d');
  document.querySelectorAll('.medallion--lg:not(img)').forEach(m => {
    let g = m.querySelector('.medallion__glyph');
    if (!g) { g = document.createElement('span'); g.className = 'medallion__glyph'; g.textContent = m.textContent.trim(); m.textContent = ''; m.appendChild(g); }
    g.style.transform = '';
    const cs = getComputedStyle(g);
    ctx.font = `${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
    const t = ctx.measureText(g.textContent);
    const box = g.getBoundingClientRect(), circle = m.getBoundingClientRect();
    // центр «чорнила» відносно початку тексту і базової лінії
    const inkCx = (t.actualBoundingBoxRight - t.actualBoundingBoxLeft) / 2;
    const inkCy = (t.actualBoundingBoxDescent - t.actualBoundingBoxAscent) / 2;
    const baseline = box.top + (box.height + t.fontBoundingBoxAscent - t.fontBoundingBoxDescent) / 2;
    const dx = (circle.left + circle.width / 2) - (box.left + inkCx);
    const dy = (circle.top + circle.height / 2) - (baseline + inkCy);
    g.style.transform = `translate(${dx.toFixed(1)}px, ${dy.toFixed(1)}px)`;
  });
}
if (document.querySelector('.medallion--lg')) {
  (document.fonts ? document.fonts.ready : Promise.resolve()).then(centerGlyphs);
  addEventListener('resize', centerGlyphs);
}
