@echo off
title SQM Search - Siti Astronomici Buoi da Ghirano
color 0b

:: Spostati nella cartella dello script
cd /d "%~dp0"

echo ====================================================================
echo      SQM Search - Ricerca Siti Astronomici da Ghirano di Prata
echo ====================================================================
echo.

:: Verifica presenza ambiente virtuale
if exist "%~dp0.venv\Scripts\streamlit.exe" (
    echo [OK] Ambiente virtuale rilevato (.venv)
    echo [*] Avvio della dashboard Streamlit in corso...
    echo [*] Il browser si aprira automaticamente tra pochi secondi.
    echo.
    "%~dp0.venv\Scripts\streamlit.exe" run app.py
) else (
    echo [!] Ambiente virtuale non trovato, tento con lo Streamlit di sistema...
    python -m streamlit run app.py
)

if %errorlevel% neq 0 (
    echo.
    echo [ERRORE] Si e verificato un problema durante l'avvio.
    pause
)
