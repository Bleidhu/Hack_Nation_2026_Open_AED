// Prezentacja „Dane (prze)życie: Wykaz AED w portalu dane.gov.pl” (PPTX).
//   npm install pptxgenjs@3.12.0   (w dowolnym katalogu; potem NODE_PATH=<ten katalog>/node_modules)
//   node prezentacja/build_prezentacja.js
// PDF: eksport z PowerPointa (prezentacja/eksport_pdf.ps1).
// Liczby na slajdach pochodzą z demo/wynik/ (testy.txt, statystyki_agregacji.json) i demo/zrzuty/README.md.
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..");
const P = (...p) => path.join(ROOT, ...p);
// wysokość obrazu PNG dla zadanej szerokości (wymiary z nagłówka IHDR)
const hPNG = (plik, w) => { const b = fs.readFileSync(plik); return (w * b.readUInt32BE(20)) / b.readUInt32BE(16); };
const OUT = P("prezentacja", "dane_przezycie_prezentacja.pptx");

const K = { granat: "0E2A47", zielen: "007A45", czerwien: "C8102E", mieta: "F2F7F4", zolc: "FFC629",
  zielenJ: "4ADE9A", czerwienJ: "FF7A85", szary: "3B5068", ramka: "C9D6CF", bialy: "FFFFFF" };
const FONT = "Arial"; // zastępczy krój z księgi znaku: Atkinson Hyperlegible nie jest instalowany z Office

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13,333 × 7,5 cala
pres.title = "Dane (prze)życie: Wykaz AED w portalu dane.gov.pl";
pres.subject = "HackNation 2026, zadanie „Misja AED – Dane na ratunek”";
pres.author = "Zespół projektu Dane (prze)życie";
pres.lang = "pl-PL";
pres.theme = { headFontFace: FONT, bodyFontFace: FONT };

const W = 13.333, M = 0.6;
const STOPKA = "Dane (prze)życie · Wykaz AED w portalu dane.gov.pl";

pres.defineSlideMaster({
  title: "TRESC",
  background: { color: K.bialy },
  objects: [
    { image: { path: P("branding", "logo", "dane-przezycie_sygnet.png"), x: M, y: 6.9, w: 0.34,
      h: hPNG(P("branding", "logo", "dane-przezycie_sygnet.png"), 0.34) } },
    { text: { text: STOPKA, options: { x: M + 0.42, y: 6.92, w: 8, h: 0.3, fontSize: 10, color: K.szary, margin: 0, valign: "middle" } } },
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.4, w: W - 2 * M, h: 0.9, fontSize: 30, bold: true,
      color: K.granat, valign: "top", align: "left", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: W - M - 0.6, y: 6.92, w: 0.6, h: 0.3, fontSize: 10, color: K.szary, align: "right" },
});
pres.defineSlideMaster({
  title: "CIEMNY",
  background: { color: K.granat },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.4, w: W - 2 * M, h: 0.9, fontSize: 30, bold: true,
      color: K.bialy, valign: "top", align: "left", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: W - M - 0.6, y: 6.92, w: 0.6, h: 0.3, fontSize: 10, color: K.mieta, align: "right" },
});

const tx = (slide, text, o) => slide.addText(text, Object.assign({ isTextBox: true, fontFace: FONT, color: K.granat,
  fontSize: 15, margin: 0, valign: "top" }, o));

// lista numerowana lub punktowana: tablica stringów albo [pogrubione, reszta]
function lista(slide, items, o, numer = true) {
  const runs = [];
  items.forEach((it, i) => {
    const last = i === items.length - 1;
    const base = { bullet: numer ? { type: "number" } : true, paraSpaceAfter: 8, breakLine: !last };
    if (Array.isArray(it)) {
      runs.push({ text: it[0], options: Object.assign({}, base, { bold: true, breakLine: false }) });
      runs.push({ text: it[1], options: { breakLine: !last } });
    } else runs.push({ text: it, options: base });
  });
  tx(slide, runs, Object.assign({ fontSize: 15 }, o));
}

