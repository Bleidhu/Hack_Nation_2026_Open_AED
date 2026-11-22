"""
Deduplikacja wierszy Wykazu AED: to samo urządzenie zgłoszone przez dwóch dostawców (albo dwa razy w jednym pliku)
ma trafić do wykazu raz.

Moduł nie importuje Django ani ORM: przyjmuje i zwraca `DataFrame` (kolumny zasobu zbiorczego), więc działa też
w `demo/sprawdz.py`. Reguły (kolejność ma znaczenie):

1. **Klucz mocny: numer seryjny.** Ten sam znormalizowany numer seryjny oznacza to samo urządzenie, chyba że oba wiersze
   podają producenta i producenci się różnią (numery seryjne różnych firm mogą się powtarzać).
2. **Klucz słaby, tylko między różnymi zasobami:** punkty w odległości do 30 m, bez sprzeczności
   (różne numery seryjne, różni producenci, różne modele albo różne kondygnacje oznaczają różne urządzenia) i z zgodnością:
   - ten sam producent albo ten sam model (marka), albo
   - gdy brakuje marki: odległość do 10 m i ta sama znormalizowana nazwa lokalizacji.
   W obrębie jednego pliku dwa AED w jednym miejscu bez numerów seryjnych to dwa urządzenia, więc nie są łączone.
3. **Który wiersz zostaje:** wyższy poziom weryfikacji, potem nowsza `data_aktualizacji`, potem wcześniejszy w kolejności.
   Puste `producent`, `model` i `numer_seryjny` zachowanego wiersza uzupełniamy z duplikatów.

Wynik zawiera listę par (`zachowany`, `pominiety`, `powod`), którą portal zapisuje w statystykach i logu.
"""

import math
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

SERIAL_PLACEHOLDERS = {"brak", "nieznany", "nieznane", "nd", "na", "none", "null", "unknown", "bd"}
MIN_SERIAL_LENGTH = 4
WEAK_DISTANCE_M = 30.0
NAME_DISTANCE_M = 10.0
VERIFICATION_RANK = {"zweryfikowany_w_terenie": 2, "zweryfikowany_przez_dysponenta": 1}
FILL_COLUMNS = ("producent", "model", "numer_seryjny")
REASON_SERIAL = "numer_seryjny"
REASON_BRAND = "marka_model_i_lokalizacja"
REASON_NAME = "nazwa_i_lokalizacja"


def _plain(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value if value is not None else "").replace("ł", "l").replace("Ł", "L"))
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in text if not unicodedata.combining(c)).lower())


def normalize_serial(value: Any) -> str:
    """Znormalizowany numer seryjny albo pusty tekst, gdy to brak danych (np. „brak”, „-”, za krótki)."""
    serial = _plain(value)
    if serial in SERIAL_PLACEHOLDERS or len(serial) < MIN_SERIAL_LENGTH or len(set(serial)) == 1:
        return ""
    return serial


def _float(value: Any) -> Optional[float]:
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 12742000.0 * math.asin(math.sqrt(a))


class _Row:
    def __init__(self, index: int, record: Dict[str, Any]):
        self.index = index
        self.record = record
        self.serial = normalize_serial(record.get("numer_seryjny"))
        self.brand = _plain(record.get("producent"))
        self.model = _plain(record.get("model"))
        self.name = _plain(record.get("nazwa_lokalizacji"))
        self.floor = str(record.get("kondygnacja") or "").strip()
        self.resource = str(record.get("id_zasobu_zrodlowego") or "")
        self.lat = _float(record.get("szerokosc_geograficzna"))
        self.lon = _float(record.get("dlugosc_geograficzna"))
        self.rank = VERIFICATION_RANK.get(str(record.get("poziom_weryfikacji") or ""), 0)
        self.updated = str(record.get("data_aktualizacji") or "")

    @property
    def best_key(self) -> Tuple[int, str, int]:
        return self.rank, self.updated, -self.index


def _conflict(a: str, b: str) -> bool:
    return bool(a) and bool(b) and a != b


def _strong_match(a: _Row, b: _Row) -> bool:
    return bool(a.serial) and a.serial == b.serial and not _conflict(a.brand, b.brand)


