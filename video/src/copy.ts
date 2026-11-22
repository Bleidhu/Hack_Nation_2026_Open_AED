// Wszystkie słowa w wideo w jednym miejscu. Napis = jedna linia, poniżej ok. 60 znaków.
// Każde twierdzenie ma pokrycie w repozytorium: INSTRUKCJA_DLA_JURY.md, ZMIANY_W_PORTALU.md, demo/wynik/.
const seconds = (s: number) => (s < 10 ? s.toFixed(1).replace('.', ',') : String(Math.round(s)));

export const COPY = {
  brand: 'Wykaz AED',
  intro: {
    kicker: 'HackNation 2026 · Misja AED – Dane na ratunek',
    lead: 'Ogólnopolska lista defibrylatorów w portalu dane.gov.pl.',
    sub: 'Zasoby wielu dysponentów scalane co noc w jeden zasób, bez migracji bazy.',
    chips: ['Dostawca', 'Odbiorca', 'Prototyp dla jury'],
  },
  /** Napis po cięciu, które skraca czekanie. Zostaje: dzięki niemu montaż jest jawny. */
  skipped: (s: number) => `Pominięto ${seconds(s)} s czekania`,
  dostawca: {
    tag: '1/3 · Dostawca',
    card: {no: '01', title: 'Dostawca', sub: 'Oznacza zbiór istniejącą metadaną portalu.'},
    window: 'Panel administracyjny dane.gov.pl (nasz fork, lokalnie)',
    zbior: 'Panel dostawcy: zbiór AED Urzędu Miasta Legionowo.',
    standard: 'Pola niestandardowe: standard = AED. Bez migracji.',
    pomoc: 'Pod polem podpowiedź: co wpisać i jakich kolumn użyć.',
    zasoby: 'Zasoby dostawców to zwykłe zasoby portalu.',
    walidacja: 'Każdy przechodzi standardową walidację portalu.',
    wykaz: 'Nocne zadanie na wzór DGA scala je w Wykaz AED.',
  },
  odbiorca: {
    tag: '2/3 · Odbiorca',
    card: {no: '02', title: 'Odbiorca', sub: 'Wykaz AED: tabela, mapa i API portalu.'},
    window: 'Portal dane.gov.pl (nasz fork, lokalnie)',
    zasob: 'Wykaz AED to zwykły zasób portalu dane.gov.pl.',
    pobierz: 'CSV i JSON-LD do pobrania, jak w każdym zasobie.',
    tabela: 'Tabela: 32 punkty od 2 dostawców w jednym układzie.',
    mapa: 'Schemat z polem geo włącza mapę portalu.',
    api: 'Stały adres API /aed-aggregated, jak /dga-aggregated.',
  },
  prototyp: {
    tag: '3/3 · Prototyp',
    card: {no: '03', title: 'Prototyp dla jury', sub: 'Cały proces offline, w jednym pliku HTML.'},
    window: 'Prototyp offline demo/index.html',
    start: 'Prototyp offline dla jury: jeden plik, bez sieci.',
    schemat: 'Portal sprawdza każdy zasób; odrzucone mają powód.',
    filtr: 'Prawdziwy wynik agregacji: filtr Legionowo, 24 punkty.',
    pochodzenie: 'Każdy rekord niesie pochodzenie: wydawca i licencja.',
    zmiany: 'Zmiany w portalu: 22 nowe pliki, 11 dopisków, 0 migracji.',
  },
  outro: {
    title: 'Twoje dane –',
    title2: 'czyjeś życie.',
    rows: [
      ['Wykaz AED w portalu', 'dodatek na wzór DGA: 0 migracji, 192 testy'],
      ['Wzorcowy zakres danych', 'XLSX: 41 kolumn dostawcy, 51 w wykazie'],
      ['Akcja „Dane (prze)życie”', 'logotyp, hasło i księga znaku (PDF)'],
      ['Dla jury', 'INSTRUKCJA_DLA_JURY.md i demo/index.html'],
    ],
    note: 'Nagrania działającego portalu (Docker, lokalnie) i prototypu z repozytorium. Wyniki są prawdziwe; '
      + 'przejścia między ekranami skrócono tylko tam, gdzie obraz przygasa.',
  },
};
