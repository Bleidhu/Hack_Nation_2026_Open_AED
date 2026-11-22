// Prezentacja „Dane (prze)życie: Wykaz AED w portalu dane.gov.pl” (PPTX) i prezentacja/README.md (mapa slajdów).
//   npm install pptxgenjs@3.12.0 jszip   (w dowolnym katalogu; potem NODE_PATH=<ten katalog>/node_modules)
//   node prezentacja/build_prezentacja.js
// PDF: eksport z PowerPointa (prezentacja/eksport_pdf.ps1). Krój Atkinson Hyperlegible (branding/fonty/) musi być zainstalowany.
// Liczby na slajdach pochodzą z demo/wynik/ (testy.txt, weryfikacja.txt, raport_agregacji.txt, import_opisu.json)
// i demo/zrzuty/README.md. Slajdy ze zrzutami 16–19, 21–22 i integrator_01–04 dodaje się tylko wtedy, gdy pliki istnieją w demo/zrzuty/.
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..");
const P = (...p) => path.join(ROOT, ...p);

// ---- Liczby do podmiany w jednym miejscu ----
// Testy portalu: ostatnia linia demo/wynik/testy.txt („N passed, M skipped”).
const TESTY_PASSED = 270;
const TESTY_SKIPPED = 2;
const TESTY_DATA = "22.11.2026";
// Liczba „passed” widoczna na zrzucie demo/zrzuty/09_testy.png. Gdy jest równa TESTY_PASSED, podpis mówi o aktualnym przebiegu.
const ZRZUT09_PASSED = 270;
// Kontrole maszynowe: pierwsza linia demo/wynik/weryfikacja.txt.
const KONTROLE = "20/20";
// Testy integratora (integrator/README.md).
const TESTY_INTEGRATORA = 97;
// Pliki portalu względem oryginału: git diff --name-status a1adc22 -- portal/ (A, M) plus nieśledzone z git status --short portal/.
const PLIKI_NOWE = 34;
const PLIKI_ZMIENIONE = 11;

// ostrzeżenie, gdy stała z liczbą testów rozjedzie się z logiem
try {
  const m = fs.readFileSync(P("demo", "wynik", "testy.txt"), "utf8").match(/(\d+) passed(?:, (\d+) skipped)?/g);
  const ost = m && m[m.length - 1].match(/(\d+) passed(?:, (\d+) skipped)?/);
  if (ost && (Number(ost[1]) !== TESTY_PASSED || Number(ost[2] || 0) !== TESTY_SKIPPED)) {
    console.warn(`UWAGA: demo/wynik/testy.txt podaje ${ost[0]}, a TESTY_PASSED/TESTY_SKIPPED = ${TESTY_PASSED}/${TESTY_SKIPPED}`);
  }
} catch (e) { /* brak logu: zostają stałe */ }

// wymiary obrazu PNG (nagłówek IHDR)
const wymiary = (plik) => { const b = fs.readFileSync(plik); return [b.readUInt32BE(16), b.readUInt32BE(20)]; };
const hPNG = (plik, w) => { const [pw, ph] = wymiary(plik); return (w * ph) / pw; };
const OUT = P("prezentacja", "dane_przezycie_prezentacja.pptx");

// kolory znaku z księgi znaku; żółty tylko na ciemnym tle, czerwień tylko tam, gdzie coś jest uwagą
const K = { granat: "0E2A47", zielen: "007A45", czerwien: "C8102E", zolc: "FFC629", szary: "3B5068", linia: "B8C4CC",
  jasny: "E6ECE9", bialy: "FFFFFF", granatJ: "8FA6BC" };
const FONT = "Atkinson Hyperlegible";
const MONO = "Consolas";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13,333 × 7,5 cala
pres.title = "Dane (prze)życie: Wykaz AED w portalu dane.gov.pl";
pres.subject = "HackNation 2026, zadanie „Misja AED – Dane na ratunek”";
pres.author = "Zespół projektu Dane (prze)życie";
pres.lang = "pl-PL";
pres.theme = { headFontFace: FONT, bodyFontFace: FONT };

const W = 13.333, M = 0.7;
const numer = (kolor) => ({ x: W - M - 0.6, y: 6.95, w: 0.6, h: 0.3, fontSize: 11, color: kolor, align: "right", fontFace: FONT });
const tytulMaster = (kolor, x, w) => ({ placeholder: { options: { name: "title", type: "title", x, y: 0.45, w, h: 1.0, fontSize: 30,
  bold: true, color: kolor, valign: "top", align: "left", margin: 0, fontFace: FONT }, text: "" } });

pres.defineSlideMaster({ title: "TRESC", background: { color: K.bialy }, objects: [tytulMaster(K.granat, M, W - 2 * M)],
  slideNumber: numer(K.szary) });
pres.defineSlideMaster({ title: "CIEMNY", background: { color: K.granat }, objects: [tytulMaster(K.bialy, M, W - 2 * M)],
  slideNumber: numer(K.granatJ) });
// slajd z tytułem w lewej kolumnie
pres.defineSlideMaster({ title: "KOLUMNA", background: { color: K.bialy }, objects: [tytulMaster(K.granat, M, 4.1)],
  slideNumber: numer(K.szary) });
pres.defineSlideMaster({ title: "TYTULOWY", background: { color: K.granat }, objects: [] });

const tx = (slide, text, o) => slide.addText(text, Object.assign({ isTextBox: true, fontFace: FONT, color: K.granat,
  fontSize: 16, margin: 0, valign: "top", paraSpaceAfter: 6 }, o));
const linia = (slide, x, y, w, kolor = K.linia, grub = 0.75) =>
  slide.addShape(pres.shapes.LINE, { x, y, w, h: 0, line: { color: kolor, width: grub } });
const strzalka = (slide, x, y, w, h, kolor = K.szary, grub = 1.5) =>
  slide.addShape(pres.shapes.LINE, { x, y, w, h, line: { color: kolor, width: grub, endArrowType: "triangle" } });
const akapity = (teksty, o = {}) => teksty.map((t, i) => ({ text: t, options: Object.assign({ breakLine: i < teksty.length - 1 }, o) }));
// akapit z pogrubionym początkiem: [[pogrubione, reszta], ...]
const zLead = (pary, kolorLead) => {
  const r = [];
  pary.forEach(([a, b], i) => {
    r.push({ text: a, options: { bold: true, color: kolorLead } });
    r.push({ text: b, options: { breakLine: i < pary.length - 1 } });
  });
  return r;
};

// zrzut ekranu z cienką ramką; crop = ile pikseli wysokości oryginału pokazać (od góry)
function zrzut(slide, plik, px, x, y, w, crop, alt) {
  const [pw, ph] = px;
  const fullH = (w * ph) / pw;
  const h = crop ? (w * crop) / pw : fullH;
  const o = { path: P("demo", "zrzuty", plik), x, y, w, h: crop ? fullH : h, altText: alt };
  if (crop) o.sizing = { type: "crop", x: 0, y: 0, w, h };
  slide.addImage(o);
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { type: "none" }, line: { color: K.linia, width: 0.75 } });
  return h;
}
// to samo z wymiarami odczytanymi z pliku; obraz wyższy niż maxH jest przycinany od dołu
function zrzutA(slide, plik, x, y, w, maxH, alt) {
  const [pw, ph] = wymiary(P("demo", "zrzuty", plik));
  const fullH = (w * ph) / pw;
  return zrzut(slide, plik, [pw, ph], x, y, w, fullH > maxH ? (maxH * pw) / w : 0, alt);
}
const podpis = (slide, text, x, y, w, kolor = K.szary) => tx(slide, text, { x, y, w, h: 0.5, fontSize: 12, color: kolor });
const jestZrzut = (plik) => fs.existsSync(P("demo", "zrzuty", plik));

