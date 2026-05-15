@echo off
REM Script de setup para rodar SEM Docker - Cassava Blight Detection
REM Este script configura tudo para rodar localmente no Windows

setlocal enabledelayedexpansion

cls
echo.
echo ================================================
echo 🌿 Cassava Blight Detection - Setup Local (SEM DOCKER)
echo ================================================
echo.

REM Verifica dependências
echo [1/5] 🔍 Verificando dependências...
echo.

where python > nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python não encontrado. Por favor, instale Python 3.9+
    echo    Baixe em: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ %PYTHON_VERSION% encontrado

where node > nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js não encontrado. Por favor, instale Node.js 18+
    echo    Baixe em: https://nodejs.org/
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo ✓ Node.js %NODE_VERSION% encontrado

echo.
echo [2/5] 📦 Configurando Backend...
echo.

cd backend

if not exist "venv" (
    echo Criando ambiente virtual Python...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ❌ Erro ao criar ambiente virtual
        pause
        exit /b 1
    )
    echo ✓ Ambiente virtual criado
) else (
    echo ✓ Ambiente virtual já existe
)

echo Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo Atualizando pip setuptools e wheel...
python -m pip install --upgrade pip setuptools wheel > nul 2>&1

echo Instalando dependências do backend...
pip install -r requirements.txt > nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Erro ao instalar dependências
    pause
    exit /b 1
)
echo ✓ Dependências do backend instaladas

if not exist "models" mkdir models
if not exist "logs" mkdir logs
echo ✓ Diretórios criados (models, logs)

cd ..

echo.
echo [3/5] 📦 Configurando Frontend...
echo.

cd frontend

if not exist ".env" (
    echo Criando .env do frontend
    (
        echo REACT_APP_API_BASE=http://localhost:8000
        echo REACT_APP_API_URL=http://localhost:8000/predict
    ) > .env
    echo ✓ .env do frontend criado
) else (
    echo ✓ .env já existe
)

if not exist "node_modules" (
    echo Instalando dependências do Node.js...
    call npm install > nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ Erro ao instalar dependências do Node
        pause
        exit /b 1
    )
    echo ✓ Dependências do frontend instaladas
) else (
    echo ✓ node_modules já existe
)

cd ..

echo.
echo [4/5] 🔐 Configurando Credenciais do Kaggle...
echo.

set KAGGLE_DIR=%USERPROFILE%\.kaggle

if exist "%KAGGLE_DIR%\kaggle.json" (
    echo ✓ Arquivo kaggle.json encontrado
) else (
    echo ⚠️  Arquivo kaggle.json não encontrado!
    echo.
    echo    Para usar o download automático do dataset:
    echo    1. Acesse: https://www.kaggle.com/settings/account
    echo    2. Clique em "Create New Token"
    echo    3. Um arquivo 'kaggle.json' será baixado
    echo    4. Coloque-o na pasta: %KAGGLE_DIR%
    echo.
    echo    Por enquanto, você pode prosseguir sem o dataset
)

echo.
echo [5/5] 🤖 Verificando modelo de IA...
echo.

if exist "backend\models\cassava_effnet_best.keras" (
    echo ✓ Modelo encontrado: cassava_effnet_best.keras
) else (
    echo ⚠️  Modelo não encontrado em backend\models\
    echo.
    echo    Se você tiver um modelo treinado, coloque em:
    echo    backend\models\cassava_effnet_best.keras
    echo.
    echo    Caso contrário, o sistema criará um modelo padrão
)

echo.
echo ================================================
echo ✅ Setup concluído com sucesso!
echo ================================================
echo.
echo 🚀 Para iniciar a aplicação:
echo.
echo    Execute o script: run_local.bat
echo.
echo    OU manualmente em dois terminais:
echo.
echo    Terminal 1 (Backend):
echo    cd backend
echo    venv\Scripts\activate.bat
echo    python -m uvicorn main:app --reload
echo.
echo    Terminal 2 (Frontend):
echo    cd frontend
echo    npm start
echo.
echo 🌐 Acessar em:
echo    Frontend:  http://localhost:3000
echo    API:       http://localhost:8000
echo    API Docs:  http://localhost:8000/docs
echo.
echo 📥 Para baixar dataset do Kaggle:
echo    cd backend
echo    python download_kaggle_dataset.py
echo.
echo ================================================
echo.

pause

