// Nagrania do wideo „Wykaz AED w portalu dane.gov.pl”. Jedna funkcja = jedna scena →
// public/captures/<scena>.mp4 + .json.
//   node capture/scenes.mjs                 → wszystkie sceny
//   node capture/scenes.mjs odbiorca        → jedna
// Portal musi działać lokalnie w Dockerze (portal/backend/README.md). Nagranie tylko czyta: w panelu nic nie jest
// zapisywane (formularz zbioru jest jedynie przewijany, wyszukiwanie zasobów to zapytanie GET).
import {launch, Recorder, settle} from './lib.mjs';
import fs from 'node:fs';
import {ADMIN, API, FRONT, EDGE, HOSTS, IDS, closePrivacy, demoUrl, login} from './portal.mjs';

if (!process.env.CHROME_PATH && fs.existsSync(EDGE)) process.env.CHROME_PATH = EDGE;

const browser = () => launch({args: [HOSTS], ignoreHTTPSErrors: true, locale: 'pl-PL',
  timezoneId: 'Europe/Warsaw'});

/** Prostokąt obejmujący kilka elementów (w chwili wywołania). */
const unionOf = (rec, ...targets) => async () => {
  const rs = (await Promise.all(targets.map(t => rec.rect(t)))).filter(Boolean);
  const x = Math.min(...rs.map(r => r.x)), y = Math.min(...rs.map(r => r.y));
  return {x, y, w: Math.max(...rs.map(r => r.x + r.w)) - x, h: Math.max(...rs.map(r => r.y + r.h)) - y};
};
/** Część elementu widoczna w oknie (dla tabel i sekcji dłuższych niż ekran). */
const visible = (rec, target, maxBottom = 720) => async () => {
  const r = await rec.rect(target);
  const x = Math.max(0, r.x), right = Math.min(1280, r.x + r.w);
  const y = Math.max(0, r.y), bottom = Math.min(maxBottom, r.y + r.h);
  return {x, y, w: Math.max(1, right - x), h: Math.max(1, bottom - y)};
};
/** Prostokąt samego tekstu elementu (a nie całej szerokości bloku). */
const textOf = (page, selector) => () => page.evaluate(sel => {
  const range = document.createRange();
  range.selectNodeContents(document.querySelector(sel));
  const b = range.getBoundingClientRect();
  return {x: b.x, y: b.y, w: b.width, h: b.height};
}, selector);
/** Czeka, aż mapa Leaflet wczyta kafelki (prawdziwe żądania do serwera OSM). */
const tilesLoaded = page => page.waitForFunction(() => {
  const tiles = [...document.querySelectorAll('#resourceMap img.leaflet-tile')];
  return tiles.length > 0 && tiles.every(t => t.complete && t.naturalWidth > 0);
}, null, {timeout: 60000});

