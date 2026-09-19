@echo off
title Instalacao do Bot de Sorteios
cls

echo =======================================================
echo       INSTALANDO DEPENDENCIAS DO BOT (1a VEZ)
echo =======================================================
echo.
echo 1. Instalando bibliotecas necessarias...

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python -m pip install -r requirements.txt
    echo.
    echo 2. Baixando navegador seguro (Chromium)...
    python -m playwright install chromium
    goto :sucesso
)

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -m pip install -r requirements.txt
    echo.
    echo 2. Baixando navegador seguro (Chromium)...
    py -m playwright install chromium
    goto :sucesso
)

echo [ERRO] Python nao foi encontrado no seu computador!
pause
exit /b 1

:sucesso
echo.
echo =======================================================
echo        TUDO PRONTO COM SUCESSO!
echo    Agora basta dar 2 cliques em "INICIAR_BOT.bat"
echo =======================================================
echo.
pause
