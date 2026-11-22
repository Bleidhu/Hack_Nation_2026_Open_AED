// Prezentacja „Dane (prze)życie: Wykaz AED w portalu dane.gov.pl” (PPTX).
//   npm install pptxgenjs@3.12.0 jszip   (w dowolnym katalogu; potem NODE_PATH=<ten katalog>/node_modules)
//   node prezentacja/build_prezentacja.js
// PDF: eksport z PowerPointa (prezentacja/eksport_pdf.ps1). Krój Atkinson Hyperlegible (branding/fonty/) musi być zainstalowany.
// Liczby na slajdach pochodzą z demo/wynik/ (testy.txt, statystyki_agregacji.json) i demo/zrzuty/README.md.
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..");
const P = (...p) => path.join(ROOT, ...p);
// wysokość obrazu PNG dla zadanej szerokości (wymiary z nagłówka IHDR)
const hPNG = (plik, w) => { const b = fs.readFileSync(plik); return (w * b.readUInt32BE(20)) / b.readUInt32BE(16); };
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
const podpis = (slide, text, x, y, w, kolor = K.szary) => tx(slide, text, { x, y, w, h: 0.5, fontSize: 12, color: kolor });

const slajd = (master = "TRESC") => pres.addSlide({ masterName: master });

// 1. Tytuł
{
  const s = slajd("TYTULOWY");
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

// 2. Problem: tabela w liniach, bez kart
{
  const s = slajd();
  s.addText("Sześć miast publikuje AED na sześć sposobów", { placeholder: "title" });
  const zr = [
    ["Krosno", "plik CSV w portalu, bez kolumny z miejscowością"],
    ["Przemyśl", "link do systemu miasta, 5 dystrybucji tych samych danych"],
    ["Marki", "CSV i XLSX wadliwe: cały wiersz w jednym polu"],
    ["Legionowo", "zasób AED w zbiorze mieszanym „Zdrowie”"],
    ["Warszawa", "w portalu tylko strona WWW, dane w API miasta z tokenem"],
    ["Gdańsk", "AED w 278 pojazdach ZTM, w pliku JSON floty"],
  ];
  let y = 1.55;
  zr.forEach(([m, d]) => {
    linia(s, M, y, 8.2);
    tx(s, m, { x: M, y: y + 0.12, w: 1.9, h: 0.4, fontSize: 18, bold: true });
    tx(s, d, { x: M + 2.0, y: y + 0.14, w: 6.2, h: 0.4, fontSize: 16 });
    y += 0.68;
  });
  linia(s, M, y, 8.2);
  tx(s, [{ text: "Z portalu nie da się dowiedzieć, gdzie jest najbliższy defibrylator.", options: { bold: true, breakLine: true } },
    { text: "Nie ma jednej listy AED. Wyszukiwarka nie przeszukuje zawartości tabel, a każdy zbiór ma inne kolumny, formaty i jakość." }],
  { x: 9.5, y: 1.55, w: 3.2, h: 4.3, fontSize: 18, paraSpaceAfter: 14 });
  podpis(s, "Źródło: przegląd API dane.gov.pl z 21.11.2026; kopie zasobów w references/dane_gov_pl_aed/.", M, 6.55, 11);
}

// 3. Rozwiązanie: cztery kroki w jednej linii, bez kart
{
  const s = slajd();
  s.addText("Wykaz AED to mechanizm DGA przerobiony na defibrylatory", { placeholder: "title" });
  const kroki = [
    ["Oznaczenie zbioru", "Dostawca wpisuje w „Polach niestandardowych”: standard = AED."],
    ["Publikacja zasobu", "Plik według wzorca, zwykła walidacja portalu."],
    ["Nocne scalanie", "Zadanie Celery o 4:15 sprawdza kolumny, licencje i dane osobowe."],
    ["Wykaz AED", "Jeden zasób zbiorczy z tabelą, mapą i API."],
  ];
  const kw = 2.75, g = 0.37;
  kroki.forEach(([t, d], i) => {
    const x = M + i * (kw + g);
    const ost = i === 3;
    linia(s, x, 1.65, kw, ost ? K.zielen : K.granat, ost ? 4 : 1.5);
    tx(s, String(i + 1), { x, y: 1.8, w: 0.8, h: 0.8, fontSize: 40, bold: true, color: ost ? K.zielen : K.szary });
    tx(s, t, { x, y: 2.75, w: kw, h: 0.45, fontSize: 20, bold: true, color: ost ? K.zielen : K.granat });
    tx(s, d, { x, y: 3.25, w: kw, h: 1.2, fontSize: 15 });
  });
  tx(s, zLead([
    ["Bez migracji. ", "Żadnych nowych pól ani tabel; oznaczenie siedzi w istniejącej metadanej zbioru."],
    ["22 nowe pliki obok DGA i 11 istniejących z dopiskami. ", "Nic nie usunięto."],
    ["Jeden wyłącznik, AED_AGGREGATION_ENABLED. ", "Po wyłączeniu portal działa jak oryginał."],
  ], K.granat), { x: M, y: 4.55, w: 10.5, h: 1.6, fontSize: 17, paraSpaceAfter: 8 });
  podpis(s, "Szczegóły: ZMIANY_W_PORTALU.md. Diff względem oryginału: git diff a1adc22 -- portal/backend", M, 6.6, 11);
  s.addNotes("Kierunek: zmieniać kod portalu, słowo kluczowe zasób, przerobić DGA, bez migracji, scalać wykazy w jedną listę.");
}

// 4. Dostawca, krok 1: tytuł w lewej kolumnie, zrzut po prawej na całą wysokość
{
  const s = slajd("KOLUMNA");
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

// 5. Dostawca, krok 2: zrzut po lewej, tekst po prawej
{
  const s = slajd();
  s.addText("Dostawca publikuje zasób według wzorca", { placeholder: "title" });
  const h = zrzut(s, "02_zasoby_dostawcow.png", [1440, 1234], M, 1.55, 7.3, 880,
    "Lista zasobów w panelu: pięć zasobów dostawców i zasób zbiorczy Wykaz defibrylatorów AED");
  podpis(s, "Zrzut 02: lista zasobów w panelu, pięć zasobów dostawców i zasób zbiorczy.", M, 1.55 + h + 0.1, 7.3);
  tx(s, [
    { text: "Dostawca pobiera szablon XLSX lub CSV wzorcowego zakresu, wypełnia kolumny (minimum to m.in. nazwa lokalizacji, miejscowość i współrzędne) i dodaje plik albo link jako zasób.", options: { breakLine: true } },
    { text: "Portal waliduje go zwykłym potokiem zasobów.", options: { breakLine: true } },
    { text: "Zbiór bez wpisu standard = AED nie trafia do wykazu, nawet gdy ma te same kolumny.", options: { bold: true } },
  ], { x: 8.45, y: 1.55, w: 4.2, h: 4.6, fontSize: 16, paraSpaceAfter: 14 });
}

// 6. Nocne scalanie: ciemny slajd, jedna duża liczba
{
  const s = slajd("CIEMNY");
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
  tx(s, "Nowy wykaz zastępuje poprzedni zasób zbiorczy, tak jak w DGA.", { x: 8.85, y: 5.65, w: 3.8, h: 0.8, fontSize: 15, color: K.granatJ });
}

// 7. Odbiorca, tabela: zrzut na całą szerokość, pod nim trzy zdania w kolumnach
{
  const s = slajd();
  s.addText("Odbiorca przegląda wykaz jak każdy zasób portalu", { placeholder: "title" });
  const w = W - 2 * M;
  const h = zrzut(s, "04_wykaz_tabela.png", [1440, 2071], M, 1.4, w, 470,
    "Frontend portalu: zasób Wykaz defibrylatorów AED, zakładka Tabela z kolumnami wzorca");
  const y = 1.4 + h + 0.2;
  const kol = [
    ["Wyszukiwanie. ", "Wpisuje „Wykaz defibrylatorów AED”, otwiera zasób, wybiera zakładkę Tabela."],
    ["Praca z tabelą. ", "Filtruje i sortuje 51 kolumn, pobiera CSV albo JSON-LD."],
    ["Pochodzenie. ", "Każdy wiersz ma wydawcę, licencję, zasób źródłowy i datę agregacji, jak wymaga CC BY 4.0."],
  ];
  kol.forEach(([a, b], i) => tx(s, zLead([[a, b]], K.zielen), { x: M + i * 4.1, y, w: 3.8, h: 1.6, fontSize: 15 }));
  podpis(s, "Zrzut 04: frontend portalu, zasób „Wykaz defibrylatorów AED”, zakładka Tabela.", M, 6.5, 11);
}

// 8. Mapa: zrzut po lewej, tytuł i tekst po prawej
{
  const s = slajd("TRESC");
  const h = zrzut(s, "05_wykaz_mapa.png", [1440, 900], M, 0.7, 7.7, 0,
    "Frontend portalu: zakładka Mapa z punktami AED w Bydgoszczy i klastrem 24 punktów z Legionowa");
  podpis(s, "Zrzut 05: zakładka Mapa zasobu zbiorczego.", M, 0.7 + h + 0.1, 7.7);
  s.addText("Mapa włącza się sama, bez nowego frontendu", { x: 8.9, y: 0.7, w: 3.75, h: 1.6, fontSize: 28, bold: true,
    color: K.granat, fontFace: FONT, margin: 0, valign: "top" });
  tx(s, akapity([
    "Schemat zasobu zbiorczego ma pole geo (szerokość, długość, etykieta), więc portal sam pokazuje swój widok mapy.",
    "Na mapie jest 24 punkty z Legionowa i 8 z przykładu wzorca w Bydgoszczy. Kliknięcie punktu otwiera rekord.",
  ]), { x: 8.9, y: 2.5, w: 3.75, h: 3.4, fontSize: 16, paraSpaceAfter: 12 });
}

// 9. API: dwa zrzuty obok siebie
{
  const s = slajd();
  s.addText("Dane wykazu są w API razem z atrybucją dostawcy", { placeholder: "title" });
  const w = 5.85;
  const h1 = zrzut(s, "06_api_aed_aggregated.png", [1440, 900], M, 1.5, w, 0,
    "Odpowiedź GET /1.4/aed-aggregated z identyfikatorami zbioru i zasobu zbiorczego");
  zrzut(s, "07_api_dane_zasobu.png", [1440, 1497], M + w + 0.4, 1.5, w, 900,
    "Odpowiedź GET /1.4/resources/40247/data: 32 rekordy z kolumnami pochodzenia");
  podpis(s, "Zrzut 06: GET /1.4/aed-aggregated, stały adres wykazu (odpowiednik /dga-aggregated).", M, 1.5 + h1 + 0.1, w);
  podpis(s, "Zrzut 07: GET /1.4/resources/40247/data, meta.count = 32 i kolumny pochodzenia.", M + w + 0.4, 1.5 + h1 + 0.1, w);
  tx(s, zLead([["Formaty maszynowe: ", "CSV (RFC 4180, UTF-8), JSON-LD i JSON:API portalu oraz schematy Table Schema, CSVW, kontekst JSON-LD i metadane DCAT-AP."]], K.zielen),
    { x: M, y: 6.0, w: 12, h: 0.7, fontSize: 15 });
}

// 10. Testy: jedna duża liczba, zrzut mniejszy
{
  const s = slajd();
  s.addText("Testy przechodzą, migracji brak", { placeholder: "title" });
  tx(s, "192", { x: M, y: 1.45, w: 4.5, h: 1.6, fontSize: 110, bold: true, color: K.zielen });
  tx(s, "testów przeszło 22.11.2026: testy AED i regresja DGA, w kontenerze portalu.", { x: M, y: 3.2, w: 4.5, h: 0.9, fontSize: 17 });
  tx(s, zLead([
    ["Testy AED: ", "logika ramek danych bez bazy oraz ORM i Celery na wzór testów DGA."],
    ["Regresja DGA: ", "istniejące testy przechodzą bez zmian."],
    ["Zero migracji: ", "makemigrations --check zwraca „No changes detected”."],
  ], K.granat), { x: M, y: 4.35, w: 4.6, h: 2.0, fontSize: 15, paraSpaceAfter: 8 });
  const h = zrzut(s, "09_testy.png", [1440, 900], 5.7, 1.5, 6.95, 0,
    "Wynik pytest w kontenerze: 192 passed oraz makemigrations --check: No changes detected");
  podpis(s, "Zrzut 09: testy w kontenerze portalu. Pełny log: demo/wynik/testy.txt", 5.7, 1.5 + h + 0.1, 6.95);
}

// 11. Wzorcowy zakres: liczby jako tabela w liniach, zasady obok
{
  const s = slajd();
  s.addText("Wzorcowy zakres danych: jeden format dla wszystkich", { placeholder: "title" });
  const lic = [
    ["41", "kolumn wzorca dostawcy, każda z typem i wymagalnością (W/Z/O)"],
    ["51", "kolumn wykazu: wzorzec plus pochodzenie i przetworzenie rekordu"],
    ["5", "arkuszy XLSX: zakres, szablon, słowniki, wykaz, zasady"],
    ["4", "schematy maszynowe: Table Schema, CSVW, JSON-LD, DCAT-AP"],
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
    ["Brak wiedzy to nie „sprawny”. ", "Puste pole statusu oznacza „nieznany”. Data importu nie jest datą weryfikacji."],
  ], K.granat), { x: 7.2, y: 1.55, w: 5.45, h: 4.6, fontSize: 17, paraSpaceAfter: 16 });
  podpis(s, "Plik: format_danych/wzorcowy_zakres_danych.xlsx. Reguły: arkusz 5_Zasady i schemat Table Schema", M, 6.55, 12);
}

