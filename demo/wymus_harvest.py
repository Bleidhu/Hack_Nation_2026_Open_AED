"""Wymuszenie harvestu AED w lokalnym portalu (demo): zamiast czekać do nocy, ten sam przebieg od razu.

    python demo/wymus_harvest.py https://host.docker.internal:8099/opis.xml --organizacja 2843
    python demo/wymus_harvest.py <adres opisu> [--organizacja ID] [--kontener mcod-admin] [--limit 300] [--zapisz plik.txt]

Kroki (wszystko przez `docker exec` w kontenerze panelu; Python 3.8+, tylko biblioteka standardowa):

1. Import opisu zbioru XML komendą portalu `import_aed_xml`: gdy zbiór z tym opisem już jest w portalu, z `--odswiez`
   (to samo robi nocne zadanie `refresh_aed_opis_task` o 4:05), a gdy go nie ma, z adresem i `--organizacja`.
   Portal pobiera opis, sprawdza XSD, pobiera CSV i porównuje md5; ta sama suma nic nie zmienia, nowa zastępuje zasób.
2. Czekanie (z limitem czasu) na potok portalu w Celery: `link_tasks_last_status` i `file_tasks_last_status` zasobu
   muszą być SUCCESS, a `data_tasks_last_status` zakończony. Wykaz AED nie wymaga SUCCESS walidacji danych
   (typy zgadywane przez portal, np. „5A” w numerze budynku), więc FAILURE jest tylko raportowany.
3. Budowa Wykazu AED komendą `create_main_aed_resource --eager` (to samo zadanie co o 4:15).
4. Raport: wynik importu, statusy zasobu, identyfikatory zbioru i zasobu wykazu, wiersze i duplikaty.

Kod wyjścia: 0 sukces, 1 import odrzucony albo błąd komendy, 2 przekroczony limit czasu albo błąd potoku zasobu.
Adres opisu jest widziany z kontenera (serwer na hoście: https://host.docker.internal:<port>, przez ngrok: adres https).
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

MARKER = "WYNIK_JSON "
NOISE = re.compile(r"(UserWarning: Overriding|^\s+warnings\.warn\(|^\[\w+\] sender:|^NoneType: None| DEBUG )")
STATUS_QUERY = """
import json
from mcod.datasets.models import Dataset
d = Dataset.objects.filter(customfields__contains={{"opis_xml": {url}}}).first()
out = {{"zbior": None}}
if d is not None:
    r = d.resources.order_by("-pk").first()
    out = {{"zbior": d.pk, "md5": (d.customfields or {{}}).get("md5"), "zasob": r.pk if r else None}}
    if r is not None:
        out.update(link=r.link, format=r.format, plik=bool(r.main_file), link_status=r.link_tasks_last_status,
                   file_status=r.file_tasks_last_status, data_status=r.data_tasks_last_status)
