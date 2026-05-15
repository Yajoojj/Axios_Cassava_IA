# 🚀 Guia de Execução - SEM DOCKER

> **Este guia mostra como rodar o Cassava Blight Detection diretamente no Windows, sem Docker.**

## ⚡ Início Rápido (3 Passos)

### Passo 1: Setup Inicial
```bash
# 1. Abra o PowerShell ou CMD
# 2. Navegue até a pasta do projeto
cd C:\Caminho\Do\Seu\Projeto\Axios_Cassava_IA

# 3. Execute o setup
setup_local.bat
```

Este script irá:
- ✓ Verificar Python 3.9+
- ✓ Verificar Node.js 18+
- ✓ Criar ambiente virtual Python
- ✓ Instalar todas as dependências
- ✓ Configurar arquivos .env
- ✓ Criar pastas necessárias

### Passo 2: Iniciar a Aplicação
```bash
# Execute em uma única vez (abre dois terminais automaticamente)
run_local.bat
```

Isso vai:
- ✓ Iniciar Backend na porta 8000
- ✓ Iniciar Frontend na porta 3000
- ✓ Abrir em duas janelas separadas

### Passo 3: Acessar no Navegador
```
Frontend:      http://localhost:3000
API Docs:      http://localhost:8000/docs
Health Check:  http://localhost:8000/health
```

---

## 📥 Configurar Kaggle (IMPORTANTE!)

Se você quer baixar o dataset:

### 1️⃣ Obter Credenciais Kaggle

1. Acesse: https://www.kaggle.com/settings/account
2. Role até a seção **API**
3. Clique em **"Create New Token"**
4. Um arquivo `kaggle.json` será baixado

### 2️⃣ Colocar o Arquivo no Lugar Certo

**Windows:**
```
C:\Users\SEU_USUARIO\.kaggle\kaggle.json
```

### 3️⃣ Baixar o Dataset

```bash
cd backend
download_dataset.bat
```

Ou manualmente:
```bash
cd backend
venv\Scripts\activate.bat
python download_kaggle_dataset.py
```

---

## 🔧 Execução Manual (Sem Scripts)

Se preferir não usar `run_local.bat`, pode fazer manualmente:

### Terminal 1 - Backend
```bash
cd backend
venv\Scripts\activate.bat
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2 - Frontend
```bash
cd frontend
npm start
```

---

## 🧠 Estrutura de Pastas

Você verá criadas:

```
backend/
├── venv/                  # Ambiente virtual Python
├── models/               # Seus modelos treinados
├── logs/                 # Logs da API
└── dataset/
    ├── healthy/          # Folhas saudáveis (se baixar)
    └── infected/         # Folhas infectadas (se baixar)

frontend/
└── node_modules/         # Dependências Node.js
```

---

## 📊 Verificar se Está Funcionando

### Health Check
```bash
# Em qualquer terminal
curl http://localhost:8000/health
```

Resposta esperada:
```json
{
  "status": "ok",
  "timestamp": "2026-05-15T...",
  "model_loaded": true,
  "version": "1.0.0"
}
```

### Testar API
```bash
curl -X POST http://localhost:8000/predict \
  -F "image=@caminho/da/sua/imagem.jpg"
```

---

## ⚠️ Solução de Problemas

### "Porta 8000 já está em uso"
```bash
# Change backend port
python -m uvicorn main:app --port 8001
```

### "Porta 3000 já está em uso"
```bash
# Em frontend/.env, altere:
REACT_APP_API_URL=http://localhost:8001/predict
```

### "Python não encontrado"
- Instale Python 3.9+ de: https://www.python.org/downloads/
- Selecione "Add Python to PATH" durante a instalação

### "Node.js não encontrado"
- Instale Node.js 18+ de: https://nodejs.org/

### "Kaggle.json não encontrado"
- Não é obrigatório. Você pode testar a API sem dataset
- Se quiser baixar depois, siga as instruções acima

---

## 🎯 Próximos Passos

### 1. Testar a Interface
1. Abra http://localhost:3000
2. Clique ou arraste uma imagem
3. Veja os resultados em tempo real

### 2. Treinar Seu Modelo (Opcional)
```bash
cd backend
python train_efficientnet.py --data-dir dataset --epochs 30
```

### 3. Deploy em Produção
- Veja [SETUP.md](SETUP.md) para instruções avançadas

---

## 💡 Dicas Úteis

### Hot Reload (Desenvolvimento)
O backend já está com `--reload`, então qualquer mudança em `main.py` causa recarga automática.

### Ver Logs
- Backend: Veja a janela do terminal correspondente
- Frontend: Veja a janela do terminal correspondente
- API: `backend/logs/api.log`

### Limpar Tudo e Recomeçar
```bash
# Windows
rmdir /s /q backend\venv
rmdir /s /q frontend\node_modules
del frontend\.env
del backend\.env

# Depois execute setup_local.bat novamente
```

---

## 📚 Mais Informações

- **Documentação Completa**: [README.md](README.md)
- **Setup Avançado**: [SETUP.md](SETUP.md)
- **API Docs**: http://localhost:8000/docs (ao rodar)
- **Logs**: `backend/logs/api.log`

---

## 🆘 Precisa de Ajuda?

1. Verifique se Python 3.9+ está instalado
2. Verifique se Node.js 18+ está instalado
3. Executar `setup_local.bat` novamente
4. Verifique os logs em `backend/logs/api.log`

---

**Pronto para começar? Execute: `setup_local.bat` seguido de `run_local.bat`** 🚀