// zrzut ekranu z ramką; crop = ile pikseli wysokości oryginału pokazać (od góry)
function zrzut(slide, plik, px, x, y, w, crop, alt) {
  const [pw, ph] = px;
  const fullH = (w * ph) / pw;
  const h = crop ? (w * crop) / pw : fullH;
  slide.addShape(pres.shapes.RECTANGLE, { x: x - 0.03, y: y - 0.03, w: w + 0.06, h: h + 0.06, fill: { color: K.ramka },
    line: { color: K.ramka } });
  const o = { path: P("demo", "zrzuty", plik), x, y, w, h: crop ? fullH : h, altText: alt };
  if (crop) o.sizing = { type: "crop", x: 0, y: 0, w, h };
  slide.addImage(o);
  return h;
}

function podpis(slide, text, x, y, w) {
  tx(slide, text, { x, y, w, h: 0.5, fontSize: 11, color: K.szary, italic: true });
}

function karta(slide, x, y, w, h, tytul, tresc, o = {}) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: o.tlo || K.mieta },
    line: { color: o.tlo || K.mieta } });
  tx(slide, tytul, { x: x + 0.2, y: y + 0.16, w: w - 0.4, h: 0.4, fontSize: o.tytulSize || 16, bold: true,
    color: o.kolorTytulu || K.granat });
  tx(slide, tresc, { x: x + 0.2, y: y + 0.6, w: w - 0.4, h: h - 0.7, fontSize: o.size || 14, color: o.kolor || K.granat });
}

function liczba(slide, x, y, w, wartosc, etykieta, kolor = K.zielen) {
  tx(slide, wartosc, { x, y, w, h: 0.8, fontSize: 44, bold: true, color: kolor });
  tx(slide, etykieta, { x, y: y + 0.8, w, h: 0.6, fontSize: 13, color: K.granat });
}

const slajd = (master = "TRESC") => pres.addSlide({ masterName: master });

// 1. Tytuł
{
  const s = slajd("CIEMNY");
  s.addImage({ path: P("branding", "logo", "dane-przezycie_logo_poziome_negatyw.png"), x: M - 0.15, y: 0.9, w: 8.4,
    h: hPNG(P("branding", "logo", "dane-przezycie_logo_poziome_negatyw.png"), 8.4),
    altText: "Logo akcji Dane (prze)życie: migotanie komór i rytm serca spotykają się w środku folderu z danymi" });
  tx(s, "Wykaz AED w portalu dane.gov.pl", { x: M, y: 3.35, w: 11, h: 0.8, fontSize: 40, bold: true, color: K.bialy });
  tx(s, "Ogólnopolski, otwarty wykaz defibrylatorów z danych wielu dysponentów. Powstał z przerobionego mechanizmu DGA w kodzie portalu, bez migracji bazy.",
    { x: M, y: 4.25, w: 10.5, h: 1.0, fontSize: 18, color: K.mieta });
  tx(s, "Zadanie „Misja AED – Dane na ratunek” · HackNation 2026 · Ministerstwo Cyfryzacji",
    { x: M, y: 6.6, w: 11, h: 0.4, fontSize: 13, color: K.mieta });
  s.addNotes("Tytuł projektu i nazwa akcji. Rozwiązanie to modyfikacja kodu portalu dane.gov.pl, a nie osobna aplikacja.");
}

// 2. Problem
{
  const s = slajd();
  s.addText("Dane o AED są rozproszone, a każdy publikuje je inaczej", { placeholder: "title" });
  const zr = [
    ["Krosno", "plik CSV w portalu; brak kolumny z miejscowością"],
    ["Przemyśl", "link do systemu miasta; 5 dystrybucji tych samych danych"],
    ["Marki", "CSV i XLSX wadliwe: cały wiersz w jednym polu"],
    ["Legionowo", "zasób AED w zbiorze mieszanym „Zdrowie”"],
    ["Warszawa", "w portalu tylko strona WWW; dane w API miasta z tokenem"],
    ["Gdańsk", "AED w 278 pojazdach ZTM, w pliku JSON floty"],
  ];
  const cw = 3.85, ch = 1.45, gx = 0.3, gy = 0.3;
  zr.forEach(([t, d], i) => karta(s, M + (i % 3) * (cw + gx), 1.55 + Math.floor(i / 3) * (ch + gy), cw, ch, t, d));
  tx(s, [
    { text: "W portalu nie ma jednej listy AED. ", options: { bold: true } },
    { text: "Wyszukiwarka nie przeszukuje zawartości tabel, a każdy zbiór ma inne kolumny, formaty i jakość. Ratownik ani mieszkaniec nie dowie się z portalu, gdzie jest najbliższy defibrylator." },
  ], { x: M, y: 5.1, w: 12.1, h: 1.0, fontSize: 16 });
  podpis(s, "Źródło: przegląd API dane.gov.pl z 21.11.2026; kopie zasobów w references/dane_gov_pl_aed/.", M, 6.3, 12);
}

