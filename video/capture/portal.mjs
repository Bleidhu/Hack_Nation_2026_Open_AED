// Portal dane.gov.pl uruchomiony lokalnie w Dockerze (portal/backend/README.md): adresy, identyfikatory, logowanie.
// Nazwy *.mcod.local trafiają na nginx portalu (127.0.0.1) regułą przeglądarki, bez wpisów w pliku hosts
// (tak samo jak demo/scenariusz/zrzuty.py). Nagranie tylko czyta: niczego nie zapisuje w panelu ani w bazie.
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {ROOT} from './lib.mjs';

export const HOSTS = '--host-resolver-rules=MAP *.mcod.local 127.0.0.1, MAP mcod.local 127.0.0.1';
export const ADMIN = 'https://admin.mcod.local';
export const API = 'https://api.mcod.local/1.4';
export const FRONT = 'https://mcod.local/pl';

/**
 * Przeglądarka do nagrań: Microsoft Edge bez okna. Chrome bez okna dostawał od serwera kafelków OpenStreetMap
 * odpowiedź 429 (pusta, szara mapa), Edge dostaje kafelki, tak jak przy zrzutach w demo/scenariusz/zrzuty.py.
 * Okno z interfejsem odpada: w skali 2x nie mieści się na ekranie. CHROME_PATH nadpisuje wybór.
 */
export const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';

/** Zbiór dostawcy (Legionowo, standard = AED), zbiór i zasób zbiorczy Wykazu AED: demo/zrzuty/README.md. */
export const IDS = {
  source: Number(process.env.AED_SOURCE_DATASET || 4211),
  dataset: Number(process.env.AED_MAIN_DATASET || 4216),
  resource: Number(process.env.AED_MAIN_RESOURCE || 40247),
};

/** Konto administratora środowiska lokalnego (portal/backend/README.md); logowanie odbywa się przed nagraniem. */
export async function login(page) {
  await page.goto(`${ADMIN}/login/`, {waitUntil: 'networkidle'});
  await page.fill('input[name=username]', process.env.AED_ADMIN_EMAIL || 'admin@mcod.local');
  await page.fill('input[name=password]', process.env.AED_ADMIN_PASSWORD || 'testadmin123!');
  await page.click('[type=submit]');
  await page.waitForLoadState('networkidle');
}

/** Prototyp offline z repozytorium (demo/index.html), otwierany z dysku jak u jury. */
export const demoUrl = (hash = '') => pathToFileURL(path.resolve(ROOT, '..', 'demo', 'index.html')).href + hash;

/** Okno „Polityka prywatności i RODO” frontu (treść z CMS, lokalnie pusta) zamykamy przed nagraniem. */
export async function closePrivacy(page) {
  const btn = page.getByRole('button', {name: 'Zamknij'});
  if (await btn.count()) await btn.first().click().catch(() => {});
}
