@echo off
REM Script para iniciar o servidor Backend e Frontend localmente
REM SEM DOCKER - Apenas desenvolvimento local

setlocal enabledelayedexpansion

cls
echo.
echo ================================================
echo 🚀 Iniciando Cassava Blight Detection (SEM DOCKER)
echo ================================================
echo.

REM Verifica se os ambientes foram configurados
if not exist "backend\venv" (
    echo ❌ Ambiente virtual do backend não encontrado!
    echo    Execute: setup_local.bat
    pause
    exit /b 1
)

if not exist "frontend\node_modules" (
    echo ❌ Dependências do frontend não encontradas!
    echo    Execute: setup_local.bat
    pause
    exit /b 1
)

echo ✓ Ambientes de desenvolvimento encontrados
echo.

REM Inicia o Backend em uma nova janela
echo [1] Iniciando Backend em porta 8000...
start "Backend - Cassava API" cmd /k "cd backend && venv\Scripts\activate.bat && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM Aguarda um pouco para o backend ligar
timeout /t 3 /nobreak

REM Inicia o Frontend em uma nova janela
echo [2] Iniciando Frontend em porta 3000...
start "Frontend - Cassava Web" cmd /k "cd frontend && npm start"

echo.
echo ================================================
echo ✅ Serviços iniciados!
echo ================================================
echo.
echo 🌐 Acessar em:
echo    Frontend:  http://localhost:3000
echo    API:       http://localhost:8000
echo    API Docs:  http://localhost:8000/docs
echo    Health:    http://localhost:8000/health
echo.
echo 📝 Logs:
echo    Backend:   Veja a primeira janela
echo    Frontend:  Veja a segunda janela
echo.
echo ⚠️  Para parar os serviços:
echo    Feche as duas janelas de terminal
echo.
echo ================================================
echo.

pause