// podpis zrzutu z kolumny „Co widać” w demo/zrzuty/README.md (pierwsze zdania, do ok. 200 znaków); bez wiersza: zapasowy
function opisZrzutu(plik, zapas) {
  try {
    const wiersz = fs.readFileSync(P("demo", "zrzuty", "README.md"), "utf8").split(/\r?\n/)
      .find((l) => l.startsWith("| `" + plik + "`"));
    if (!wiersz) return zapas;
    let t = wiersz.split("|")[2].replace(/`/g, "").trim();
    if (t.length > 200) {
      const zd = t.split(/(?<=\.)\s+/);
      t = "";
      for (const z of zd) { if ((t + " " + z).trim().length > 200) break; t = (t + " " + z).trim(); }
      if (!t) t = zapas;
    }
    return t;
  } catch (e) { return zapas; }
}

// wiersz „z praktyki → pole wzorca”: po lewej zdanie z doświadczenia, po prawej pola (mono) i krótkie wyjaśnienie
function wiersz(slide, y, h, lewa, pola, opis, planowane) {
  linia(slide, M, y, W - 2 * M);
  tx(slide, lewa, { x: M, y: y + 0.12, w: 5.3, h: h - 0.2, fontSize: 15 });
  tx(slide, [
    { text: pola, options: { fontFace: MONO, bold: true, fontSize: 13, color: planowane ? K.czerwien : K.zielen, breakLine: true } },
    { text: opis, options: { fontSize: 13, color: K.szary } },
  ], { x: M + 5.8, y: y + 0.12, w: W - 2 * M - 5.8, h: h - 0.2, paraSpaceAfter: 4 });
}

// numeracja slajdów do mapy w README
let licznik = 0;
const nr = {};
const slajd = (master = "TRESC", klucz) => {
  licznik += 1;
  if (klucz) nr[klucz] = licznik;
  return pres.addSlide({ masterName: master });
};

// zrzut przycięty do prostokąta wycinek = [px szer., px wys., px od lewej, px od góry], wpasowany w maxW × maxH; zwraca [w, h]
function zrzutWycinek(slide, plik, x, y, maxW, maxH, wycinek, alt) {
  const [pw, ph] = wymiary(P("demo", "zrzuty", plik));
  const [cw0, ch0, x0, y0] = wycinek || [pw, ph, 0, 0];
  const ox = x0 || 0, oy = y0 || 0;
  const cw = Math.min(pw - ox, cw0), ch = Math.min(ph - oy, ch0);
  const sk = Math.min(maxW / cw, maxH / ch);
  const w = cw * sk, h = ch * sk;
  const o = { path: P("demo", "zrzuty", plik), x, y, w: pw * sk, h: ph * sk, altText: alt };
  if (cw < pw || ch < ph) o.sizing = { type: "crop", x: ox * sk, y: oy * sk, w, h };
  slide.addImage(o);
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { type: "none" }, line: { color: K.linia, width: 0.75 } });
  return [w, h];
}

// slajd z jednym zrzutem, dodawany tylko wtedy, gdy plik istnieje (zrzuty 16–19 powstają osobno, w Dockerze)
// p: { plik, tytul, podpis (pełny podpis zgodny z demo/zrzuty/README.md; bez niego pierwsze zdania z README), alt, wycinek, tekst }
function slajdZrzutu(klucz, p) {
  if (!jestZrzut(p.plik)) return false;
  const s = slajd("TRESC", klucz);
  s.addText(p.tytul, { placeholder: "title" });
  const top = 1.45;
  const maxW = p.tekst ? 7.4 : W - 2 * M;
  const [w, h] = zrzutWycinek(s, p.plik, M, top, maxW, 4.55, p.wycinek, p.alt);
  tx(s, `Zrzut ${p.plik.slice(0, 2)}: ${p.podpis || opisZrzutu(p.plik, "")}`,
    { x: M, y: top + h + 0.1, w: p.tekst ? w : Math.max(w, 9), h: 6.85 - (top + h + 0.1), fontSize: 12, color: K.szary });
  if (p.tekst) {
    const xt = M + w + 0.45;
    tx(s, zLead(p.tekst, K.zielen), { x: xt, y: top, w: W - M - xt, h: 5.0, fontSize: 15, paraSpaceAfter: 12 });
  }
  s.addNotes("Zrzut z portalu uruchomionego lokalnie w Dockerze, z naszymi zmianami. Opis zrzutów: demo/zrzuty/README.md.");
  return true;
}

// 1. Tytuł
{
  const s = slajd("TYTULOWY", "tytul");
  const l = P("branding", "logo", "dane-przezycie_logo_poziome_negatyw.png");
  s.addImage({ path: l, x: M - 0.15, y: 0.8, w: 8.4, h: hPNG(l, 8.4),
    altText: "Logo akcji Dane (prze)życie: migotanie komór i rytm serca spotykają się w środku folderu z danymi" });
  s.addText("Wykaz AED w portalu dane.gov.pl", { x: M, y: 3.5, w: 11.5, h: 0.9, fontSize: 44, bold: true, color: K.bialy,
    fontFace: FONT, margin: 0, valign: "top", placeholder: undefined });
  tx(s, "Ogólnopolski, otwarty wykaz defibrylatorów z danych wielu dysponentów. Powstał z przerobionego mechanizmu DGA w kodzie portalu, bez migracji bazy.",
    { x: M, y: 4.5, w: 10.8, h: 1.1, fontSize: 20, color: K.bialy });
  tx(s, "HackNation 2026, zadanie „Misja AED – Dane na ratunek”, Ministerstwo Cyfryzacji",
    { x: M, y: 6.7, w: 11, h: 0.35, fontSize: 14, color: K.granatJ });
  s.addNotes("Tytuł projektu i nazwa akcji. Rozwiązanie to modyfikacja kodu portalu dane.gov.pl, a nie osobna aplikacja.");
}

// 2. Problem: scenariusz z zadania i trzy pytania
{
  const s = slajd("CIEMNY", "problem");
  s.addText("Gdy liczy się każda minuta, nie wiadomo, gdzie jest defibrylator", { placeholder: "title" });
  tx(s, "Warszawa, 3 marca. Fotograf sejmowy ma zawał, świadkowie chcą pomóc i szukają defibrylatora. Podobno jest w kilku miejscach, ale są zamknięte na klucz.",
    { x: M, y: 1.85, w: 6.9, h: 1.9, fontSize: 22, color: K.bialy });
  tx(s, "Defibrylatora AED może użyć każdy. Trzeba tylko wiedzieć, gdzie szukać.", { x: M, y: 3.95, w: 6.9, h: 0.9, fontSize: 17, color: K.granatJ });
  const pyt = [["Gdzie", "jest najbliższe urządzenie?"], ["Czy", "jest dostępne?"], ["Czy", "działa?"]];
  let y = 1.85;
  pyt.forEach(([a, b]) => {
    linia(s, 8.2, y, 4.45, K.szary);
    tx(s, a, { x: 8.2, y: y + 0.12, w: 1.4, h: 0.8, fontSize: 34, bold: true, color: K.zolc });
    tx(s, b, { x: 9.65, y: y + 0.3, w: 3.0, h: 0.7, fontSize: 18, color: K.bialy });
    y += 1.15;
  });
  linia(s, 8.2, y, 4.45, K.szary);
  tx(s, zLead([["Nie ma dziś kompletnej mapy defibrylatorów. ", "Dane są rozproszone, niepełne i często niezweryfikowane."]], K.zolc),
    { x: M, y: 5.5, w: 11.9, h: 1.0, fontSize: 20, color: K.bialy });
  s.addNotes("Scenariusz pochodzi z opisu zadania. Trzy pytania, na które odpowiedź ma dawać zbiór danych: gdzie, czy dostępny, czy działa.");
}

// 3. Rozproszone źródła: miasta w portalu i bazy poza portalem
{
  const s = slajd("TRESC", "zrodla");
  s.addText("Dane są rozproszone: sześć miast i bazy poza portalem", { placeholder: "title" });
  const zr = [
    ["Krosno", "plik CSV, bez kolumny z miejscowością"],
    ["Przemyśl", "link do systemu miasta, 5 dystrybucji"],
    ["Marki", "CSV i XLSX wadliwe: cały wiersz w jednym polu"],
    ["Legionowo", "zasób AED w zbiorze mieszanym „Zdrowie”"],
    ["Warszawa", "w portalu tylko strona WWW, dane w API z tokenem"],
    ["Gdańsk", "AED w 278 pojazdach ZTM, w pliku JSON floty"],
  ];
  let y = 1.5;
  zr.forEach(([m, d]) => {
    linia(s, M, y, 7.3);
    tx(s, m, { x: M, y: y + 0.1, w: 1.8, h: 0.4, fontSize: 17, bold: true });
    tx(s, d, { x: M + 1.9, y: y + 0.12, w: 5.4, h: 0.4, fontSize: 15 });
    y += 0.58;
  });
  linia(s, M, y, 7.3);
  tx(s, "Poza portalem", { x: 8.5, y: 1.5, w: 4.15, h: 0.4, fontSize: 17, bold: true, color: K.zielen });
  tx(s, zLead([
    ["OpenStreetMap i OpenAEDMap. ", "Z tej mapy importują dane operatorzy numerów alarmowych 112, 997 i 998."],
    ["Zamknięte bazy aplikacji. ", "Pierwszy Ratownik, Staying Alive i inne."],
    ["Mogłyby kiedyś trafić do portalu. ", "Dziś OSM ma licencję ODbL, więc używamy go tylko do porównań."],
  ], K.granat), { x: 8.5, y: 1.95, w: 4.15, h: 3.4, fontSize: 15, paraSpaceAfter: 12 });
  tx(s, "Nie ma jednej listy AED, a każdy zbiór ma inne kolumny i formaty.", { x: M, y: 5.55, w: 11.9, h: 0.5, fontSize: 20, bold: true });
  podpis(s, "Źródła: przegląd API dane.gov.pl z 21.11.2026; MSWiA, odpowiedź z 15.04.2026 na interpelację nr 16205.", M, 6.55, 11.9);
  s.addNotes("Sześć miast publikuje AED na sześć sposobów. Poza portalem są bazy, które dziś nie mogą wejść do zbioru: OpenAEDMap (ODbL) i bazy zamknięte. MSWiA w odpowiedzi na interpelację 16205 potwierdziło, że operatorzy 112, 997 i 998 pobierają lokalizacje AED z openaedmap.org.");
}

// 4. Z praktyki ratownika: dojście do urządzenia
{
  const s = slajd("TRESC", "praktyka1");
  s.addText("Pod presją czasu: gdzie dokładnie i czy da się wejść", { placeholder: "title" });
  tx(s, "Z praktyki ratownika", { x: M, y: 1.15, w: 5.3, h: 0.3, fontSize: 12, bold: true, color: K.szary });
  tx(s, "Pole we wzorcu", { x: M + 5.8, y: 1.15, w: 5, h: 0.3, fontSize: 12, bold: true, color: K.szary });
  wiersz(s, 1.5, 1.35, "Nie ma czasu szukać oznakowań ani zgadywać, że AED wisi dwie kondygnacje wyżej.",
    "opis_lokalizacji · kondygnacja · wewnatrz_budynku", "Opis miejsca jest wymagany: gdzie wejść, które piętro, przy czym.");
  wiersz(s, 2.85, 1.35, "Dostępność zmienia się w ciągu doby: budynek bywa czynny tylko w określonych godzinach.",
    "dostepny_24_7 · godziny_dostepnosci", "Całodobowo albo godziny otwarcia. Pole 24/7 jest wymagane.");
  wiersz(s, 4.2, 1.35, "Urządzenie bywa zamknięte na klucz albo niedostępne dla przechodnia.",
    "typ_dostepu · zabezpieczenie · instrukcja_dostepu", "Publiczny, ograniczony lub prywatny; szafka otwarta, na kod, na klucz. W instrukcji bez kodów i bez miejsca klucza.");
  linia(s, M, 5.55, W - 2 * M);
  tx(s, "Dlatego opis lokalizacji, typ dostępu i dostępność całodobowa są polami wymaganymi.",
    { x: M, y: 5.75, w: 11.9, h: 0.5, fontSize: 18, bold: true });
  s.addNotes("Każdy wiersz to potrzeba zgłoszona z praktyki i pole, które na nią odpowiada. Pola wymagane to opis_lokalizacji, typ_dostepu i dostepny_24_7 (obok nazwy, miejscowości, współrzędnych, identyfikatora i daty aktualizacji).");
}

// 5. Z praktyki ratownika: stan urządzenia i opiekun
{
  const s = slajd("TRESC", "praktyka2");
  s.addText("Czy działa i kto za nim odpowiada", { placeholder: "title" });
  tx(s, "Z praktyki ratownika", { x: M, y: 1.15, w: 5.3, h: 0.3, fontSize: 12, bold: true, color: K.szary });
  tx(s, "Pole we wzorcu", { x: M + 5.8, y: 1.15, w: 5, h: 0.3, fontSize: 12, bold: true, color: K.szary });
  wiersz(s, 1.5, 1.3, "AED z wyczerpaną baterią lub elektrodami idzie do serwisu, a po użyciu też. W zbiorze musi być wtedy oznaczony jako niedostępny.",
    "status_urzadzenia · data_waznosci_elektrod · data_waznosci_baterii", "Status: sprawny, niesprawny, w serwisie, wycofany, nieznany. Wykaz sam wylicza, czy wymaga przeglądu.");
  wiersz(s, 2.8, 1.15, "Dyspozytor poprowadzi przez procedurę dokładniej, gdy zna model. Dzieci wymagają elektrod lub klucza pediatrycznego.",
    "producent · model · elektrody_pediatryczne", "Pole pediatryczne mówi, czy są elektrody lub tryb dla dzieci.");
  wiersz(s, 3.95, 1.4, "Ktoś musi odpowiadać za urządzenie. W jednym budynku od tygodnia piszczał rozładowany AED, a obsługi trzeba było szukać.",
    "dysponent_nazwa · telefon_kontaktowy · email_kontaktowy", "Kontakt do opiekuna, tylko funkcyjny (serwis budynku, sekretariat), nigdy imienny. Podobnie jak w brytyjskim The Circuit, gdzie urządzenie rejestruje jego opiekun.");
  wiersz(s, 5.35, 1.0, "Po użyciu sprzęt powinien wrócić do właściciela.",
    "numer_seryjny", "Numer z tabliczki znamionowej, opcjonalny (wzorzec 2.1.0). Wskazuje egzemplarz i jest kluczem deduplikacji wykazu.");
  podpis(s, "Puste pole statusu oznacza „nieznany”, nigdy „sprawny”. The Circuit: British Heart Foundation.", M, 6.55, 11.9);
  s.addNotes("Numer seryjny jest kolumną wzorca od wersji 2.1.0 (po kolumnie model, opcjonalny). To numer urządzenia, nie dane osoby. Kontakt jest funkcyjny z powodu RODO. W The Circuit (Wielka Brytania) urządzenie rejestruje jego opiekun (Guardian), który podaje kontakt do osoby odpowiedzialnej i potwierdza dane co kwartał.");
}

// 6. Wzorcowy zakres: liczby jako tabela w liniach, zasady obok
{
  const s = slajd("TRESC", "wzorzec");
  s.addText("Z tych potrzeb powstał wzorcowy zakres danych", { placeholder: "title" });
  const lic = [
    ["42", "kolumny wzorca dostawcy, każda z typem i wymagalnością (W/Z/O)"],
    ["52", "kolumny wykazu: wzorzec plus pochodzenie i przetworzenie rekordu"],
    ["5", "arkuszy XLSX: zakres, szablon, słowniki, wykaz, zasady"],
    ["5", "rodzajów schematów: Table Schema, CSVW, JSON-LD, DCAT-AP i XSD"],
  ];
  let y = 1.55;
  lic.forEach(([n, d]) => {
    linia(s, M, y, 5.6);
    tx(s, n, { x: M, y: y + 0.1, w: 1.1, h: 0.7, fontSize: 36, bold: true, color: K.zielen });
    tx(s, d, { x: M + 1.2, y: y + 0.2, w: 4.4, h: 0.7, fontSize: 15 });
    y += 1.05;
  });
  linia(s, M, y, 5.6);
  tx(s, zLead([
    ["Licencje. ", "Do wykazu trafiają tylko zasoby na CC0 1.0 i CC BY 4.0, z atrybucją. Dane z OpenStreetMap (ODbL) są pomijane."],
    ["Dane osobowe. ", "Gdy zbiór deklaruje dane osobowe, telefon i e-mail są usuwane, a rekord dostaje kod kontakt_usuniety."],
    ["Status nieznany. ", "Puste pole statusu oznacza „nieznany”, nigdy „sprawny”. Data importu nie jest datą weryfikacji."],
  ], K.granat), { x: 7.2, y: 1.55, w: 5.45, h: 4.6, fontSize: 17, paraSpaceAfter: 16 });
  podpis(s, "Plik: format_danych/wzorcowy_zakres_danych.xlsx. Reguły: arkusz 5_Zasady i schemat Table Schema. XSD: rekordy (aed_punkty.xsd) i opis zbioru (aed_opis_zbioru.xsd).", M, 6.55, 12);
}

// 7. Rozwiązanie: cztery kroki w jednej linii, bez kart
{
  const s = slajd("TRESC", "mechanizm");
  s.addText("Jak to działa: mechanizm DGA przerobiony na defibrylatory", { placeholder: "title" });
  const kroki = [
    ["Oznaczenie zbioru", "Dostawca wpisuje w „Polach niestandardowych”: standard = AED."],
    ["Publikacja zasobu", "Plik według wzorca albo opis XML z linkiem do CSV i sumą md5. Zwykła walidacja portalu."],
    ["Nocne scalanie", "Zadanie Celery o 4:15 sprawdza kolumny, licencje i dane osobowe, a potem usuwa duplikaty."],
    ["Wykaz AED", "Jeden zasób zbiorczy z tabelą, mapą i API."],
  ];
  const kw = 2.75, g = 0.37;
  kroki.forEach(([t, d], i) => {
    const x = M + i * (kw + g);
    const ost = i === 3;
    linia(s, x, 1.65, kw, ost ? K.zielen : K.granat, ost ? 4 : 1.5);
    tx(s, String(i + 1), { x, y: 1.8, w: 0.8, h: 0.8, fontSize: 40, bold: true, color: ost ? K.zielen : K.szary });
    tx(s, t, { x, y: 2.75, w: kw, h: 0.45, fontSize: 20, bold: true, color: ost ? K.zielen : K.granat });
    tx(s, d, { x, y: 3.25, w: kw, h: 1.25, fontSize: 15 });
  });
  tx(s, zLead([
    ["Bez migracji. ", "Żadnych nowych pól ani tabel; oznaczenie siedzi w istniejącej metadanej zbioru."],
    [`${PLIKI_NOWE} nowe pliki i ${PLIKI_ZMIENIONE} istniejących z dopiskami. `, "Kod AED obok DGA, testy, schematy XSD i próbki danych. Nic nie usunięto."],
    ["Jeden wyłącznik, AED_AGGREGATION_ENABLED. ", "Po wyłączeniu portal działa jak oryginał."],
  ], K.granat), { x: M, y: 4.65, w: 11.5, h: 1.6, fontSize: 17, paraSpaceAfter: 8 });
  podpis(s, "Szczegóły: ZMIANY_W_PORTALU.md. Diff względem oryginału: git diff a1adc22 -- portal/backend", M, 6.6, 11);
  s.addNotes("Kierunek: zmieniać kod portalu, słowo kluczowe zasób, przerobić DGA, bez migracji, scalać wykazy w jedną listę. Liczba plików: git diff --name-status a1adc22 -- portal/ oraz pliki jeszcze nieśledzone (aed_dedup.py, aed_import.py, aed_opis.py, aed_opis_zbioru.xsd i ich testy).");
}

// 8. Dostawca, krok 1: tytuł w lewej kolumnie, zrzut po prawej na całą wysokość
{
  const s = slajd("KOLUMNA", "dostawca1");
  s.addText("Dostawca oznacza zbiór jako AED", { placeholder: "title" });
  zrzut(s, "01_formularz_zbioru_standard_aed.png", [1440, 900], 5.3, 1.0, 7.35, 0,
    "Formularz zbioru w panelu portalu: w Polach niestandardowych wpis standard = AED i podpowiedź pod polem");
  tx(s, akapity([
    "W formularzu zbioru, w „Polach niestandardowych”, dostawca dodaje klucz standard z wartością AED. Wersja po spacji też działa, np. „AED 1.1”.",
    "Podpowiedź pod polem mówi, co wpisać.",
    "To istniejąca metadana zbioru (Dataset.customfields). Nie ma nowego pola, tagu ani checkboxa.",
  ]), { x: M, y: 1.9, w: 4.1, h: 3.9, fontSize: 16, paraSpaceAfter: 12 });
  podpis(s, "Zrzut 01: panel portalu uruchomionego lokalnie, zbiór z Legionowa.", 5.3, 5.75, 7.35);
}

// 9. Dostawca, krok 2: zrzut po lewej, tekst po prawej
{
  const s = slajd("TRESC", "dostawca2");
  s.addText("Dostawca publikuje zasób według wzorca", { placeholder: "title" });
  const h = zrzut(s, "02_zasoby_dostawcow.png", [1440, 1234], M, 1.55, 7.3, 880,
    "Lista zasobów w panelu: pięć zasobów dostawców i zasób zbiorczy Wykaz defibrylatorów AED");
  podpis(s, "Zrzut 02: lista zasobów w panelu, pięć zasobów dostawców i zasób zbiorczy.", M, 1.55 + h + 0.1, 7.3);
  tx(s, [
    { text: "Dostawca pobiera szablon XLSX lub CSV wzorcowego zakresu, wypełnia kolumny (minimum to m.in. nazwa lokalizacji, miejscowość i współrzędne) i dodaje plik albo link jako zasób.", options: { breakLine: true } },
    { text: "Portal waliduje go zwykłym potokiem zasobów.", options: { breakLine: true } },
    { text: "Zbiór bez wpisu standard = AED nie trafia do wykazu, nawet gdy ma te same kolumny.", options: { bold: true, breakLine: true } },
    { text: "Dostawca z własnym serwerem może zamiast tego wystawić opis zbioru w XML (następny slajd).", options: { color: K.szary } },
  ], { x: 8.45, y: 1.55, w: 4.2, h: 4.9, fontSize: 16, paraSpaceAfter: 14 });
}

// 10. Dane z zewnątrz: opis XML → XSD → CSV i md5 → kontrola → zbiór i zasób (diagram z prostych kształtów)
{
  const s = slajd("TRESC", "opis");
  s.addText("Integracja przez API: opis XML, CSV i suma md5", { placeholder: "title" });
  const kroki = [
    ["Opis XML", "Portal pobiera po HTTPS opis.xml z serwera lub API dostawcy i wymaga kodu 200."],
    ["Schemat XSD", "Sprawdza opis schematem aed_opis_zbioru.xsd: metadane, link do CSV, md5."],
    ["CSV i md5", "Pobiera CSV spod linku i porównuje jego sumę md5 z sumą z opisu."],
    ["Kontrola CSV", "Kolumny minimum wzorca, wiersze przyjęte i pominięte, duplikaty w pliku."],
    ["Zbiór i zasób", "Zbiór z customfields: standard = AED, opis_xml, md5. Zasób CSV w tym zbiorze."],
  ];
  const g = 0.42, bw = (W - 2 * M - 4 * g) / 5, by = 1.6, bh = 2.05;
  kroki.forEach(([t, d], i) => {
    const x = M + i * (bw + g);
    const ost = i === 4;
    s.addShape(pres.shapes.RECTANGLE, { x, y: by, w: bw, h: bh, fill: { color: K.bialy },
      line: { color: ost ? K.zielen : K.granat, width: ost ? 3 : 1.25 } });
    tx(s, [
      { text: String(i + 1), options: { bold: true, fontSize: 14, color: ost ? K.zielen : K.szary, breakLine: true } },
      { text: t, options: { bold: true, fontSize: 16, color: ost ? K.zielen : K.granat, breakLine: true } },
      { text: d, options: { fontSize: 12, color: K.granat } },
    ], { x: x + 0.12, y: by + 0.1, w: bw - 0.24, h: bh - 0.2, paraSpaceAfter: 3 });
    if (i < 4) strzalka(s, x + bw + 0.05, by + bh / 2, g - 0.1, 0, K.szary, 1.75);
  });
  // gałąź odrzucenia pod krokami 1–4
  const yb = by + bh, yr = yb + 0.38, wr = 4 * bw + 3 * g;
  for (let i = 0; i < 4; i++) strzalka(s, M + i * (bw + g) + bw / 2, yb, 0, yr - yb, K.czerwien, 1.25);
  s.addShape(pres.shapes.RECTANGLE, { x: M, y: yr, w: wr, h: 0.5, fill: { type: "none" }, line: { color: K.czerwien, width: 1.25 } });
  tx(s, zLead([["Błąd w krokach 1–4 ", "(brak kodu 200, niezgodny XSD, inne md5, brak kolumn): import odrzucony, nic nie zapisano."]], K.czerwien),
    { x: M + 0.15, y: yr + 0.13, w: wr - 0.3, h: 0.3, fontSize: 12, color: K.czerwien });
  // dalej: nocne zadanie
  const x5 = M + 4 * (bw + g);
  strzalka(s, x5 + bw / 2, yb, 0, yr - yb, K.zielen, 1.75);
  tx(s, "O 4:15 nocne zadanie scala zasób w Wykaz AED.", { x: x5, y: yr + 0.05, w: bw, h: 0.6, fontSize: 12, bold: true, color: K.zielen });
  // opis pod diagramem
  const yt = yr + 0.8;
  tx(s, zLead([
    ["Zgłoszenie adresu. ", "Komenda import_aed_xml <adres opisu> --organizacja <ID> zaczytuje zbiór; --dry-run tylko sprawdza."],
    ["Co noc o 4:05 ", "zadanie Celery refresh_aed_opis_task pobiera opisy jeszcze raz. Ta sama suma md5 niczego nie zmienia, nowa zastępuje zasób."],
    ["Bez migracji. ", "Adres opisu i suma md5 są zapisane w Dataset.customfields."],
  ], K.granat), { x: M, y: yt, w: 5.75, h: 6.5 - yt, fontSize: 13, paraSpaceAfter: 6 });
  tx(s, zLead([
    ["Wariant dodatkowy: ", "rekordy wprost w XML (aed_punkty.xsd) jako zasób z linkiem; nocne zadanie waliduje je schematem."],
    ["Bez czekania do nocy: ", "demo/wymus_harvest.py od razu odświeża opis i buduje wykaz."],
    ["Integrator (dodatek) ", "buduje opis z gotowego pliku CSV i liczy md5 (podkomenda opis)."],
  ], K.granat), { x: M + 6.15, y: yt, w: 5.75, h: 6.5 - yt, fontSize: 13, paraSpaceAfter: 6 });
  podpis(s, "Przykłady: format_danych/przyklady/opis/ (poprawny, z błędnym md5, niezgodny z XSD). Wynik kontroli: demo/wynik/import_opisu.json. Kod: mcod/resources/aed_opis.py, aed_import.py.", M, 6.55, 11.5);
  s.addNotes("Główna ścieżka danych spoza portalu według wskazówek mentora: XML opisuje zbiór i wskazuje plik CSV, a suma md5 potwierdza, że pobrano właśnie ten plik. Kolejność kontroli: kod 200, XSD, pobranie CSV, md5, kolumny i duplikaty, dopiero potem zapis zbioru i zasobu. Niezgodne md5 odrzuca import i nic nie zapisuje. Zmiana md5 przy odświeżeniu zastępuje zasób. Wariant dodatkowy: rekordy wprost w XML (aed_punkty.xsd) jako zasób z linkiem; nocne zadanie waliduje go schematem i scala z CSV.");
}

// 11–13. (warunkowo) zrzuty importu opisu: po jednym na slajd, żeby tekst terminala był czytelny
slajdZrzutu("zrzutOpisXml", { plik: "16_opis_xml_dostawcy.png", tytul: "Dostawca wystawia opis zbioru i plik CSV", wycinek: [1440, 520],
  podpis: "serwer dostawcy (demo/serwer_zewnetrzny.py, dane fikcyjne). GET /opis.xml zwraca 200 i opis z linkiem do CSV i sumą md5; md5 pobranego aed.csv jest taka sama.",
  alt: "Serwer dostawcy: odpowiedź 200 z opisem zbioru w XML (tytuł, dysponent, licencja CC BY 4.0, link do CSV, md5, 7 rekordów) i pobranie aed.csv z tą samą sumą md5" });
slajdZrzutu("zrzutImport", { plik: "17_import_opisu_komenda.png", tytul: "Portal importuje opis, a błędny odrzuca", wycinek: [1440, 660],
  podpis: "komenda import_aed_xml w kontenerze portalu: --dry-run, odrzucenie przy błędnym md5 i przy opisie niezgodnym z XSD (nic nie zapisano), import (zbiór 4251, zasób 40253) i powtórka bez zmian.",
  alt: "Terminal: import_aed_xml z wynikami: dry-run zgodny, błędne md5 odrzucone, opis niezgodny z XSD odrzucony, import utworzył zbiór 4251 i zasób 40253, powtórka bez zmian" });
slajdZrzutu("zrzutZbior", { plik: "18_zbior_z_opisu_w_panelu.png", tytul: "Zbiór z opisu ma w metadanych adres opisu i md5",
  wycinek: [990, 800, 230, 0],
  podpis: "panel portalu, formularz zbioru utworzonego z opisu XML: opis zbioru z XML, „Pola niestandardowe” z wpisami md5, opis_xml i standard = AED, częstotliwość aktualizacji „Codziennie”.",
  alt: "Panel portalu: formularz zbioru utworzonego z opisu XML; w Polach niestandardowych md5, opis_xml i standard = AED, pod nimi podpowiedź Wykazu AED",
  tekst: [
    ["standard = AED. ", "Zbiór trafia do Wykazu AED tak jak zbiór oznaczony ręcznie."],
    ["opis_xml. ", "Adres opisu, z którego zadanie o 4:05 odświeża zbiór."],
    ["md5. ", "Suma CSV z ostatniego importu. Inna suma przy odświeżeniu oznacza nowy plik i zastąpienie zasobu."],
    ["Bez migracji. ", "To istniejąca metadana zbioru (Dataset.customfields)."],
  ] });

// 12. Nocne scalanie: ciemny slajd, jedna duża liczba
{
  const s = slajd("CIEMNY", "scalanie");
  s.addText("Co noc portal scala zasoby w jeden wykaz", { placeholder: "title" });
  const h = zrzut(s, "03_komenda_wykaz_statystyki.png", [1440, 900], M, 1.55, 7.6, 0,
    "Terminal: komenda create_main_aed_resource, dwa zasoby przyjęte, dwa pominięte z powodem, 32 wiersze");
  podpis(s, "Zrzut 03: komenda budująca wykaz. Pełny log: demo/wynik/komenda_create_main_aed_resource.txt", M, 1.55 + h + 0.1, 7.6, K.granatJ);
  tx(s, "32", { x: 8.85, y: 1.45, w: 3.8, h: 1.3, fontSize: 80, bold: true, color: K.zolc });
  tx(s, "wiersze w wykazie z dwóch przyjętych zasobów. Dwa zasoby pominięto, każdy z powodem w logu.",
    { x: 8.85, y: 2.85, w: 3.8, h: 1.2, fontSize: 16, color: K.bialy });
  tx(s, zLead([
    ["Krosno: ", "brak kolumny miejscowosc."],
    ["Marki: ", "brak kolumn minimum."],
    ["Legionowo i wzorzec: ", "przyjęte."],
  ], K.zolc), { x: 8.85, y: 4.1, w: 3.8, h: 1.4, fontSize: 15, color: K.bialy });
  tx(s, "Potem deduplikacja. Nowy wykaz zastępuje poprzedni zasób zbiorczy, tak jak w DGA.", { x: 8.85, y: 5.6, w: 3.8, h: 0.9, fontSize: 15, color: K.granatJ });
}

// 13. Deduplikacja przy budowie wykazu
{
  const s = slajd("TRESC", "dedup");
  s.addText("Ten sam defibrylator od dwóch dostawców trafia do wykazu raz", { placeholder: "title" });
  const reguly = [
    [0.95, "Klucz mocny: numer seryjny. ", "Ten sam numer to to samo urządzenie, chyba że wiersze podają różnych producentów."],
    [1.5, "Klucz słaby: marka i odległość. ", "Tylko między różnymi zasobami: do 30 m i ten sam producent lub model. Bez marki: do 10 m i ta sama nazwa lokalizacji. Różne numery, producenci, modele lub kondygnacje wykluczają duplikat."],
    [1.2, "Który wiersz zostaje. ", "Ten z wyższym poziomem weryfikacji, potem z nowszą datą aktualizacji. Puste pola producent, model i numer_seryjny uzupełnia duplikat."],
    [0.95, "Ślad w logu. ", "Każda para (zachowany, pominięty, powód) trafia do logu, a liczba do statystyki wiersze_zdeduplikowane."],
  ];
  let y = 1.6;
  reguly.forEach(([h, a, b]) => {
    linia(s, M, y, 6.5);
    tx(s, zLead([[a, b]], K.zielen), { x: M, y: y + 0.12, w: 6.5, h: h - 0.15, fontSize: 15 });
    y += h;
  });
  linia(s, M, y, 6.5);
  const xr = 7.8, wr = W - M - xr;
  tx(s, "15 → 14", { x: xr, y: 1.5, w: wr, h: 1.1, fontSize: 60, bold: true, color: K.zielen });
  tx(s, "wierszy w przykładach: plik dostawcy z opisu XML (7) i przykład wzorca (8). Zostaje CT-01, pominięty BYD-HALA-A: ten sam producent i numer seryjny FRX-2026-0001.",
    { x: xr, y: 2.7, w: wr, h: 1.5, fontSize: 15 });
  linia(s, xr, 4.35, wr);
  tx(s, "39 → 38", { x: xr, y: 4.5, w: wr, h: 0.8, fontSize: 40, bold: true, color: K.zielen });
  tx(s, "wierszy w demo/agreguj.py: migawka dane.gov.pl, przykład wzorca i plik dostawcy. Jeden duplikat po numerze seryjnym.",
    { x: xr, y: 5.3, w: wr, h: 1.1, fontSize: 15 });
  podpis(s, "Kod: mcod/resources/aed_dedup.py (bez ORM). Dowody: demo/wynik/weryfikacja.txt, raport_agregacji.txt.", M, 6.55, 11.5);
  s.addNotes("Deduplikacja działa w portalu, przy budowie wykazu, dla wszystkich źródeł (pliki, link, opis XML). Progi z kodu: 30 m dla zgodnej marki lub modelu, 10 m dla zgodnej nazwy bez marki. W obrębie jednego pliku dwa AED w jednym miejscu bez numerów seryjnych to dwa urządzenia, więc nie są łączone.");
}

// 16. (warunkowo) zrzut: budowa wykazu z deduplikacją w portalu
slajdZrzutu("zrzutDedup", { plik: "19_wykaz_deduplikacja.png", tytul: "Deduplikacja w uruchomionym portalu: 45 → 38 wierszy",
  wycinek: [1440, 470],
  podpis: "create_main_aed_resource --eager po imporcie opisu XML (wybrane linie logu). Zasoby przyjęte 4, pominięte 3 z powodem; 45 wierszy przed deduplikacją, 38 po, 7 duplikatów (6 po nazwie i lokalizacji, 1 po numerze seryjnym). Statystyki: demo/wynik/statystyki_opis_dedup.json.",
  alt: "Terminal: budowa Wykazu AED; trzy zasoby pominięte z powodem, siedem duplikatów pominiętych z powodem, wykaz ma 38 wierszy" });

// (warunkowo) po deduplikacji: API i tabela wykazu z numerem seryjnym (zrzuty 21 i 22)
if (jestZrzut("21_api_wykaz_numer_seryjny.png") && jestZrzut("22_wykaz_tabela_opis.png")) {
  const s = slajd("TRESC", "zrzutPoDedup");
  s.addText("Po deduplikacji: jeden wiersz na urządzenie", { placeholder: "title" });
  const top = 1.5, kw = 5.85;
  const [w1, h1] = zrzutWycinek(s, "21_api_wykaz_numer_seryjny.png", M, top, kw, 3.2, [1000, 620, 0, 0],
    "Odpowiedź API zasobu wykazu: 38 wierszy, 52 kolumny, 10 wierszy z numerem seryjnym; wiersze OL-001 i CT-01 z producentem, modelem i numerem");
  const [w2, h2] = zrzutWycinek(s, "22_wykaz_tabela_opis.png", M + kw + 0.5, top, kw, 3.2, [1300, 520, 80, 380],
    "Tabela Wykazu AED we froncie portalu: kolumny producent, model, numer_seryjny z wartościami FRX-2026-1101, ZP-2026-1102, DL-2026-1103");
  podpis(s, "Zrzut 21: wybrane pola GET /1.4/resources/40258/data (sformatowane): 38 wierszy, 52 kolumny, 10 wierszy z numerem seryjnym.", M, top + h1 + 0.1, w1);
  podpis(s, `Zrzut 22: ${opisZrzutu("22_wykaz_tabela_opis.png", "tabela Wykazu AED z kolumną numer_seryjny.")}`, M + kw + 0.5, top + h2 + 0.1, w2);
  tx(s, zLead([["Uzupełnianie z duplikatu. ", "Wiersz OL-001 z zasobu XML nie miał producenta, modelu ani numeru. Po scaleniu ma je z tego samego urządzenia podanego w CSV z opisu."]], K.zielen),
    { x: M, y: 5.8, w: 11.9, h: 0.7, fontSize: 15 });
  s.addNotes("Zrzuty z portalu uruchomionego lokalnie w Dockerze (zasób wykazu 40258). Opis zrzutów: demo/zrzuty/README.md.");
}

// 15. Odbiorca, tabela: zrzut na całą szerokość, pod nim trzy zdania w kolumnach
{
  const s = slajd("TRESC", "tabela");
  s.addText("Odbiorca przegląda wykaz jak każdy zasób portalu", { placeholder: "title" });
  const w = W - 2 * M;
  const h = zrzut(s, "04_wykaz_tabela.png", [1440, 2071], M, 1.4, w, 470,
    "Frontend portalu: zasób Wykaz defibrylatorów AED, zakładka Tabela z kolumnami wzorca");
  const y = 1.4 + h + 0.2;
  const kol = [
    ["Wyszukiwanie. ", "Odbiorca wpisuje „Wykaz defibrylatorów AED”, otwiera zasób i wybiera zakładkę Tabela."],
    ["Praca z tabelą. ", "Filtruje i sortuje 52 kolumny, pobiera CSV albo JSON-LD."],
    ["Pochodzenie. ", "Każdy wiersz ma wydawcę, licencję, zasób źródłowy i datę agregacji, jak wymaga CC BY 4.0."],
  ];
  kol.forEach(([a, b], i) => tx(s, zLead([[a, b]], K.zielen), { x: M + i * 4.1, y, w: 3.8, h: 1.6, fontSize: 15 }));
  podpis(s, "Zrzut 04: frontend portalu, zasób „Wykaz defibrylatorów AED”, zakładka Tabela.", M, 6.5, 11);
}

// 16. Mapa: zrzut po lewej, tytuł i tekst po prawej
{
  const s = slajd("TRESC", "mapa");
  const h = zrzut(s, "05_wykaz_mapa.png", [1440, 900], M, 0.7, 7.7, 0,
    "Frontend portalu: zakładka Mapa z punktami AED w Bydgoszczy i klastrem 24 punktów z Legionowa");
  podpis(s, "Zrzut 05: zakładka Mapa zasobu zbiorczego.", M, 0.7 + h + 0.1, 7.7);
  s.addText("Mapa włącza się sama, bez nowego frontendu", { x: 8.9, y: 0.7, w: 3.75, h: 1.6, fontSize: 28, bold: true,
    color: K.granat, fontFace: FONT, margin: 0, valign: "top" });
  tx(s, akapity([
    "Schemat zasobu zbiorczego ma pole geo (szerokość, długość, etykieta), więc portal sam pokazuje swój widok mapy.",
    "Na mapie są 24 punkty z Legionowa i 8 z przykładu wzorca w Bydgoszczy. Kliknięcie punktu otwiera rekord.",
  ]), { x: 8.9, y: 2.5, w: 3.75, h: 3.4, fontSize: 16, paraSpaceAfter: 12 });
}

// 17. API: dwa zrzuty obok siebie
{
  const s = slajd("TRESC", "api");
  s.addText("Dane wykazu są w API razem z atrybucją dostawcy", { placeholder: "title" });
  const w = 5.85;
  const h1 = zrzut(s, "06_api_aed_aggregated.png", [1440, 900], M, 1.5, w, 0,
    "Odpowiedź GET /1.4/aed-aggregated z identyfikatorami zbioru i zasobu zbiorczego");
  zrzut(s, "07_api_dane_zasobu.png", [1440, 1497], M + w + 0.4, 1.5, w, 900,
    "Odpowiedź GET /1.4/resources/40247/data: 32 rekordy z kolumnami pochodzenia");
  podpis(s, "Zrzut 06: GET /1.4/aed-aggregated, stały adres wykazu (odpowiednik /dga-aggregated).", M, 1.5 + h1 + 0.1, w);
  podpis(s, "Zrzut 07: GET /1.4/resources/40247/data, meta.count = 32 i kolumny pochodzenia.", M + w + 0.4, 1.5 + h1 + 0.1, w);
  tx(s, zLead([["Formaty maszynowe: ", "CSV (RFC 4180, UTF-8), JSON-LD i JSON:API portalu oraz schematy Table Schema, CSVW, XSD, kontekst JSON-LD i metadane DCAT-AP."]], K.zielen),
    { x: M, y: 6.0, w: 12, h: 0.7, fontSize: 15 });
}

// 18. Testy: jedna duża liczba, zrzut mniejszy
{
  const s = slajd("TRESC", "testy");
  s.addText("Testy przechodzą, migracji brak", { placeholder: "title" });
  tx(s, String(TESTY_PASSED), { x: M, y: 1.45, w: 4.5, h: 1.6, fontSize: 110, bold: true, color: K.zielen });
  tx(s, `testów przeszło ${TESTY_DATA} w kontenerze portalu. ${TESTY_SKIPPED} pominięte: porównanie kopii XSD, które wykonuje demo/sprawdz.py.`,
    { x: M, y: 3.15, w: 4.6, h: 0.95, fontSize: 15 });
  tx(s, zLead([
    ["Testy AED: ", "CSV, XML, opis zbioru z md5 i deduplikacja. Logika ramek danych bez bazy, ORM i Celery na wzór testów DGA."],
    ["Regresja DGA: ", "istniejące testy przechodzą bez zmian."],
    ["Zero migracji: ", "makemigrations --check zwraca „No changes detected”."],
    ["Kontrole maszynowe: ", `${KONTROLE} PASS w demo/wynik/weryfikacja.txt.`],
  ], K.granat), { x: M, y: 4.2, w: 4.6, h: 2.25, fontSize: 14, paraSpaceAfter: 6 });
  const aktualny = ZRZUT09_PASSED === TESTY_PASSED;
  const h = zrzut(s, "09_testy.png", [1440, 900], 5.7, 1.5, 6.95, 0,
    `Wynik pytest w kontenerze: ${ZRZUT09_PASSED} passed oraz makemigrations --check: No changes detected`);
  podpis(s, aktualny ? "Zrzut 09: testy w kontenerze portalu. Pełny log: demo/wynik/testy.txt"
    : `Zrzut 09: wcześniejszy przebieg w kontenerze (${ZRZUT09_PASSED} passed, przed opisem XML i deduplikacją). Aktualny pełny log: demo/wynik/testy.txt`,
  5.7, 1.5 + h + 0.1, 6.95);
}

// 19. Dodatek: integrator
{
  const s = slajd("TRESC", "integrator");
  s.addText("Dodatek: integrator dla dostawców bez wzorcowego formatu", { placeholder: "title" });
  tx(s, "Krok 2, dodatek: Wykaz AED działa bez niego. Integrator to osobna aplikacja, bez zmian w portalu: przygotowuje plik CSV i opis XML, które portal pobiera.",
    { x: M, y: 1.45, w: 12, h: 0.9, fontSize: 16, color: K.szary });
  const w = [
    ["Dane z innych formatów", "CSV, TSV, XLSX, GeoJSON i OSM: mapowanie kolumn, normalizacja i walidacja do wzorca.", "Warszawa: API z tokenem, czytamy zapisaną odpowiedź. Gdańsk: dane flotowe, więc raport zamiast wierszy."],
    ["Opis zbioru XML", "Podkomenda opis buduje z gotowego CSV opis zgodny z aed_opis_zbioru.xsd i liczy sumę md5.", "Sprawdza minimum kolumn, licencję, słowniki i link https. Portal zaczytuje opis komendą import_aed_xml."],
    ["Dane z formularza", "Lokalny interfejs i polecenie dodaj: dostawca bez własnego systemu wpisuje rekord, a integrator go sprawdza.", "Licencja źródła jest jawna, a dane z OSM (ODbL) zostają tylko lokalnie."],
    ["Porównanie z OSM", "Raport: w obu zbiorach, tylko w wykazie, tylko w OSM. Osobno lista kandydatów na duplikaty, tylko do wglądu.", `${TESTY_INTEGRATORA} testów bez Dockera, wyniki w demo/integrator/.`],
  ];
  let y = 2.45;
  w.forEach(([t, d1, d2]) => {
    linia(s, M, y, 12);
    tx(s, t, { x: M, y: y + 0.12, w: 2.4, h: 0.9, fontSize: 16, bold: true, color: K.zielen });
    tx(s, d1, { x: M + 2.6, y: y + 0.12, w: 4.6, h: 0.9, fontSize: 15 });
    tx(s, d2, { x: M + 7.4, y: y + 0.12, w: 4.6, h: 0.9, fontSize: 15, color: K.szary });
    y += 0.98;
  });
  linia(s, M, y, 12);
  tx(s, "Planowane: tryb pośrednika między API dostawcy a harvesterem portalu.", { x: M, y: 6.55, w: 12, h: 0.4, fontSize: 14, bold: true, color: K.czerwien });
  s.addNotes("Deduplikację, która usuwa duplikaty z wykazu, robi portal (aed_dedup.py). Integrator tylko wskazuje kandydatów i niczego nie scala. Pośrednik (tłumaczenie zapytań harvestera na API dostawcy i z powrotem) jest zapisany jako zadanie, nie jako gotowa funkcja.");
}

// (warunkowo) integrator w praktyce: zrzuty lokalnego interfejsu i terminala (dodatek, krok 2)
const notatkaIntegratora = "Zrzuty integratora (dodatek, krok 2), nie portalu: lokalny interfejs python integrator/ui/serwer.py pod 127.0.0.1 i terminal. Opis zrzutów: demo/zrzuty/README.md, sekcja integratora.";
if (jestZrzut("integrator_01_import_mapowanie.png") && jestZrzut("integrator_02_walidacja.png")) {
  const s = slajd("TRESC", "integratorZrzut1");
  s.addText("Dodatek: integrator przepisuje plik dostawcy na wzorzec", { placeholder: "title" });
  tx(s, "KROK 2, DODATEK POZA PORTALEM. Lokalny interfejs integratora (127.0.0.1)", { x: M, y: 1.08, w: 11.9, h: 0.3, fontSize: 12, bold: true, color: K.szary });
  const top = 1.5;
  const [w1, h1] = zrzutWycinek(s, "integrator_01_import_mapowanie.png", M, top, 5.4, 4.3, [1000, 900, 220, 190],
    "Integrator, zakładka Import i mapowanie: plik TSV sieci sklepów, cel portal, licencja CC0 1.0 i mapowanie kolumn w JSON");
  const x2 = M + w1 + 0.45, kw2 = W - M - x2;
  const [w2, h2] = zrzutWycinek(s, "integrator_02_walidacja.png", x2, top, kw2, 3.3, [1000, 540, 220, 200],
    "Integrator, zakładka Walidacja: 4 wiersze, 3 poprawne, 1 odrzucony z powodem, licencja CC0 1.0 dopuszczalna, przycisk pobrania CSV");
  podpis(s, "Zrzut integrator_01: eksport sieci sklepów (TSV, CP1250, własne nazwy kolumn, dane fikcyjne) i zapisane mapowanie kolumn w JSON.", M, top + h1 + 0.1, w1);
  podpis(s, "Zrzut integrator_02: raport walidacji. Wiersz 5 odrzucony (brak dostepny_24_7), ostrzeżenie o elektrodach po terminie.", x2, top + h2 + 0.1, w2);
  tx(s, zLead([
    ["Do portalu trafiają tylko poprawne wiersze, ", "a licencja musi być jawna: CC0 1.0 albo CC BY 4.0."],
    ["Plik nie opuszcza komputera. ", "Serwer słucha tylko na 127.0.0.1 i niczego nie zapisuje na dysku."],
  ], K.granat), { x: x2, y: top + h2 + 0.75, w: kw2, h: 6.5 - (top + h2 + 0.75), fontSize: 14, paraSpaceAfter: 8 });
  s.addNotes(notatkaIntegratora);
}
if (jestZrzut("integrator_04_opis_xml_md5.png") && jestZrzut("integrator_03_porownanie_osm.png")) {
  const s = slajd("TRESC", "integratorZrzut2");
  s.addText("Dodatek: opis XML z sumą md5 i porównanie z OSM", { placeholder: "title" });
  tx(s, "KROK 2, DODATEK POZA PORTALEM. Terminal i lokalny interfejs integratora", { x: M, y: 1.08, w: 11.9, h: 0.3, fontSize: 12, bold: true, color: K.szary });
  const top = 1.5;
  const [w1, h1] = zrzutWycinek(s, "integrator_04_opis_xml_md5.png", M, top, 7.3, 4.4, [1220, 793, 0, 0],
    "Terminal: importer.py opis zapisuje opis.xml z md5 f093977d…, md5sum pliku daje tę samą sumę, opis zgodny z XSD; z licencją ODbL polecenie kończy się błędem");
  const x2 = M + w1 + 0.45, kw2 = W - M - x2;
  const [w2, h2] = zrzutWycinek(s, "integrator_03_porownanie_osm.png", x2, top, kw2, 3.0, [1040, 620, 200, 560],
    "Integrator, zakładka Porównanie z OSM: w obu 0, tylko w wykazie 38, tylko w OSM 2; tabela Tylko w wykazie z id_aed i nazwami lokalizacji z Legionowa");
  podpis(s, "Zrzut integrator_04: podkomenda opis na aed_dostawcy.csv (7 rekordów). Suma w opisie równa md5sum pliku, opis zgodny z aed_opis_zbioru.xsd; licencja ODbL odrzucona.", M, top + h1 + 0.1, w1);
  podpis(s, "Zrzut integrator_03: wykaz (38 wierszy) i próbka OSM (2 punkty), początek tabeli „Tylko w wykazie”. Raport tylko lokalnie, ODbL.", x2, top + h2 + 0.1, w2);
  tx(s, zLead([
    ["Ten opis zaczytuje portal: ", "import_aed_xml, a potem co noc refresh_aed_opis_task."],
    ["OSM tylko do porównań. ", "Dane ODbL nie trafiają do wykazu."],
  ], K.granat), { x: x2, y: top + h2 + 0.85, w: kw2, h: 6.6 - (top + h2 + 0.85), fontSize: 14, paraSpaceAfter: 6 });
  s.addNotes(notatkaIntegratora);
}

// 20. Ograniczenia: dwie kolumny tekstu, bez kart
{
  const s = slajd("TRESC", "ograniczenia");
  s.addText("Czego wykaz jeszcze nie robi", { placeholder: "title" });
  const o = [
    ["Realne źródła. ", "Większość zasobów AED w portalu nie ma dziś kolumn wzorca. Wykaz pomija je z powodem; z realnych danych przyjęto Legionowo (24 punkty)."],
    ["Warszawa i Gdańsk. ", "Warszawa: w portalu tylko strona WWW, dane w API z tokenem. Gdańsk: dane flotowe, nie punkty."],
    ["Typy zgadywane przez portal. ", "Walidacja portalu może oznaczyć błędem plik zgodny ze wzorcem (np. „5A” w numerze budynku); wykaz czyta go wprost."],
    ["Deduplikacja heurystyczna. ", "Numer seryjny jest opcjonalny, a realne pliki z portalu go nie mają. Wtedy decyduje odległość z marką lub nazwą, i to tylko między różnymi zasobami."],
    ["Wersja live i film. ", "Link przez ngrok (WERSJA_LIVE.md) działa tylko przy włączonym tunelu. Film pokazuje ścieżkę z plikiem CSV, bez opisu XML i deduplikacji."],
    ["Planowane. ", "Integrator jako pośrednik między API dostawcy a harvesterem i osobna strona „Wykaz AED” we froncie."],
    ["Akcja promocyjna. ", "To projekt znaku i materiałów; zachęty oznaczone jako propozycje nie są wdrożone. Kolizji nazwy (UPRP, EUIPO, domeny) nie sprawdzaliśmy."],
  ];
  [0, 1].forEach((k) => {
    tx(s, zLead(o.slice(k * 4, k * 4 + 4), K.czerwien), { x: M + k * 6.2, y: 1.5, w: 5.75, h: 5.1, fontSize: 15, paraSpaceAfter: 12 });
  });
}

// 21. Akcja promocyjna
{
  const s = slajd("CIEMNY", "akcja");
  s.addText("Dane (prze)życie: nazwa, hasło i znak akcji", { placeholder: "title" });
  const lp = P("branding", "logo", "dane-przezycie_logo_pionowe_negatyw.png");
  s.addImage({ path: lp, x: M, y: 1.5, w: 3.5, h: hPNG(lp, 3.5),
    altText: "Logo akcji w układzie pionowym na granatowym tle z hasłem Twoje dane – czyjeś życie" });
  tx(s, [
    { text: "Twoje dane – czyjeś życie.", options: { bold: true, color: K.zolc, fontSize: 26, breakLine: true } },
    { text: "Czerwona linia migotania komór i zielony rytm serca spotykają się w środku folderu z danymi. Chaos zamienia się w porządek dwa razy: w sercu po defibrylacji i w danych po publikacji według jednego wzorca. Nawias w nazwie daje dwa odczytania: „dane przeżycie” i „dane życie”.",
      options: { fontSize: 16 } },
  ], { x: 4.8, y: 1.5, w: 7.8, h: 2.3, color: K.bialy, paraSpaceAfter: 12 });
  const mat = [
    ["dane-przezycie_naklejka_A6.png", "Naklejka A6 na szafkę AED"],
    ["dane-przezycie_odznaka_dysponenta.png", "Odznaka dysponenta"],
    ["dane-przezycie_post_1080.png", "Post do mediów społecznościowych"],
  ];
  let x = 4.8;
  mat.forEach(([f, alt]) => {
    const pl = P("branding", "materialy", f);
    const h = 2.3, w = (h * h) / hPNG(pl, h);
    s.addImage({ path: pl, x, y: 3.95, w, h, altText: alt });
    tx(s, alt, { x, y: 6.35, w: Math.max(w, 1.9), h: 0.3, fontSize: 12, color: K.granatJ });
    x += w + 0.3;
  });
  tx(s, "Księga znaku: branding/ksiega_znaku.pdf. Logotyp w JPG, PNG, PDF i SVG: branding/logo/",
    { x: M, y: 6.95, w: 10, h: 0.3, fontSize: 12, color: K.granatJ });
}

// 22. Akcja: co zyskuje dysponent
{
  const s = slajd("TRESC", "korzysci");
  s.addText("Co zyskuje dysponent, który udostępnia dane", { placeholder: "title" });
  const kr = [
    ["1", "Wzorzec", "Dysponent pobiera XLSX lub CSV z zakresem danych."],
    ["2", "Publikacja", "Zasób w zbiorze z wpisem standard = AED albo opis XML z linkiem do CSV."],
    ["3", "Wykaz", "Co noc portal dołącza zasób do wykazu."],
  ];
  let y = 1.6;
  kr.forEach(([n, t, d]) => {
    linia(s, M, y, 4.6, K.granat, 1.5);
    tx(s, n, { x: M, y: y + 0.1, w: 0.7, h: 0.8, fontSize: 36, bold: true, color: K.szary });
    tx(s, [{ text: t, options: { bold: true, fontSize: 18, breakLine: true } }, { text: d, options: { fontSize: 14, color: K.szary } }],
      { x: M + 0.8, y: y + 0.14, w: 3.8, h: 1.0 });
    y += 1.25;
  });
  tx(s, zLead([
    ["Odzyskanie AED po akcji. ", "Wykaz podaje dysponenta, kontakt do opiekuna i numer seryjny, jeśli dysponent go poda. Po użyciu wiadomo, do kogo zwrócić urządzenie."],
    ["Naklejka A6 na szafkę. ", "Z ID z wykazu, datą sprawdzenia i kodem QR do zgłoszenia problemu."],
    ["Odznaka „Nasze AED są w Wykazie AED”. ", "Na stronie, w stopce e-maila i przy wejściu."],
    ["Propozycje rozwoju: ", "przypomnienia o terminach elektrod i baterii, ranking gmin, wyróżnienie „Gmina z otwartym AED” 16 października."],
  ], K.zielen), { x: 6.0, y: 1.6, w: 6.65, h: 4.8, fontSize: 16, paraSpaceAfter: 14 });
  podpis(s, "Opis akcji: branding/AKCJA_DANE_PRZEZYCIE.md. Naklejka i odznaka: branding/materialy/.", M, 6.55, 11.9);
  s.addNotes("Zwrot urządzenia po użyciu opiera się na danych dysponenta, kontakcie funkcyjnym i numerze seryjnym (opcjonalnym od wzorca 2.1.0). Przypomnienia, ranking i wyróżnienie to propozycje poza zakresem prototypu.");
}

// 23. Jak sprawdzić i użycie AI
{
  const s = slajd("CIEMNY", "sprawdzenie");
  s.addText("Jak to sprawdzić bez stawiania środowiska", { placeholder: "title" });
  const kroki = [
    ["INSTRUKCJA_DLA_JURY.md", "krótka ścieżka sprawdzenia w ponumerowanych krokach"],
    ["DODATKOWE_INFORMACJE.md", "każde wymaganie zadania w osobnym kroku, z plikiem dowodowym"],
    ["demo/index.html", "klikalny prototyp całego procesu, działa offline"],
    ["demo/wynik/weryfikacja.txt", `${KONTROLE} kontroli maszynowych PASS (python demo/sprawdz.py)`],
    ["ZMIANY_W_PORTALU.md", "lista zmian w kodzie portalu i diff względem oryginału"],
    ["branding/ksiega_znaku.pdf", "księga znaku akcji Dane (prze)życie"],
  ];
  let y = 1.45;
  kroki.forEach(([f, d]) => {
    linia(s, M, y, 12, K.szary);
    tx(s, f, { x: M, y: y + 0.11, w: 4.9, h: 0.35, fontSize: 15, bold: true, color: K.zolc, fontFace: MONO });
    tx(s, d, { x: M + 5.0, y: y + 0.11, w: 7.0, h: 0.35, fontSize: 15, color: K.bialy });
    y += 0.52;
  });
  linia(s, M, y, 12, K.szary);
  tx(s, zLead([["Użycie AI. ", "Asystentów AI (Claude, Cursor) używaliśmy do wsparcia analizy kodu portalu, pisania kodu i implementacji testów oraz do wsparcia tworzenia księgi znaku i plików znaku, a także przy redakcji dokumentów, zrzutach ekranu i składaniu prezentacji. Kierunek rozwiązania, decyzje o danych, licencjach i ochronie danych oraz wybór znaku należą do zespołu. Każdą zmianę sprawdziliśmy testami i w uruchomionym portalu."]], K.zolc),
    { x: M, y: y + 0.3, w: 11.2, h: 1.9, fontSize: 15, color: K.bialy });
}

// ---- README z mapą slajdów (numery liczone przy budowie, bo slajdy ze zrzutami są warunkowe) ----
function zakres(...klucze) {
  const n = klucze.map((k) => nr[k]).filter(Boolean).sort((a, b) => a - b);
  if (!n.length) return "";
  const r = [];
  let a = n[0], b = n[0];
  for (const x of n.slice(1)) { if (x === b + 1) b = x; else { r.push(a === b ? `${a}` : `${a}–${b}`); a = b = x; } }
  r.push(a === b ? `${a}` : `${a}–${b}`);
  return r.join(", ");
}
const zrzutoweKlucze = ["dostawca1", "dostawca2", "zrzutOpisXml", "zrzutImport", "zrzutZbior", "scalanie", "zrzutDedup", "zrzutPoDedup", "tabela", "mapa", "api", "testy"];
const README = `# Prezentacja

- [\`dane_przezycie_prezentacja.pdf\`](dane_przezycie_prezentacja.pdf): wersja do czytania (${licznik} slajdów).
- [\`dane_przezycie_prezentacja.pptx\`](dane_przezycie_prezentacja.pptx): wersja edytowalna (PowerPoint).

| Wymaganie (\`references/zadanie_konkursowe.pdf\` §4) | Slajdy |
|---|---|
| min. 5 slajdów z dowodami na realizację wymagań technicznych (zrzuty ekranu) | ${zakres(...zrzutoweKlucze)}: zrzuty z portalu uruchomionego lokalnie (podpisy jak w [\`../demo/zrzuty/README.md\`](../demo/zrzuty/README.md)) |
| opis funkcjonalności, w tym kroków użytkownika | ${zakres("problem", "zrodla")} (problem i źródła), ${zakres("praktyka1", "praktyka2", "wzorzec")} (z potrzeb do pól wzorca), ${nr.mechanizm} (mechanizm), ${zakres("dostawca1", "dostawca2")} (kroki dostawcy), ${zakres("opis", "zrzutOpisXml", "zrzutImport", "zrzutZbior")} (integracja przez API: opis XML, XSD, CSV, md5), ${nr.scalanie} (scalanie), ${zakres("dedup", "zrzutDedup", "zrzutPoDedup")} (deduplikacja), ${zakres("tabela", "mapa", "api")} (kroki odbiorcy) |
| lista ograniczeń | ${nr.ograniczenia} |
| akcja promocyjna: nazwa, hasło, logotyp, korzyści dla dysponentów | ${zakres("tytul", "akcja", "korzysci")} |
| dodatek: integrator danych (poza portalem, krok 2), w tym zrzuty lokalnego interfejsu i terminala | ${zakres("integrator", "integratorZrzut1", "integratorZrzut2")} |
| zakres użycia AI (\`regulamin_zadania.pdf\` §2 ust. 8) | ${nr.sprawdzenie} |

Liczby na slajdach pochodzą z plików w [\`../demo/wynik/\`](../demo/wynik/) (\`testy.txt\`, \`weryfikacja.txt\`, \`raport_agregacji.txt\`, \`import_opisu.json\`) i [\`../demo/integrator/\`](../demo/integrator/README.md) (slajdy ${zakres("integrator", "integratorZrzut1", "integratorZrzut2")}). Liczby testów i plików są stałymi na początku \`build_prezentacja.js\` (\`TESTY_PASSED\`, \`TESTY_SKIPPED\`, \`KONTROLE\`, \`PLIKI_NOWE\`). Slajdy z plikami zrzutów \`16\`–\`19\` i \`21\`–\`22\` (opis XML, import, zbiór z opisu, wykaz po deduplikacji, API i tabela z numerem seryjnym) oraz \`integrator_01\`–\`04\` skrypt dodaje tylko wtedy, gdy pliki są w \`demo/zrzuty/\`; numery slajdów w tej tabeli liczy przy budowie. Krój w prezentacji to Atkinson Hyperlegible z księgi znaku. PDF ma go osadzonego; w PPTX bez zainstalowanego kroju PowerPoint podstawi inny, więc do czytania służy PDF (krój: branding/fonty/).

## Regeneracja

\`\`\`bash
npm install pptxgenjs@3.12.0 jszip                # w dowolnym katalogu
NODE_PATH=<ten katalog>/node_modules node prezentacja/build_prezentacja.js   # PPTX i ten README
powershell -File prezentacja/eksport_pdf.ps1      # PDF przez PowerPoint (Windows)
\`\`\`
`;

// pptxgenjs zapisuje w ZIP-ie wpisy katalogów, przez które pliki bywają odrzucane przez usługi chmurowe: usuwamy je
const JSZip = require("jszip");
pres.write({ outputType: "nodebuffer" })
  .then((buf) => JSZip.loadAsync(buf, { createFolders: false }))
  .then(async (zip) => {
    const out = new JSZip(); // zip.remove() na katalogu usuwa też jego zawartość, więc kopiujemy same pliki
    for (const n of Object.keys(zip.files).filter((n) => !zip.files[n].dir)) {
      out.file(n, await zip.files[n].async("nodebuffer"), { createFolders: false });
    }
    return out.generateAsync({ type: "nodebuffer", compression: "DEFLATE" });
  })
  .then((buf) => {
    fs.writeFileSync(OUT, buf);
    fs.writeFileSync(P("prezentacja", "README.md"), README);
    console.log("OK:", OUT, `(${licznik} slajdów)`);
    console.log("Slajdy:", JSON.stringify(nr));
  });
