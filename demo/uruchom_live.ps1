# Uruchamia wersję live: serwer dostawcy (8098, https), bramę demo/brama_live.py (8090) i tunel ngrok (demo/ngrok.yml),
# a potem wpisuje publiczny adres do WERSJA_LIVE.md. Portal w Dockerze musi już działać.
#   powershell -ExecutionPolicy Bypass -File demo/uruchom_live.ps1               # start
#   powershell -ExecutionPolicy Bypass -File demo/uruchom_live.ps1 -BezAdmina    # bez panelu administracyjnego
#   powershell -ExecutionPolicy Bypass -File demo/uruchom_live.ps1 -Zatrzymaj    # zatrzymaj tunel i bramę
# Dodatkowe hasło (Basic) na panel: przed startem $env:BRAMA_ADMIN_AUTH = "login:haslo" (nie zapisywać w repo).
param([switch]$Zatrzymaj, [switch]$BezAdmina, [int]$PortDostawcy = 8098, [int]$PortBramy = 8090)
$repo = Split-Path -Parent $PSScriptRoot
$log = Join-Path $env:TEMP "aed_live"
New-Item -ItemType Directory -Force $log | Out-Null

function Get-Nasluch([int]$port) { [bool](Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) }
function Stop-Skrypt([string]$wzor) {
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like "*$wzor*" } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
}

if ($Zatrzymaj) {
    Get-Process ngrok -ErrorAction SilentlyContinue | Stop-Process -Force
    Stop-Skrypt "brama_live.py"
    Write-Output "Zatrzymano tunel i bramę (serwer dostawcy działa dalej; portal korzysta z niego lokalnie)."
    exit 0
}

if (-not (Get-Nasluch $PortDostawcy)) {
    Start-Process python -ArgumentList "demo/serwer_zewnetrzny.py", "--https", "--port", "$PortDostawcy" -WorkingDirectory $repo `
        -WindowStyle Hidden -RedirectStandardOutput "$log\dostawca.log" -RedirectStandardError "$log\dostawca.err"
}
if (-not (Get-Nasluch $PortBramy)) {
    $argumenty = @("demo/brama_live.py", "--port", "$PortBramy", "--dostawca", "https://127.0.0.1:$PortDostawcy")
    if ($BezAdmina) { $argumenty += "--bez-admina" }
    Start-Process python -ArgumentList $argumenty -WorkingDirectory $repo -WindowStyle Hidden `
        -RedirectStandardOutput "$log\brama.log" -RedirectStandardError "$log\brama.err"
}
if (-not (Get-Process ngrok -ErrorAction SilentlyContinue)) {
    Start-Process ngrok -ArgumentList "start", "--all", "--config", "$env:LOCALAPPDATA\ngrok\ngrok.yml", "--config", "$repo\demo\ngrok.yml", `
        "--log", "$log\ngrok.log", "--log-format", "logfmt" -WindowStyle Hidden
}
$adres = $null
for ($i = 0; $i -lt 30 -and -not $adres; $i++) {
    Start-Sleep 1
    try { $adres = ((Invoke-RestMethod http://127.0.0.1:4040/api/tunnels).tunnels | Where-Object name -eq "aed-live").public_url } catch {}
}
if (-not $adres) { Write-Output "Tunel nie wystartował; dziennik: $log\ngrok.log"; exit 1 }
Write-Output "Publiczny adres: $adres  (strona startowa: $adres/live/)"
python "$repo\demo\ustaw_link_live.py" --portal $adres --sprawdz
