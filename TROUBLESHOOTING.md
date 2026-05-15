## 🔧 Solução de Problemas Comuns

### ❌ "Python não encontrado"

**Solução:**
1. Baixe Python 3.9+ em: https://www.python.org/downloads/
2. Na instalação, **MARQUE** "Add Python to PATH"
3. Restart o computador
4. Execute `setup_local.bat` novamente

---

### ❌ "Node.js não encontrado"

**Solução:**
1. Baixe Node.js 18+ em: https://nodejs.org/
2. Instale normalmente
3. Restart o computador
4. Execute `setup_local.bat` novamente

---

### ❌ "Porta 8000 já está em uso"

**Solução:**
1. Feche outras aplicações que possam estar usando a porta
2. Ou altere a porta no backend/.env:
   ```
   PORT=8001
   ```
3. E altere no frontend/.env:
   ```
   REACT_APP_API_URL=http://localhost:8001/predict
   ```

---

### ❌ "Porta 3000 já está em uso"

**Solução:**
1. Feche outras aplicações (como outra instância do Node)
2. Execute em outro terminal:
   ```
   netstat -ano | findstr :3000
   ```
   Note o PID (número final)
   ```
   taskkill /PID [NUMERO] /F
   ```
3. Execute `run_local.bat` novamente

---

### ❌ "npm: comando não encontrado"

**Solução:**
1. Rode `npm --version` para testar
2. Se não funcionar, reinstale Node.js
3. Se Node.js está instalado mas npm não:
   ```
   npm install -g npm
   ```

---

### ❌ "pip: comando não encontrado"

**Solução:**
1. Use `python -m pip` ao invés de `pip`
2. Ou insira Python novamente

---

### ❌ "Backend não conecta ao banco" ou "Modelo não encontrado"

**Solução:**
1. Verifique se o arquivo existe:
   ```
   C:\Seu\Projeto\backend\models\cassava_effnet_best.keras
   ```
2. Se não existir, o sistema criará um modelo padrão automaticamente
3. Execute: `python launcher.py` e escolha opção 4 para verificar deps

---

### ❌ "CORS error" ou "Bloqueado por navegador"

**Solução:**
1. Abra `backend/.env` e verifique:
   ```
   CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
   ```
2. Se estiver usando outra porta, altere para:
   ```
   CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001
   ```
3. Reinicie o backend

---

### ❌ "Ambiente virtual não encontrado"

**Solução:**
1. Delete a pasta: `backend/venv`
2. Execute: `setup_local.bat`
3. Aguarde completar

---

### ❌ "node_modules bloqueado"

**Solução:**
1. Delete a pasta: `frontend/node_modules`
2. Execute: `npm install` dentro de `frontend/`
3. Aguarde completar

---

### ❌ "Kaggle.json não encontrado"

**Isso não é obrigatório!**

Se quiser baixar o dataset:
1. Acesse: https://www.kaggle.com/settings/account
2. Clique em "Create New Token"
3. Coloque `kaggle.json` em: `C:\Users\SEU_USUARIO\.kaggle\`
4. Execute: `backend/download_dataset.bat`

Se não quiser, a IA ainda funciona (usa modelo padrão).

---

### ❌ "Erro ao baixar dataset do Kaggle"

**Solução:**
1. Verifique `kaggle.json`:
   ```
   C:\Users\SEU_USUARIO\.kaggle\kaggle.json
   ```
2. Verifique se tem internet (o dataset é grande ~3.4 GB)
3. Tente novamente: `backend/download_dataset.bat`
4. Você pode pausar (`Ctrl+C`) e continuar depois

---

### ❌ "ModuleNotFoundError: tensorflow"

**Solução:**
1. Abra: `backend/`
2. Ative venv: `venv\Scripts\activate.bat`
3. Reinstale: `pip install -r requirements.txt`
4. Aguarde completar

---

### ❌ "Frontend diz 'Connection refused'"

**Solução:**
1. Verifique se backend está rodando (primeira janela do `run_local.bat`)
2. Acesse: http://localhost:8000/health
3. Se der erro, o backend não está rodando
4. Feche `run_local.bat` e execute novamente

---

### ❌ "Tudo está funcionando mas a IA não processa imagem"

**Solução:**
1. Teste a API:
   ```
   python test_api.py
   ```
2. Verifique se o modelo está carregado:
   ```
   http://localhost:8000/health
   ```
3. Verifique os logs:
   ```
   backend/logs/api.log
   ```

---

### ✅ Verificar se Tudo Está OK

```
python test_api.py
```

Esse script testa:
- ✅ Backend respondendo
- ✅ Frontend respondendo
- ✅ API Docs carregando
- ✅ Modelo carregado

Se tudo passar, está pronto para usar!

---

## 💡 Dicas Extras

### Executar Backend sem reload (melhor performance)
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Ver logs em tempo real
```bash
type backend\logs\api.log
```

### Limpar tudo e recomeçar
```bash
rmdir /s /q backend\venv
rmdir /s /q frontend\node_modules
del backend\.env
del frontend\.env
del backend\logs\api.log

Depois execute setup_local.bat novamente
```

### Mudar o threshold de confiança
Edite `backend/.env`:
```
CONFIDENCE_THRESHOLD=0.6  # Mais rigoroso
CONFIDENCE_THRESHOLD=0.4  # Mais lenient
```

---

## 📞 Se Nada Funcionar

1. Execute: `python test_api.py`
2. Verifique os logs: `backend/logs/api.log`
3. Leia: `EXECUTATION_GUIDE_PT_BR.md`
4. Refaça: `setup_local.bat`

---

**Não desista! A IA é simples de rodar! 🚀**

