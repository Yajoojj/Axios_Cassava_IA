# ⚠️ IMPORTANTE: LEIA PRIMEIRO!

## Como Rodar a IA (SEM DOCKER)

### ✅ Opção 1: Jeito MAIS Fácil (Recomendado)

```
1. Duplo clique em: launcher.py
   (Ou execute: python launcher.py)
   
   Isso abre um menu:
   - Escolha opção 1 para setup
   - Depois escolha opção 2 para rodar
```

---

### ✅ Opção 2: Jeito Rápido

```
1. Duplo clique em: setup_local.bat
   (Aguarde completar - pode levar 5-10 minutos)

2. Duplo clique em: run_local.bat
   (Abre 2 janelas: Backend e Frontend)

3. Acesse no navegador: http://localhost:3000
```

---

### ✅ Opção 3: Jeito Manual (Mais Controle)

```
Terminal 1 (Backend):
  cd backend
  venv\Scripts\activate.bat
  python -m uvicorn main:app --reload

Terminal 2 (Frontend):
  cd frontend
  npm start

Navegador:
  http://localhost:3000
```

---

## 🔐 Se Quiser Baixar Dataset do Kaggle

1. Acesse: https://www.kaggle.com/settings/account
2. Role até "API" e clique "Create New Token"
3. Um arquivo "kaggle.json" será baixado
4. **Coloque em:** C:\Users\SEU_USUARIO\.kaggle\kaggle.json
5. Execute: backend/download_dataset.bat

---

## ✨ Pronto! Agora você terá:

- ✅ Frontend em http://localhost:3000
- ✅ API em http://localhost:8000
- ✅ Documentação em http://localhost:8000/docs
- ✅ Health Check em http://localhost:8000/health

---

## 📋 Pré-requisitos (Só Verificar)

- Python 3.9+ → https://www.python.org/downloads/
- Node.js 18+ → https://nodejs.org/

(Se não tiver, instale antes de rodar)

---

## 📚 Documentação Completa

- **COMECE_AQUI.txt** → Guia super rápido
- **EXECUTATION_GUIDE_PT_BR.md** → Guia completo
- **README.md** → Documentação técnica

---

## 🆘 E SE Não Funcionar?

Execute: `python test_api.py`

Isso testa se tudo está funcionando.

---

## 🎯 TL;DR (Resume MUITO)

```
1. Execute: setup_local.bat
2. Execute: run_local.bat
3. Acesse: http://localhost:3000
```

Pronto! 🚀