// 12. Akcja promocyjna
{
  const s = slajd("CIEMNY");
  s.addText("Dane (prze)życie: akcja dla dysponentów danych", { placeholder: "title" });
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

// 13. Ograniczenia: dwie kolumny tekstu, bez kart
{
  const s = slajd();
  s.addText("Czego wykaz jeszcze nie robi", { placeholder: "title" });
  const o = [
    ["Realne źródła. ", "Większość zasobów AED w portalu nie ma dziś kolumn wzorca. Wykaz je pomija z powodem; z realnych danych przyjęto Legionowo (24 punkty)."],
    ["Brak deduplikacji. ", "Ten sam AED zgłoszony przez dwóch dostawców da dwa wiersze, każdy z własnym pochodzeniem."],
    ["Warszawa i Gdańsk. ", "Warszawa: w portalu tylko strona WWW, dane w API z tokenem. Gdańsk: dane flotowe, nie punkty."],
    ["Typy zgadywane przez portal. ", "Walidacja portalu może oznaczyć błędem plik zgodny ze wzorcem (np. „5A” w numerze budynku); wykaz czyta go wprost."],
    ["Integrator (dodatek). ", "Pomaga dostawcom bez wzorca (Warszawa, Gdańsk, OSM), ale jest poza portalem: portal może działać bez niego. Osobnej strony „Wykaz AED” we froncie nie ma."],
    ["Akcja promocyjna. ", "To projekt znaku i materiałów. Kolizji nazwy (UPRP, EUIPO, domeny) nie sprawdzaliśmy."],
  ];
  [0, 1].forEach((k) => {
    tx(s, zLead(o.slice(k * 3, k * 3 + 3), K.czerwien), { x: M + k * 6.2, y: 1.6, w: 5.8, h: 4.8, fontSize: 16, paraSpaceAfter: 18 });
  });
}

// 13a. Dodatek: integrator (osobna aplikacja, poza portalem)
{
  const s = slajd();
  s.addText("Dodatek: integrator dla dostawców bez wzorcowego formatu", { placeholder: "title" });
  tx(s, [
    { text: "Dwie największe instytucje na dane.gov.pl nie publikują dziś tabeli AED. Integrator (osobna aplikacja, zero zmian w portalu) przepisuje ich pliki na wzorzec v2, a dostawca podłącza wynik zwykłym zasobem typu „link”.", options: { breakLine: true } },
  ], { x: M, y: 1.5, w: 12, h: 1.0, fontSize: 16, color: K.szary });
  const w = [
    ["Warszawa", "API z tokenem → czytamy przykład odpowiedzi z dokumentacji", "1 wiersz zgodny z v2, licencja CC BY 4.0 jawnie w pochodzeniu"],
    ["Gdańsk", "baza 503 pojazdów ZTM, 278 z AED", "0 wierszy punktowych + jednoznaczny powód: dane flotowe, a wzorzec opisuje punkty"],
    ["Duplikaty i OSM", "pary kandydatów tylko flagowane (bez scalania); OSM tylko lokalnie z oznaczeniem ODbL", "raporty: w obu / tylko w wykazie / tylko w OSM"],
    ["Lokalne UI i testy", "python integrator/ui/serwer.py → http://127.0.0.1:8765 (offline, nic nie zapisuje na dysku)", "87 testów bez Dockera; demo/integrator/ generuje jedno polecenie"],
  ];
  let y = 2.6;
  w.forEach(([t, d1, d2]) => {
    linia(s, M, y, 12);
    tx(s, t, { x: M, y: y + 0.12, w: 2.4, h: 1.0, fontSize: 16, bold: true, color: K.zielen });
    tx(s, d1, { x: M + 2.6, y: y + 0.12, w: 4.6, h: 1.0, fontSize: 15 });
    tx(s, d2, { x: M + 7.4, y: y + 0.12, w: 4.6, h: 1.0, fontSize: 15, color: K.szary });
    y += 1.05;
  });
  tx(s, "Wykaz AED w portalu działa bez integratora. Dowody: demo/integrator/ (jedno polecenie: python integrator/generuj_demo.py) i integrator/README.md; instrukcja dla jury, krok 14.",
    { x: M, y: 6.75, w: 12, h: 0.5, fontSize: 12, color: K.szary });
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
  let y = 1.5;
  kroki.forEach(([f, d]) => {
    linia(s, M, y, 12, K.szary);
    tx(s, f, { x: M, y: y + 0.13, w: 4.6, h: 0.4, fontSize: 16, bold: true, color: K.zolc, fontFace: MONO });
    tx(s, d, { x: M + 4.8, y: y + 0.13, w: 7.2, h: 0.4, fontSize: 16, color: K.bialy });
    y += 0.62;
  });
  linia(s, M, y, 12, K.szary);
  tx(s, zLead([["Użycie AI. ", "Asystentów AI (Claude, Cursor) używaliśmy do wsparcia analizy kodu portalu, pisania kodu i implementacji testów oraz do wsparcia tworzenia księgi znaku i plików znaku, a także przy redakcji dokumentów, zrzutach ekranu i składaniu prezentacji. Kierunek rozwiązania, decyzje o danych, licencjach i ochronie danych oraz wybór znaku należą do zespołu. Każdą zmianę sprawdziliśmy testami i w uruchomionym portalu."]], K.zolc),
    { x: M, y: 4.4, w: 11.2, h: 1.7, fontSize: 15, color: K.bialy });
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
