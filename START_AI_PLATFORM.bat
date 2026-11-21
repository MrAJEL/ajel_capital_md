@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title AJEL Capital
echo ========================================================
echo  AJEL CAPITAL - ARRANQUE
echo ========================================================

rem --- 1. Docker Desktop -------------------------------------------------------
docker info >nul 2>&1
if not errorlevel 1 goto docker_ok
echo Docker Desktop no esta corriendo. Intentando abrirlo...
if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
for /l %%i in (1,1,60) do (
    docker info >nul 2>&1 && goto docker_ok
    timeout /t 3 /nobreak >nul
)
echo [ERROR] Docker no arranco. Abre Docker Desktop, espera a que diga "Running" y vuelve a ejecutar este archivo.
pause
exit /b 1
:docker_ok

set "COMPOSE=docker compose"
docker compose version >nul 2>&1 || set "COMPOSE=docker-compose"

rem --- 2. .env (se crea una sola vez, con claves aleatorias) ----------------------
if exist ".env" goto env_ok
echo Creando .env con claves aleatorias...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$g=[Security.Cryptography.RandomNumberGenerator]::Create(); function H($n){$b=New-Object byte[] $n; $g.GetBytes($b); -join ($b | ForEach-Object { $_.ToString('x2') })}; (Get-Content '.env.example') -replace '^POSTGRES_PASSWORD=.*',('POSTGRES_PASSWORD='+(H 12)) -replace '^JWT_SECRET_KEY=.*',('JWT_SECRET_KEY='+(H 32)) -replace '^ENVIRONMENT=.*','ENVIRONMENT=development' | Set-Content -Encoding ascii '.env'"
if not exist ".env" (
    echo [ERROR] No se pudo crear .env. Copia .env.example a .env y rellenalo a mano.
    pause
    exit /b 1
)
:env_ok

rem --- 3. Levantar contenedores ------------------------------------------------
echo Levantando PostgreSQL, Redis, API y la web...
%COMPOSE% up -d --build
if errorlevel 1 (
    echo [ERROR] Fallo docker compose. Ultimos logs:
    %COMPOSE% logs --tail 40
    pause
    exit /b 1
)

rem --- 4. Esperar a que la web responda (la primera vez tarda 1-3 min) -----------
echo Esperando a que la app responda en http://localhost:3000 ...
for /l %%i in (1,1,90) do (
    curl.exe -sf -o nul -m 60 http://localhost:3000 && goto app_ok
    timeout /t 2 /nobreak >nul
)
echo [ERROR] La web no respondio. Estado y logs:
%COMPOSE% ps
%COMPOSE% logs --tail 40 frontend backend
pause
exit /b 1
:app_ok

rem --- 5. Abrir en Chrome (o en el navegador por defecto) ------------------------
set "URL=http://localhost:3000"
set "CHROME="
for %%p in ("%ProgramFiles%\Google\Chrome\Application\chrome.exe" "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" "%LocalAppData%\Google\Chrome\Application\chrome.exe") do if exist %%p set "CHROME=%%~p"
if defined CHROME (start "" "%CHROME%" "%URL%") else (start "" "%URL%")

set "IP="
for /f "usebackq delims=" %%a in (`powershell -NoProfile -Command "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch 'vEthernet|Loopback|WSL' -and $_.PrefixOrigin -in 'Dhcp','Manual' } | Select-Object -First 1).IPAddress"`) do set "IP=%%a"

echo ========================================================
echo  LISTO
echo  En esta PC:          %URL%
if defined IP echo  Desde el iPhone:     http://%IP%:3000   (mismo wifi)
echo  API / docs:          http://localhost:8000/docs
echo  Para apagar:         %COMPOSE% down
echo ========================================================
pause
