@echo off
REM Script para baixar o dataset do Kaggle de forma simples
REM Se você não tem credenciais, veja as instruções abaixo

cls
echo.
echo ================================================
echo 🌿 Download Dataset Cassava Leaf Disease
echo ================================================
echo.

if not exist ".kaggle\kaggle.json" (
    echo ❌ Arquivo kaggle.json não encontrado!
    echo.
    echo 📋 Para usar este script:
    echo.
    echo    1. Acesse: https://www.kaggle.com/settings/account
    echo    2. Role até "API"
    echo    3. Clique em "Create New Token"
    echo    4. Um arquivo 'kaggle.json' será baixado
    echo    5. Coloque-o na pasta: %USERPROFILE%\.kaggle\
    echo.
    echo    Depois execute este script novamente.
    echo.
    pause
    exit /b 1
)

echo ✓ Credenciais do Kaggle encontradas
echo.

REM Ativa o ambiente virtual
if not exist "venv" (
    echo ❌ Ambiente virtual não encontrado!
    echo    Execute setup_local.bat primeiro
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo.
echo [1/4] Verificando instalação do kaggle...
python -c "import kaggle" > nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Pacote kaggle não encontrado
    echo    Instalando...
    pip install kaggle > nul 2>&1
)
echo ✓ Kaggle API disponível
echo.

echo [2/4] 🌍 Baixando dataset...
echo.
echo ⏳ Isso pode levar alguns minutos (dataset ~3.4 GB)...
echo.

python download_kaggle_dataset.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ Erro ao baixar dataset
    pause
    exit /b 1
)

echo.
echo ================================================
echo ✅ Dataset baixado com sucesso!
echo ================================================
echo.

pause