// 3. Rozwiązanie
{
  const s = slajd();
  s.addText("Wykaz AED: mechanizm DGA przerobiony na defibrylatory", { placeholder: "title" });
  const kroki = [
    ["1. Oznaczenie zbioru", "dostawca wpisuje w „Polach niestandardowych”: standard = AED"],
    ["2. Publikacja zasobu", "plik według wzorca; zwykła walidacja portalu"],
    ["3. Nocne scalanie", "zadanie Celery o 4:15 sprawdza kolumny, licencje i dane osobowe"],
    ["4. Wykaz AED", "jeden zasób zbiorczy z tabelą, mapą i API"],
  ];
  const bw = 2.75, gap = 0.37;
  kroki.forEach(([t, d], i) => {
    const x = M + i * (bw + gap);
    karta(s, x, 1.6, bw, 1.9, t, d, i === 3 ? { tlo: K.zielen, kolorTytulu: K.bialy, kolor: K.bialy } : {});
    if (i < 3) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + bw + 0.06, y: 2.4, w: 0.25, h: 0.3,
      fill: { color: K.szary }, line: { color: K.szary } });
  });
  liczba(s, M, 4.0, 3.6, "0 migracji", "żadnych nowych pól ani tabel; oznaczenie przez istniejącą metadaną zbioru");
  liczba(s, M + 4.1, 4.0, 3.9, "22 + 11", "plików: 22 nowe obok DGA i 11 istniejących z dopiskami; nic nie usunięto");
  liczba(s, M + 8.5, 4.0, 3.6, "1 wyłącznik", "AED_AGGREGATION_ENABLED: po wyłączeniu portal działa jak oryginał");
  podpis(s, "Szczegóły: ZMIANY_W_PORTALU.md; diff względem oryginału: git diff a119b1b -- portal/backend.", M, 6.3, 12);
  s.addNotes("Kierunek: zmieniać kod portalu, słowo kluczowe zasób, przerobić DGA, bez migracji, scalać wykazy w jedną listę.");
}

// 4–10: dowody ze zrzutami
function dowod(tytul, plik, px, crop, alt, podp, kroki, nota, numer = true) {
  const s = slajd();
  s.addText(tytul, { placeholder: "title" });
  const h = zrzut(s, plik, px, M, 1.5, 7.7, crop, alt);
  podpis(s, podp, M, 1.5 + h + 0.12, 7.7);
  lista(s, kroki, { x: 8.75, y: 1.5, w: 4.0, h: 3.4 }, numer);
  if (nota) karta(s, 8.75, 4.75, 4.0, 1.75, nota[0], nota[1], { size: 12 });
  return s;
}

dowod("Dostawca, krok 1: oznacza zbiór jako AED", "01_formularz_zbioru_standard_aed.png", [1440, 900], 0,
  "Formularz zbioru w panelu portalu: w Polach niestandardowych wpis standard = AED i podpowiedź pod polem",
  "Zrzut 01: panel portalu uruchomionego lokalnie (Docker), zbiór z Legionowa.",
  ["Otwiera formularz swojego zbioru w panelu.", "W „Polach niestandardowych” dodaje klucz standard i wartość AED (dopuszczalne np. „AED 1.1”).",
    "Podpowiedź pod polem mówi, co wpisać."],
  ["Bez migracji, tagów i checkboxa", "Istniejąca metadana zbioru (Dataset.customfields), zgodnie z zaleceniem organizatora."]);

