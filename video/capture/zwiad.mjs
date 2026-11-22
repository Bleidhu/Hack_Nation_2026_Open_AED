// Rekonesans przed nagraniem: zrzuty kandydackich ekranów w rozmiarze nagrania (1280x720), bez nagrywania.
//   node capture/zwiad.mjs   → out/zwiad/*.png  (oraz wypisane prostokąty elementów)
import {chromium} from 'playwright-core';
import fs from 'node:fs';
import path from 'node:path';
import {ROOT, chromePath} from './lib.mjs';
import {API, FRONT, HOSTS, IDS, closePrivacy, demoUrl} from './portal.mjs';

const OUT = path.join(ROOT, 'out', 'zwiad');
fs.mkdirSync(OUT, {recursive: true});
const browser = await chromium.launch({executablePath: chromePath(), args: [HOSTS]});
const ctx = await browser.newContext({viewport: {width: 1280, height: 720}, ignoreHTTPSErrors: true, locale: 'pl-PL'});
const page = await ctx.newPage();
const shot = async (name, full = false) => {
  await page.waitForTimeout(1200);
  await page.screenshot({path: path.join(OUT, `${name}.png`), fullPage: full});
  console.log(name, page.url());
};
const box = async (sel) => { const b = await page.locator(sel).first().boundingBox().catch(() => null); console.log('  ', sel, b && Object.values(b).map(Math.round).join(',')); };

// Front: zasób zbiorczy, mapa z kafelkami, klaster.
await page.goto(`${FRONT}/dataset/${IDS.dataset}/resource/${IDS.resource}`, {waitUntil: 'networkidle'});
await page.waitForTimeout(1500); await closePrivacy(page);
await shot('10_front_zasob');
for (const s of ['h1', 'a:has-text("CSV (")', 'a:has-text("JSONLD")', 'text=Tabela', 'text=Mapa', '#resourceMap']) await box(s);
await page.locator('a:has-text("Mapa"), [role=tab]:has-text("Mapa")').first().click();
await page.waitForSelector('#resourceMap .leaflet-marker-icon', {timeout: 60000});
await page.locator('#resourceMap').scrollIntoViewIfNeeded();
await page.waitForLoadState('networkidle');
await shot('11_front_mapa');
for (const s of ['#resourceMap', '#resourceMap .clusterText', '#resourceMap .leaflet-marker-icon']) await box(s);
const c = await page.locator('#resourceMap .clusterText').last().boundingBox(); console.log('cluster', c); await page.mouse.click(c.x + c.width / 2, c.y + c.height / 2);
await page.waitForTimeout(2500);
await shot('12_front_mapa_klaster');
await page.locator('#resourceMap .leaflet-marker-icon:not(.marker-cluster)').first().click().catch(e => console.log(e.message));
await page.waitForTimeout(1500);
await shot('13_front_mapa_popup');

// API z formatowaniem.
await page.goto(`${API}/aed-aggregated`, {waitUntil: 'networkidle'});
await page.locator('input[type=checkbox]').first().check().catch(e => console.log(e.message));
await shot('14_api_pretty');

// Prototyp offline.
await page.goto(demoUrl(), {waitUntil: 'load'});
await page.click('nav.etapy button[data-krok="4"]');
await shot('20_demo_krok4');
await page.click('nav.etapy button[data-krok="5"]');
await shot('21_demo_krok5');
await page.selectOption('#f-miasto', {label: 'Bydgoszcz'}).catch(async () => console.log(await page.locator('#f-miasto option').allTextContents()));
await shot('22_demo_bydgoszcz');
for (const s of ['#filtry', '#f-miasto', '.mapa-box', '.tabela-wrap', '#tab-wykaz tbody tr', '#tab-wykaz tbody tr button, #tab-wykaz tbody tr a', '#licznik-wynikow']) await box(s);
await page.locator('#tab-wykaz tbody tr button, #tab-wykaz tbody tr a').first().click().catch(e => console.log(e.message));
await page.waitForTimeout(800);
await shot('23_demo_szczegoly');
await box('#szczegoly');
console.log('scrollY', await page.evaluate(() => scrollY));
await page.click('nav.etapy button[data-krok="7"]');
await shot('24_demo_krok7', true);
await page.click('nav.etapy button[data-krok="8"]');
await shot('25_demo_krok8', true);
await browser.close();
