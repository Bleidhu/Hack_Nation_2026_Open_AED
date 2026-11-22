# Film: Wykaz AED w portalu dane.gov.pl

[`dane_przezycie_wykaz_aed.mp4`](dane_przezycie_wykaz_aed.mp4): 1 min 14 s, 1920×1080, 60 kl./s, H.264, bez dźwięku, napisy po polsku. Otworzysz go w każdej przeglądarce i każdym odtwarzaczu.

Film pokazuje realizację zadania na nagraniach działającego portalu. Przejścia przez prototyp offline w filmie nie ma; prototyp opisuje [`../../INSTRUKCJA_DLA_JURY.md`](../../INSTRUKCJA_DLA_JURY.md).

| Czas | Część | Co widać |
|---|---|---|
| 0:00 | otwarcie | Wykaz AED, akcja „Dane (prze)życie” |
| 0:10 | 1/2 Dostawca | panel portalu: zbiór z `standard = AED` w „Polach niestandardowych”, podpowiedź pod polem, zasoby AED po walidacji |
| 0:39 | 2/2 Odbiorca | front portalu: zasób „Wykaz defibrylatorów AED” (CSV i JSON-LD, tabela, mapa), odpowiedź `GET /1.4/aed-aggregated` |
| 1:06 | zamknięcie | co oddajemy: Wykaz AED, wzorcowy zakres XLSX, logotyp i księga znaku, instrukcja dla jury |

**Uczciwość nagrania:**
- Wszystkie ujęcia to nagrania portalu z naszymi zmianami, uruchomionego lokalnie w Dockerze 22.11.2026. Makiet nie ma.
- Montaż jest jawny:
  - czekanie na wczytanie mapy skrócono, a na ekranie jest napis „Pominięto 1,7 s czekania”;
  - przejście do API wycięto, a w tym miejscu obraz przygasa;
  - część z prototypem offline (karta 03 i przejście przez `demo/index.html`, 35 s) usunięto w całości 22.11.2026; film przechodzi od odpowiedzi API wprost do zamknięcia.
- Kursor jest dorysowany ze zapisu ruchów myszy, a kliknięcia i pisanie były prawdziwe.
- Nagranie niczego nie zapisało w portalu.

Źródła filmu (skrypty nagrań, kompozycja, napisy) i instrukcja odtworzenia: [`../../video/README.md`](../../video/README.md).
