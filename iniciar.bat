@echo off
color 0A
echo.
echo ===================================================
echo    Iniciando Generador de Reportes (IDIC ULima)
echo ===================================================
echo.

echo Iniciando servidor Backend (FastAPI)...
start "Backend - Generador de Reportes" cmd /c "cd backend && python main.py"
:: Pausa de 2 segundos para asegurar que el backend se levante primero
timeout /t 2 /nobreak > nul

echo Iniciando servidor Frontend (React/Vite) y abriendo el navegador...
start "Frontend - Generador de Reportes" cmd /c "cd frontend && npm run dev -- --open"

echo.
echo ¡Servicios iniciados! Se han abierto en ventanas separadas.
echo Puedes cerrar esta ventana.
echo.
timeout /t 3 /nobreak > nul
exit
