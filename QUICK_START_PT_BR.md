## 🎯 SIGA ESTE GUIA PASSO A PASSO

---

## PASSO 1: PRÉ-REQUISITOS (Só verificar UMA VEZ)

### Você tem Python 3.9+?
```
Windows + R → cmd
python --version
```

Se não tiver:
→ Baixe em https://www.python.org/downloads/
→ Marque "Add Python to PATH"
→ Restart PC

### Você tem Node.js 18+?
```
node --version
```

Se não tiver:
→ Baixe em https://nodejs.org/
→ Instale normalmente
→ Restart PC

---

## PASSO 2: PREPARAR (SÓ EXECUTA UMA VEZ)

```
1. Abra a pasta do projeto
2. Duplo clique em: setup_local.bat
3. Aguarde completar (pode levar 5-10 minutos)
```

Esse script faz:
✅ Criar ambiente Python
✅ Instalar dependências
✅ Configurar pastas
✅ Preparar tudo

---

## PASSO 3: RODAR (TODA VEZ QUE QUISER)

```
1. Duplo clique em: run_local.bat
2. Abre 2 janelas automaticamente
3. Aguarde carregar (30-60 segundos)
```

Abra seu navegador:
```
http://localhost:3000
```

---

## PASSO 4: USAR A IA

1. Arraste uma imagem de folha
2. Clique em "Analisar"
3. Veja os resultados!

---

## (OPCIONAL) PASSO 5: BAIXAR DATASET

Se quiser análises mais precisas com seu próprio dataset:

### 5.1 Obter Kaggle.json
```
1. Acesse: https://www.kaggle.com/settings/account
2. Role até "API"
3. Clique "Create New Token"
4. Um arquivo "kaggle.json" será baixado
```

### 5.2 Colocar no Lugar Certo
```
Copie o arquivo para:
C:\Users\SEU_USUARIO\.kaggle\kaggle.json

(Crie a pasta .kaggle se não existir)
```

### 5.3 Baixar Dataset
```
1. Abra pasta: backend/
2. Duplo clique em: download_dataset.bat
3. Aguarde (vai levar 30+ minutos)
```

---

## ✅ TESTANDO SE TUDO FUNCIONA

```
python test_api.py
```

Se tudo der verde (✅), está pronto!

---

## 🆘 DEU ERRO?

Ver: **TROUBLESHOOTING.md**

Se não resolver:
1. Feche tudo
2. Execute: setup_local.bat
3. Execute: run_local.bat
4. Execute: python test_api.py

---

## 📍 IMPORTANTE

### Arquivo .env do Kaggle

Você já tem um arquivo `kaggle.json` com credenciais:
```json
{"username":"yagokurashiki","key":"8eafa35437cadcf3164954f5bf68856c"}
```

Coloque na pasta home:
```
C:\Users\SEU_USUARIO\.kaggle\kaggle.json
```

O script detectará automaticamente.

---

## 🚀 COMEÇAR AGORA

Abra PowerShell ou CMD nesta pasta e execute:

### Forma 1: Menu Interativo (Melhor)
```
python launcher.py
```

### Forma 2: Scripts (Automático)
```
setup_local.bat
run_local.bat
```

### Forma 3: Manual (Mais Controle)
```
Terminal 1:
cd backend
venv\Scripts\activate.bat
python -m uvicorn main:app --reload

Terminal 2:
cd frontend
npm start
```

---

## 📌 ATALHOS

| Ação | Comando |
|------|---------|
| Preparar | `setup_local.bat` |
| Rodar | `run_local.bat` |
| Testar | `python test_api.py` |
| Menu | `python launcher.py` |
| Baixar Dataset | `backend\download_dataset.bat` |

---

## 🎓 DOCUMENTAÇÃO

Leia nessa ordem:

1. **START_HERE.md** ← Você está aqui!
2. COMECE_AQUI.txt
3. EXECUTATION_GUIDE_PT_BR.md
4. TROUBLESHOOTING.md
5. README.md

---

## 💡 DICAS

✅ Feche run_local.bat com `Ctrl+C` em cada janela
✅ Se der erro de porta, veja TROUBLESHOOTING.md
✅ Logs estão em: backend/logs/api.log
✅ Modelo está em: backend/models/

---

## 🎉 PRONTO!

Quando der tudo certo, você terá:
- ✅ Frontend: http://localhost:3000
- ✅ API: http://localhost:8000
- ✅ API Docs: http://localhost:8000/docs
- ✅ IA funcionando 100%

**Boa sorte! 🌿**

