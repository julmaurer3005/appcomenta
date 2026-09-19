@echo off
title Bot de Sorteios Instagram
cls

echo =======================================================
echo        INICIANDO BOT DE SORTEIOS DO INSTAGRAM
echo =======================================================
echo.
echo Abrindo o painel de controle visual...
echo.

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python app_gui.py
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo [AVISO] O aplicativo foi encerrado.
        pause
    )
    goto :fim
)

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py app_gui.py
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo [AVISO] O aplicativo foi encerrado.
        pause
    )
    goto :fim
)

echo [ERRO] Python nao foi encontrado no seu computador!
echo Por favor, certifique-se de que o Python esta instalado.
echo Baixe em: https://www.python.org/
pause

:fim