dowod("Dostawca, krok 2: publikuje zasób według wzorca", "02_zasoby_dostawcow.png", [1440, 1234], 900,
  "Lista zasobów w panelu: pięć zasobów dostawców i zasób zbiorczy Wykaz defibrylatorów AED",
  "Zrzut 02: lista zasobów w panelu, pięć zasobów dostawców i zasób zbiorczy.",
  ["Pobiera szablon XLSX lub CSV wzorcowego zakresu.", "Wypełnia kolumny; minimum to m.in. nazwa lokalizacji, miejscowość i współrzędne.",
    "Dodaje plik albo link jako zasób; portal waliduje go zwykłym potokiem."],
  ["Kontrola każdego zasobu", "Zbiór bez standard = AED nie trafia do wykazu, nawet gdy ma te same kolumny."]);

{
  const s = dowod("Portal co noc scala zasoby w jeden wykaz", "03_komenda_wykaz_statystyki.png", [1440, 900], 0,
    "Terminal: komenda create_main_aed_resource, dwa zasoby przyjęte, dwa pominięte z powodem, 32 wiersze",
    "Zrzut 03: komenda budująca wykaz (pełny log: demo/wynik/komenda_create_main_aed_resource.txt).",
    [["Krosno: ", "pominięte, brak kolumny miejscowosc"], ["Marki: ", "pominięte, brak kolumn minimum"],
      ["Legionowo i wzorzec: ", "przyjęte"]], null, false);
  liczba(s, 8.75, 3.85, 1.9, "2 + 2", "zasoby przyjęte i pominięte z powodem");
  liczba(s, 10.85, 3.85, 1.9, "32", "wiersze w wykazie", K.zielen);
  tx(s, "Nowy wykaz zastępuje poprzedni zasób zbiorczy, tak jak w DGA. Przy każdym pominiętym zasobie log podaje powód.",
    { x: 8.75, y: 5.4, w: 4.0, h: 1.1, fontSize: 13 });
}

dowod("Odbiorca: przegląda wykaz jak każdy zasób portalu", "04_wykaz_tabela.png", [1440, 2071], 900,
  "Frontend portalu: zasób Wykaz defibrylatorów AED, zakładka Tabela z kolumnami wzorca",
  "Zrzut 04: frontend portalu, zasób „Wykaz defibrylatorów AED”, zakładka Tabela.",
  ["Wyszukuje „Wykaz defibrylatorów AED”.", "W zakładce Tabela filtruje i sortuje 51 kolumn.", "Pobiera CSV albo JSON-LD."],
  ["Pochodzenie każdego wiersza", "Wydawca, licencja, zasób źródłowy i data agregacji: atrybucja wymagana przez CC BY 4.0."]);

dowod("Mapa włącza się sama, bez nowego frontendu", "05_wykaz_mapa.png", [1440, 900], 0,
  "Frontend portalu: zakładka Mapa z punktami AED w Bydgoszczy i klastrem 24 punktów z Legionowa",
  "Zrzut 05: zakładka Mapa zasobu zbiorczego.",
  ["Otwiera zakładkę Mapa.", "Widzi 24 punkty z Legionowa i 8 z przykładu wzorca w Bydgoszczy.", "Klika punkt, żeby zobaczyć rekord."],
  ["Jak to działa", "Schemat zasobu zbiorczego ma pole geo (szerokość, długość, etykieta), więc portal sam włącza swój widok mapy."]);

{
  const s = slajd();
  s.addText("Dane wykazu w API, z atrybucją dostawcy", { placeholder: "title" });
  const w = 5.85;
  const h1 = zrzut(s, "06_api_aed_aggregated.png", [1440, 900], M, 1.5, w, 0,
    "Odpowiedź GET /1.4/aed-aggregated z identyfikatorami zbioru i zasobu zbiorczego");
  zrzut(s, "07_api_dane_zasobu.png", [1440, 1497], M + w + 0.4, 1.5, w, 900,
    "Odpowiedź GET /1.4/resources/40247/data: 32 rekordy z kolumnami pochodzenia");
  podpis(s, "Zrzut 06: GET /1.4/aed-aggregated, stały adres wykazu (odpowiednik /dga-aggregated).", M, 1.5 + h1 + 0.12, w);
  podpis(s, "Zrzut 07: GET /1.4/resources/40247/data, meta.count = 32 i kolumny pochodzenia.", M + w + 0.4, 1.5 + h1 + 0.12, w);
  tx(s, [
    { text: "Formaty odczytywalne maszynowo: ", options: { bold: true } },
    { text: "CSV (RFC 4180, UTF-8), JSON-LD i JSON:API portalu; schematy Table Schema, CSVW, kontekst JSON-LD i metadane DCAT-AP." },
  ], { x: M, y: 5.95, w: 12.1, h: 0.8, fontSize: 15 });
}

