@echo off
chcp 65001 > nul
title Extrator de Seguidores do Instagram

echo =======================================================
echo    📥 EXTRATOR DE SEGUIDORES DO INSTAGRAM 📥
echo =======================================================
echo.

python extrair_seguidores.py

echo.
echo =======================================================
echo    Pressione qualquer tecla para fechar esta janela.
echo =======================================================
pause > nul
