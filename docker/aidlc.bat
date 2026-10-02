@echo off
setlocal
REM ============================================================
REM  aidlc.bat - contenedor aislado tai-aidlc (Ubuntu + Claude Code + AI-DLC)
REM
REM  Uso:
REM    aidlc.bat [args de claude]   arranca el contenedor y entra a Claude Code
REM                                 (ej: aidlc.bat --continue)
REM    aidlc.bat --shell            abre bash dentro del contenedor
REM    aidlc.bat --stop             detiene el contenedor (conserva todo)
REM    aidlc.bat --rebuild          reconstruye la imagen y recrea el contenedor
REM    aidlc.bat --reset            borra contenedor + copia del repo (volumen);
REM                                 conserva los logins en docker\.state
REM ============================================================

set "DOCKER_DIR=%~dp0"
set "COMPOSE=docker compose -f "%DOCKER_DIR%compose.yml""
set "CID=tai-aidlc"

docker info >nul 2>&1
if errorlevel 1 (
    echo Docker no esta corriendo o no esta instalado. Inicia Docker Desktop primero.
    exit /b 1
)

REM Los bind mounts deben existir como DIRECTORIOS antes de levantar.
for %%D in (claude gh git) do if not exist "%DOCKER_DIR%.state\%%D" mkdir "%DOCKER_DIR%.state\%%D"

if /i "%~1"=="--stop"    goto :stop
if /i "%~1"=="--rebuild" goto :rebuild
if /i "%~1"=="--reset"   goto :reset
if /i "%~1"=="--shell"   goto :shell
goto :claude

:up
%COMPOSE% up -d
if errorlevel 1 ( echo ERROR al levantar el contenedor. & exit /b 1 )
docker exec -it -u developer %CID% aidlc-bootstrap
if errorlevel 1 ( echo ERROR en la preparacion del contenedor. & exit /b 1 )
goto :eof

:claude
call :up || exit /b 1
echo Lanzando Claude Code en /workspace ...
docker exec -it -u developer -w /workspace %CID% claude %*
exit /b %errorlevel%

:shell
call :up || exit /b 1
docker exec -it -u developer -w /workspace %CID% bash -l
exit /b %errorlevel%

:stop
%COMPOSE% stop
exit /b %errorlevel%

:rebuild
%COMPOSE% build --pull
if errorlevel 1 ( echo ERROR al construir la imagen. & exit /b 1 )
%COMPOSE% up -d --force-recreate
exit /b %errorlevel%

:reset
echo Se borrara el contenedor y la copia del repo (volumen tai-aidlc-workspace).
echo Lo que no hayas empujado a GitHub se PIERDE. Los logins en docker\.state se conservan.
set /p OK="Escribe 'si' para continuar: "
if /i not "%OK%"=="si" ( echo Cancelado. & exit /b 0 )
%COMPOSE% down -v
exit /b %errorlevel%