{
  const s = dowod("Jakość: 192 testy przechodzą, migracji brak", "09_testy.png", [1440, 900], 0,
    "Wynik pytest w kontenerze: 192 passed oraz makemigrations --check: No changes detected",
    "Zrzut 09: testy w kontenerze portalu (pełny log: demo/wynik/testy.txt).",
    [["Testy AED: ", "logika ramek danych bez bazy oraz ORM i Celery na wzór testów DGA."],
      ["Regresja DGA: ", "istniejące testy przechodzą bez zmian."],
      ["Zero migracji: ", "makemigrations --check zwraca „No changes detected”."]], null, false);
  liczba(s, 8.75, 4.6, 4.0, "192 passed", "testy AED i regresja DGA, 22.11.2026");
}

// 11. Wzorcowy zakres danych
{
  const s = slajd();
  s.addText("Wzorcowy zakres danych: jeden format dla wszystkich", { placeholder: "title" });
  liczba(s, M, 1.5, 2.8, "41", "kolumn wzorca dostawcy, każda z typem i wymagalnością (W/Z/O)");
  liczba(s, M + 3.1, 1.5, 2.8, "51", "kolumn wykazu: wzorzec plus pochodzenie i przetworzenie rekordu");
  liczba(s, M + 6.2, 1.5, 2.8, "5", "arkuszy XLSX: zakres, szablon, słowniki, wykaz, zasady");
  liczba(s, M + 9.3, 1.5, 2.8, "4", "schematy maszynowe: Table Schema, CSVW, JSON-LD, DCAT-AP");
  const z = [
    ["Licencje", "Do wykazu trafiają tylko zasoby na CC0 1.0 i CC BY 4.0, z atrybucją. Dane z OpenStreetMap (ODbL) są pomijane."],
    ["Dane osobowe", "Gdy zbiór deklaruje dane osobowe, telefon i e-mail są usuwane, a rekord dostaje kod kontakt_usuniety."],
    ["Uczciwość danych", "Puste pole statusu oznacza „nieznany”, a nie „sprawny”. Data importu nie jest datą weryfikacji."],
  ];
  z.forEach(([t, d], i) => karta(s, M + i * 4.1, 3.6, 3.85, 2.3, t, d, { size: 14 }));
  podpis(s, "Plik: format_danych/wzorcowy_zakres_danych.xlsx; uzasadnienie: docs/06_DECYZJE_STRUKTURA_DANYCH_AED.md.", M, 6.2, 12);
}

// 12. Akcja promocyjna
{
  const s = slajd("CIEMNY");
  s.addText("Dane (prze)życie: akcja, która zachęca dysponentów", { placeholder: "title" });
  s.addImage({ path: P("branding", "logo", "dane-przezycie_logo_pionowe_negatyw.png"), x: M, y: 1.45, w: 3.6,
    h: hPNG(P("branding", "logo", "dane-przezycie_logo_pionowe_negatyw.png"), 3.6),
    altText: "Logo akcji w układzie pionowym na granatowym tle z hasłem Twoje dane – czyjeś życie" });
  tx(s, [
    { text: "Hasło: ", options: { bold: true, color: K.zolc } },
    { text: "Twoje dane – czyjeś życie.", options: { breakLine: true } },
    { text: " ", options: { breakLine: true, fontSize: 8 } },
    { text: "Czerwona linia migotania komór i zielony rytm serca spotykają się w środku folderu z danymi. Chaos zamienia się w porządek dwa razy: w sercu po defibrylacji i w danych po publikacji według jednego wzorca. Nawias w nazwie daje dwa odczytania: „dane przeżycie” i „dane życie”." },
  ], { x: 4.7, y: 1.5, w: 8.0, h: 2.2, fontSize: 16, color: K.bialy });
  const mat = [
    ["materialy", "dane-przezycie_naklejka_A6.png", "Naklejka A6 na szafkę AED"],
    ["materialy", "dane-przezycie_odznaka_dysponenta.png", "Odznaka dysponenta"],
    ["materialy", "dane-przezycie_post_1080.png", "Post do mediów społecznościowych"],
  ];
  let x = 4.7;
  mat.forEach(([d, f, alt]) => {
    const h = 2.3, w = (h * h) / hPNG(P("branding", d, f), h);
    s.addImage({ path: P("branding", d, f), x, y: 3.95, w, h, altText: alt });
    tx(s, alt, { x, y: 6.3, w, h: 0.3, fontSize: 11, color: K.mieta });
    x += w + 0.3;
  });
  tx(s, "Księga znaku: branding/ksiega_znaku.pdf · logotyp w JPG, PNG, PDF i SVG: branding/logo/",
    { x: M, y: 6.85, w: 10, h: 0.35, fontSize: 11, color: K.mieta });
}

