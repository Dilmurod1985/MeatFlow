# START_MEATFLOW.ps1 - старт MeatFlow на Windows
# Определяет локальный IP и запускает uvicorn

$ErrorActionPreference = 'Stop'

Write-Host "Запуск MeatFlow..." -ForegroundColor Cyan

# Получаем первый доступный не-loopback IPv4 адрес
$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -ne '127.0.0.1' -and $_.IPAddress -notlike '169.*' -and $_.InterfaceOperationalStatus -eq 'Up' } | Select-Object -First 1 -ExpandProperty IPAddress)
if(-not $ip){ $ip='localhost' }

Write-Host "Сервер будет доступен по адресу: http://$ip:8000" -ForegroundColor Green

# Запускаем uvicorn в новом окне
$script = "uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
Start-Process -FilePath powershell -ArgumentList "-NoExit","-Command","cd `"$(Get-Location)`"; $env:PYTHONPATH='.'; python -m pip install -r requirements.txt; $script" -WorkingDirectory (Get-Location)

Write-Host "Uvicorn запущен (в новом окне)." -ForegroundColor Cyan
