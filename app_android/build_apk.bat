@echo off
title InstaSorteio - Gerador de APK Android
cls

echo =======================================================
echo         📱 GERADOR DE APK ANDROID - INSTASORTEIO
echo =======================================================
echo.
echo Verificando ambiente de desenvolvimento Android...
echo.

where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [AVISO] Node.js nao foi detectado no sistema.
    echo Para compilar o APK localmente, instale o Node.js: https://nodejs.org/
    echo.
    echo DICA: Voce tambem pode compilar o APK de graca na Nuvem
    echo usando o GitHub Actions (veja README_ANDROID.md).
    pause
    exit /b
)

echo [1/3] Instalando dependencias do Capacitor...
call npm install

echo [2/3] Sincronizando arquivos com o projeto Android...
call npx cap sync android

echo [3/3] Abrindo projeto no Android Studio...
call npx cap open android

echo.
echo =======================================================
echo  Projeto aberto no Android Studio!
echo  Clique em: Build - Build Bundle(s) / APK(s) - Build APK(s)
echo =======================================================
pause
