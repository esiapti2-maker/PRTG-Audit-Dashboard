@echo off
title Servidor de Auditoria PRTG
color 0B
echo =========================================================================
echo        PRTG AUDIT INTEGRATED DASHBOARD - INICIADOR AUTOMATICO
echo =========================================================================
echo [+] Verificando entorno...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [-] Error: Python no esta instalado o no se encuentra en el PATH.
    echo Por favor instala Python 3.8+ o agregalo a tus variables de entorno.
    pause
    exit /b 1
)

echo [+] Iniciando el servidor local de Python en el puerto 5000...
echo [+] Abriendo el navegador en http://localhost:5000/
echo [!] Para apagar el servidor de auditoria, cierra esta ventana o presiona Ctrl+C.
echo =========================================================================
echo.

python "%~dp0server.py"

pause