def _weak_match(a: _Row, b: _Row) -> Optional[str]:
    if a.resource == b.resource or None in (a.lat, a.lon, b.lat, b.lon):
        return None
    if _conflict(a.serial, b.serial) or _conflict(a.brand, b.brand) or _conflict(a.model, b.model) or _conflict(a.floor, b.floor):
        return None
    meters = distance_m(a.lat, a.lon, b.lat, b.lon)
    if meters > WEAK_DISTANCE_M:
        return None
    if (a.brand and a.brand == b.brand) or (a.model and a.model == b.model):
        return REASON_BRAND
    if not (a.brand and b.brand) and meters <= NAME_DISTANCE_M and a.name and a.name == b.name:
        return REASON_NAME
    return None


def _serial_pairs(rows: List[_Row]) -> set:
    by_serial: Dict[str, List[_Row]] = {}
    for row in rows:
        if row.serial:
            by_serial.setdefault(row.serial, []).append(row)
    return {(a.index, b.index) for group in by_serial.values() for i, a in enumerate(group) for b in group[i + 1 :]}


def _grid_pairs(rows: List[_Row]) -> set:
    """Pary z sąsiednich komórek siatki ~100 m, żeby nie porównywać wszystkich ze wszystkimi."""
    grid: Dict[Tuple[int, int], List[_Row]] = {}
    for row in rows:
        if row.lat is not None and row.lon is not None:
            grid.setdefault((int(row.lat * 1000), int(row.lon * 1000)), []).append(row)
    pairs = set()
    for (cx, cy), group in grid.items():
        near = [r for dx in (-1, 0, 1) for dy in (-1, 0, 1) for r in grid.get((cx + dx, cy + dy), [])]
        pairs.update((a.index, b.index) for a in group for b in near if a.index < b.index)
    return pairs


def _candidate_pairs(rows: List[_Row]):
    for i, j in sorted(_serial_pairs(rows) | _grid_pairs(rows)):
        yield rows[i], rows[j]


def _group_rows(rows: List[_Row]) -> Tuple[Dict[int, List[_Row]], Dict[int, Tuple[int, str]]]:
    """Grupy tego samego urządzenia (union-find) i powód połączenia każdego wiersza."""
    parent = list(range(len(rows)))
    edges: Dict[int, Tuple[int, str]] = {}

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in _candidate_pairs(rows):
        reason = REASON_SERIAL if _strong_match(a, b) else _weak_match(a, b)
        if reason and find(a.index) != find(b.index):
            parent[find(b.index)] = find(a.index)
            edges[b.index] = (a.index, reason)
            edges.setdefault(a.index, (b.index, reason))
    groups: Dict[int, List[_Row]] = {}
    for row in rows:
        groups.setdefault(find(row.index), []).append(row)
    return groups, edges


def _fill_values(keeper: _Row, members: List[_Row]) -> Dict[str, Any]:
    fill = {}
    for column in FILL_COLUMNS:
        if not str(keeper.record.get(column) or "").strip():
            donor = next((m.record.get(column) for m in members if str(m.record.get(column) or "").strip()), None)
            if donor:
                fill[column] = donor
    return fill


def deduplicate_rows(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, str]]]:
    """Zwraca ramkę bez duplikatów (kolejność zachowanych wierszy bez zmian) i listę usuniętych duplikatów."""
    if df.empty:
        return df, []
    rows = [_Row(i, rec) for i, rec in enumerate(df.to_dict("records"))]
    groups, edges = _group_rows(rows)
    drop, duplicates = set(), []
    result = df.copy()
    for members in groups.values():
        if len(members) == 1:
            continue
        keeper = max(members, key=lambda r: r.best_key)
        for column, value in _fill_values(keeper, members).items():
            result.iat[keeper.index, result.columns.get_loc(column)] = value
        for member in members:
            if member is not keeper:
                drop.add(member.index)
                reason = edges.get(member.index, (0, REASON_SERIAL))[1]
                duplicates.append(
                    {
                        "zachowany": str(keeper.record.get("id_aed", keeper.index)),
                        "pominiety": str(member.record.get("id_aed", member.index)),
                        "powod": reason,
                    }
                )
    return result.drop(index=result.index[sorted(drop)]).reset_index(drop=True), duplicates
