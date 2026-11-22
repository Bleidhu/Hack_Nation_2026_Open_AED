# Film: Wykaz AED w portalu dane.gov.pl

[`dane_przezycie_wykaz_aed.mp4`](dane_przezycie_wykaz_aed.mp4): 1 min 49 s, 1920×1080, 60 kl./s, H.264, bez dźwięku, napisy po polsku. Otworzysz go w każdej przeglądarce i każdym odtwarzaczu.

Film pokazuje realizację zadania na nagraniach z działających stron:

| Czas | Część | Co widać |
|---|---|---|
| 0:00 | otwarcie | Wykaz AED, akcja „Dane (prze)życie” |
| 0:10 | 1/3 Dostawca | panel portalu: zbiór z `standard = AED` w „Polach niestandardowych”, podpowiedź pod polem, zasoby AED po walidacji |
| 0:39 | 2/3 Odbiorca | front portalu: zasób „Wykaz defibrylatorów AED” (CSV i JSON-LD, tabela, mapa), odpowiedź `GET /1.4/aed-aggregated` |
| 1:09 | 3/3 Prototyp | [`../index.html`](../index.html) otwarty z dysku: budowa wykazu, filtr Legionowo, pochodzenie rekordu, zmiany w portalu |
| 1:40 | zamknięcie | co oddajemy: Wykaz AED, wzorcowy zakres XLSX, logotyp i księga znaku, instrukcja dla jury |

**Uczciwość nagrania:**
- Wszystkie ujęcia to nagrania portalu z naszymi zmianami, uruchomionego lokalnie w Dockerze 22.11.2026, oraz prototypu z repozytorium. Makiet nie ma.
- Montaż jest jawny:
  - czekanie na wczytanie mapy skrócono, a na ekranie jest napis „Pominięto 1,7 s czekania”;
  - przejście do API i przewinięcie prototypu w górę wycięto, a w tych miejscach obraz przygasa.
- Kursor jest dorysowany ze zapisu ruchów myszy, a kliknięcia i pisanie były prawdziwe.
- Nagranie niczego nie zapisało w portalu.

Źródła filmu (skrypty nagrań, kompozycja, napisy) i instrukcja odtworzenia: [`../../video/README.md`](../../video/README.md).