const scenes = {
  /** Dostawca: zbiór oznaczony w „Polach niestandardowych”, potem lista zasobów w panelu. */
  async dostawca() {
    const {ctx, page} = await browser();
    try {
      await login(page);
      await page.goto(`${ADMIN}/datasets/dataset/${IDS.source}/change/`);
      await settle(page);
      const rec = new Recorder(page, 'dostawca', {base: ADMIN}); await rec.start();
      const title = page.locator('[name=title]');
      await rec.mark('zbior', unionOf(rec, 'h1', title));
      await rec.moveToRect(await rec.rect(title), {fx: 0.35});
      await rec.wait(2400);

      const pola = await rec.rect('.field-customfields');
      await rec.scrollBy(pola.y - 200, 1100);
      await rec.wait(300);
      const klucz = page.locator('input[name="json_key[customfields]"]').first();
      const wartosc = page.locator('input[name="json_value[customfields]"]').first();
      const pomoc = page.locator('.field-customfields').getByText('Wykaz AED', {exact: false}).first();
      await rec.mark('pola', '.field-customfields');
      await rec.mark('standard', unionOf(rec, klucz, wartosc));
      await rec.moveToRect(await rec.rect(wartosc), {fx: 0.25});
      await rec.wait(3000);
      await rec.mark('pomoc', pomoc);
      await rec.moveToRect(await rec.rect(pomoc), {fx: 0.92, fy: 1.6});
      await rec.wait(3600);

      // Lista zasobów: z menu panelu (na górze strony), wyszukiwanie „AED”.
      await rec.scrollBy(-(await page.evaluate(() => scrollY)), 900);
      await rec.wait(200);
      const menu = page.locator('a[href$="/resources/resource/"]').filter({hasText: 'Zasoby'}).first();  // menu panelu, nie zakładka formularza
      await rec.mark('menu', menu);
      await rec.clickOn(menu);                                             // klik 0
      await rec.mark('nav-start');
      await rec.realtime(async () => { await page.waitForURL(/resources\/resource/); await page.waitForLoadState('networkidle'); });
      await rec.mark('lista-pusta', '#searchbar');
      await rec.clickOn('#searchbar', {fx: 0.3});                         // klik 1
      await page.locator('#searchbar').fill('');
      await rec.type('AED', {cps: 8});
      await rec.wait(250);
      await rec.mark('szukaj');
      await page.keyboard.press('Enter');
      await rec.realtime(async () => { await page.waitForURL(/q=AED/); await page.waitForLoadState('networkidle'); });
      await rec.mark('lista', visible(rec, '#result_list'));
      await rec.moveTo(640, 690);
      await rec.wait(2600);
      const wykaz = page.locator('#result_list tbody tr').filter({hasText: 'Wykaz defibrylatorów AED'}).first();
      await rec.mark('wykaz', wykaz);
      await rec.moveToRect(await rec.rect(wykaz.locator('a').first()), {fx: 0.5});
      await rec.wait(3400);
      await rec.stop();
    } finally { await ctx.close(); }
  },

  /** Odbiorca: zasób zbiorczy we froncie portalu (opis, pobieranie, tabela, mapa) i stały adres API. */
  async odbiorca() {
    const {ctx, page} = await browser();
    try {
      await page.goto(`${FRONT}/dataset/${IDS.dataset}/resource/${IDS.resource}`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1500); await closePrivacy(page); await page.waitForTimeout(800);
      await settle(page);
      const rec = new Recorder(page, 'odbiorca', {base: FRONT}); await rec.start();
      await rec.mark('naglowek', unionOf(rec, 'h1', 'ul.list-unstyled'));
      await rec.moveToRect(await rec.rect('h1'), {fx: 0.75, fy: 1.4});
      await rec.wait(2800);
      const csv = page.locator('a:has-text("CSV (")').first(), jsonld = page.locator('a:has-text("JSONLD")').first();
      await rec.mark('pobierz', unionOf(rec, csv, jsonld));
      await rec.moveToRect(await rec.rect(csv));
      await rec.wait(2800);

      const tabs = await rec.rect('a:has-text("Mapa")');
      await rec.scrollBy(tabs.y - 40, 1200);
      await rec.wait(300);
      await rec.mark('tabela', visible(rec, 'table.datagrid'));
      await rec.moveTo(700, 650);
      await rec.wait(3400);

      await rec.mark('przed-mapa');
      await rec.clickOn('a:has-text("Mapa")');                            // klik 0
      await rec.realtime(async () => {
        await page.waitForSelector('#resourceMap .leaflet-marker-icon', {timeout: 60000});
        await rec.mark('mapa-start');
        await tilesLoaded(page);
        await page.waitForLoadState('networkidle');
      });
      const map = await rec.rect('#resourceMap');
      await rec.scrollBy(map.y - 70, 800);
      await rec.wait(400);
      await rec.mark('mapa', '#resourceMap');
      await rec.mark('punkty', unionOf(rec, page.locator('#resourceMap .leaflet-marker-icon').first(), page.locator('#resourceMap .clusterText').last()));
      await rec.moveTo(640, 360);
      await rec.wait(3800);

      await rec.mark('nav-start');
      await rec.realtime(async () => { await page.goto(`${API}/aed-aggregated`, {waitUntil: 'networkidle'}); });
      await rec.mark('api-surowe', 'pre');
      await rec.moveTo(560, 300);
      await rec.wait(900);
      // „Układ strukturalny” przeglądarki (pole w jej własnym interfejsie, poza DOM strony): Tab i Spacja.
      await page.keyboard.press('Tab');
      await rec.wait(250);
      await rec.mark('formatuj');
      await page.keyboard.press('Space');
      await rec.wait(500);
      await rec.mark('api', textOf(page, 'pre'));
      await rec.wait(3600);
      await rec.stop();
    } finally { await ctx.close(); }
  },

  /** Prototyp offline dla jury: problem, budowa wykazu, przeglądanie z pochodzeniem rekordu, co zmieniliśmy. */
  async prototyp() {
    const {ctx, page} = await browser();
    try {
      await page.goto(demoUrl());
      await settle(page);
      // Ciężka strona (duże SVG) odświeża się wolno: wolniejsze nagrywanie daje więcej klatek.
      const rec = new Recorder(page, 'prototyp', {base: 'file://', slow: 9}); await rec.start();
      await rec.mark('start', unionOf(rec, 'header.top', '#etap-1 table'));
      await rec.moveTo(900, 560);
      await rec.wait(3000);

      await rec.clickOn('nav.etapy button[data-krok="4"]');              // klik 0
      await rec.wait(500);
      await rec.mark('schemat', unionOf(rec, '#etap-4 h2', '#etap-4 > svg'));
      await rec.moveTo(860, 470);
      await rec.wait(3200);

      await rec.clickOn('nav.etapy button[data-krok="5"]');              // klik 1
      await rec.wait(500);
      await rec.mark('filtry', '#filtry');
      await rec.moveToRect(await rec.rect('#f-miasto'), {fx: 0.4});
      await page.focus('#f-miasto');
      await rec.wait(300);
      await rec.mark('wybor');
      // „Legionowo (24)”: realny zasób z dane.gov.pl (CC0). Strzałki zmieniają wybór bez rozwijania listy systemowej.
      await page.keyboard.press('ArrowDown');
      await rec.wait(350);
      await page.keyboard.press('ArrowDown');
      await rec.wait(600);
      if (!/Legionowo/.test(await page.locator('#f-miasto option:checked').textContent())) throw new Error('Filtr nie wybrał Legionowa');
      await rec.mark('wybrano', unionOf(rec, '#f-miasto', '#licznik-wynikow'));
      await rec.wait(1200);
      const mapa = await rec.rect('.mapa-box');
      await rec.scrollBy(mapa.y - 90, 1000);
      await rec.wait(300);
      await rec.mark('mapa', visible(rec, '.mapa-box'));
      await rec.moveTo(640, 500);
      await rec.wait(2600);

      const row = page.locator('#tab-wykaz tbody tr').first();
      const rowTop = await rec.rect(row);
      await rec.scrollBy(rowTop.y - 260, 1000);
      await rec.wait(300);
      await rec.mark('wiersz', row);
      await rec.clickOn(row.locator('button, a').first());                // klik 2
      await rec.wait(700);
      const details = page.locator('#szczegoly dl, #szczegoly table').first();
      await rec.mark('szczegoly', visible(rec, '#szczegoly'));
      await rec.mark('pochodzenie', visible(rec, details, 430));
      await rec.moveTo(900, 300);
      await rec.wait(3600);

      await rec.scrollBy(-(await page.evaluate(() => scrollY)), 1100);   // menu kroków jest na górze strony
      await rec.wait(200);
      await rec.clickOn('nav.etapy button[data-krok="7"]');              // klik 3
      await rec.wait(500);
      await rec.mark('zmiany', unionOf(rec, '#etap-7 h2', '#karty-zmian'));
      await rec.moveTo(900, 640);
      await rec.wait(3600);
      await rec.stop();
    } finally { await ctx.close(); }
  },
};

const wanted = process.argv.slice(2);
for (const name of wanted.length ? wanted : Object.keys(scenes)) {
  if (!scenes[name]) { console.error(`Brak sceny "${name}". Sceny: ${Object.keys(scenes).join(', ')}`); process.exit(1); }
  console.log(`— ${name}`);
  await scenes[name]();
}