// 13. Ograniczenia
{
  const s = slajd();
  s.addText("Ograniczenia", { placeholder: "title" });
  const o = [
    ["Realne źródła", "Większość zasobów AED w portalu nie ma dziś kolumn wzorca. Wykaz je pomija z powodem; z realnych danych przyjęto Legionowo (24 punkty)."],
    ["Brak deduplikacji", "Ten sam AED zgłoszony przez dwóch dostawców da dwa wiersze, każdy z własnym pochodzeniem."],
    ["Warszawa i Gdańsk", "Warszawa: w portalu tylko strona WWW, dane w API z tokenem. Gdańsk: dane flotowe, nie punkty."],
    ["Typy zgadywane przez portal", "Walidacja portalu może oznaczyć błędem plik zgodny ze wzorcem (np. „5A” w numerze budynku); wykaz czyta go wprost."],
    ["Integrator i frontend", "Integrator dla dostawców bez wzorca to zalążek (krok 2). Osobnej strony „Wykaz AED” we froncie nie ma."],
    ["Akcja promocyjna", "Projekt znaku i materiałów; kolizje nazwy (UPRP, EUIPO, domeny) nie zostały sprawdzone."],
  ];
  const cw = 3.85, ch = 2.15;
  o.forEach(([t, d], i) => karta(s, M + (i % 3) * (cw + 0.3), 1.5 + Math.floor(i / 3) * (ch + 0.3), cw, ch, t, d, { size: 13 }));
}

// 14. Jak sprawdzić i użycie AI
{
  const s = slajd("CIEMNY");
  s.addText("Jak to sprawdzić bez stawiania środowiska", { placeholder: "title" });
  const kroki = [
    ["INSTRUKCJA_DLA_JURY.md", "każde wymaganie zadania w ponumerowanym kroku"],
    ["demo/index.html", "klikalny prototyp całego procesu, działa offline"],
    ["ZMIANY_W_PORTALU.md", "lista zmian w kodzie portalu i diff względem oryginału"],
    ["branding/ksiega_znaku.pdf", "księga znaku akcji Dane (prze)życie"],
  ];
  kroki.forEach(([f, d], i) => karta(s, M + (i % 2) * 6.2, 1.5 + Math.floor(i / 2) * 1.3, 5.9, 1.1, f, d,
    { tlo: "1C3D61", kolorTytulu: K.zolc, kolor: K.bialy }));
  tx(s, [
    { text: "Użycie AI. ", options: { bold: true, color: K.zolc } },
    { text: "Asystentów AI (Claude, Cursor) używaliśmy do analizy kodu portalu, pisania kodu i testów według naszego planu, redakcji dokumentów, automatyzacji zrzutów oraz generowania plików znaku i prezentacji ze skryptów. Kierunek rozwiązania, decyzje o danych, licencjach i ochronie danych oraz wybór znaku należą do zespołu; każdą zmianę sprawdziliśmy testami i w uruchomionym portalu." },
  ], { x: M, y: 4.3, w: 12.1, h: 1.6, fontSize: 15, color: K.bialy });
  s.addImage({ path: P("branding", "logo", "dane-przezycie_logo_poziome_negatyw.png"), x: M - 0.1, y: 6.0, w: 3.6,
    h: hPNG(P("branding", "logo", "dane-przezycie_logo_poziome_negatyw.png"), 3.6),
    altText: "Logo akcji Dane (prze)życie" });
}

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
  .then((buf) => { fs.writeFileSync(OUT, buf); console.log("OK:", OUT); });