print("WYNIK_JSON " + json.dumps(out))
"""


class Portal:
    def __init__(self, container: str, log):
        self.container = container
        self.log = log

    def manage(self, *args: str, timeout: int = 600):
        cmd = ["docker", "exec", self.container, "python", "manage.py", *args]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        text = proc.stdout.decode("utf-8", errors="replace")
        lines = [line for line in text.splitlines() if not NOISE.search(line)]
        return proc.returncode, lines

    def status(self, url: str) -> dict:
        code, lines = self.manage("shell", "-c", STATUS_QUERY.format(url=json.dumps(url)), timeout=120)
        found = [line[len(MARKER):] for line in lines if line.startswith(MARKER)]
        if code != 0 or not found:
            raise RuntimeError("zapytanie o stan zasobu nie powiodło się:\n" + "\n".join(lines[-15:]))
        return json.loads(found[-1])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Wymuszenie harvestu AED: import opisu XML, czekanie na Celery, Wykaz AED.")
    ap.add_argument("url", help="adres https opisu zbioru (XML) widziany z kontenera portalu")
    ap.add_argument("--organizacja", type=int, help="ID instytucji dostawcy (wymagane przy pierwszym imporcie)")
    ap.add_argument("--kontener", default="mcod-admin", help="kontener panelu portalu (domyślnie mcod-admin)")
    ap.add_argument("--limit", type=int, default=300, help="limit czekania na Celery w sekundach (domyślnie 300)")
    ap.add_argument("--interwal", type=float, default=3.0, help="odstęp sprawdzania stanu w sekundach")
    ap.add_argument("--zapisz", type=Path, help="zapisz pełny przebieg (polecenia i wyjście) do pliku")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    transcript = []

    def log(line: str = "") -> None:
        print(line, flush=True)
        transcript.append(line)

    portal = Portal(a.kontener, log)
    started = time.time()
    try:
        return run(a, portal, log, started)
    finally:
        if a.zapisz:
            a.zapisz.parent.mkdir(parents=True, exist_ok=True)
            a.zapisz.write_text("\n".join(transcript) + "\n", encoding="utf-8")


def run(a, portal: Portal, log, started: float) -> int:
    log(f"Wymuszenie harvestu AED: {a.url} (kontener {a.kontener})")
    before = portal.status(a.url)
    if before["zbior"] is not None:
        log(f"1/3 Zbiór {before['zbior']} z tym opisem jest w portalu (md5 {before.get('md5')}): import_aed_xml --odswiez")
        args = ["import_aed_xml", "--odswiez"]
    elif a.organizacja:
        log(f"1/3 Pierwszy import opisu dla instytucji {a.organizacja}: import_aed_xml <adres> --organizacja")
        args = ["import_aed_xml", a.url, "--organizacja", str(a.organizacja)]
    else:
        log("Zbioru z tym opisem nie ma w portalu: podaj --organizacja (ID instytucji dostawcy).")
        return 1
    log("$ docker exec " + a.kontener + " python manage.py " + " ".join(args))
    code, lines = portal.manage(*args)
    for line in lines:
        log("  " + line)
    after = portal.status(a.url)
    mine = [line for line in lines if line.startswith(a.url)]
    if code != 0 or after["zbior"] is None or (mine and ": odrzucono" in mine[-1]):
        log("Import odrzucony albo nieudany: zbiór bez zmian, wykazu nie buduję.")
        return 1
    if after.get("zasob") is None:
        log(f"Zbiór {after['zbior']} nie ma zasobu.")
        return 1

    log(f"2/3 Czekam na Celery dla zasobu {after['zasob']} (limit {a.limit} s)")
    deadline = time.time() + a.limit
    last = None
    while True:
        state = portal.status(a.url)
        current = (state.get("link_status"), state.get("file_status"), state.get("data_status"))
        if current != last:
            log(f"  {time.time() - started:6.1f} s  link={current[0] or '-'} plik={current[1] or '-'} dane={current[2] or '-'}")
            last = current
        if "FAILURE" in current[:2]:
            log("Potok portalu zgłosił błąd linku albo pliku: zasób nie trafi do wykazu.")
            return 2
        if current[0] == "SUCCESS" and current[1] == "SUCCESS" and current[2] in ("SUCCESS", "FAILURE"):
            break
        if time.time() > deadline:
            log("Przekroczony limit czasu: czy działa kontener mcod-celery?")
            return 2
        time.sleep(a.interwal)
    if current[2] == "FAILURE":
        log("  Walidacja danych portalu: FAILURE (typy zgadywane przez portal); Wykaz AED czyta plik mimo to.")

    log("3/3 Wykaz AED")
    log(f"$ docker exec {a.kontener} python manage.py create_main_aed_resource --eager")
    code, lines = portal.manage("create_main_aed_resource", "--eager")
    summary = {}
    for line in lines:
        match = re.match(r"^(Zbiór|Zasób|Wiersze): (\d+)$", line)
        if match:
            summary[match.group(1)] = match.group(2)
        if " INFO " in line and ("Wykaz AED:" in line or "Duplikat" in line) or line.startswith(("Zbiór", "Zasób", "Wiersze")):
            log("  " + line.split(" INFO ", 1)[-1].strip())
        elif " WARNING " in line or " ERROR " in line:
            log("  " + line.split("    ", 1)[-1].strip())
    if code != 0:
        log("\n".join(lines[-20:]))
        log("Budowa wykazu nieudana.")
        return 1

    log("")
    log("Raport")
    log(f"  opis zbioru:    {a.url}")
    log(f"  zbiór dostawcy: {after['zbior']}, zasób CSV: {after['zasob']}, md5: {after.get('md5')}")
    log(f"  statusy zasobu: link {current[0]}, plik {current[1]}, dane {current[2]}")
    log(f"  Wykaz AED:      zbiór {summary.get('Zbiór')}, zasób {summary.get('Zasób')}, wiersze {summary.get('Wiersze')}")
    log(f"  czas:           {time.time() - started:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
