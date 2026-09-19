@echo off
title InstaSorteio - Servidor App Mobile
cls

echo =======================================================
echo     📱 INICIANDO SERVIDOR DO APP MOBILE (PWA) 📱
echo =======================================================
echo.
echo Iniciando servidor web para controle pelo celular...
echo.

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python app_mobile\server.py
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo [AVISO] O servidor foi finalizado.
        pause
    )
    goto :fim
)

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py app_mobile\server.py
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo [AVISO] O servidor foi finalizado.
        pause
    )
    goto :fim
)

echo [ERRO] Python nao foi encontrado no seu computador!
pause

:fim
