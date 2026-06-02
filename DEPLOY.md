# Deploy do Axios Cassava IA

Este projeto tem duas partes:

- `frontend/`: interface React, recomendada para Vercel.
- `backend/`: API FastAPI com TensorFlow/OpenCV, recomendada para Docker ou servidor Python persistente.

## 1. GitHub

Antes de enviar:

```bash
git status
git add .
git commit -m "Corrige IA, deploy e integracao Supabase"
git push origin main
```

O `.gitignore` impede envio de `venv`, `node_modules`, datasets, logs e segredos.

## 2. Vercel

A Vercel deve publicar o frontend.

Configuracao:

- Build command: `cd frontend && npm ci && npm run build`
- Output directory: `frontend/build`
- Environment variable:
  - `REACT_APP_API_URL=https://URL-DO-SEU-BACKEND/predict`

O arquivo `vercel.json` ja deixa esses caminhos configurados.

## 3. Backend

Local:

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Se voce ja tinha um `venv` antigo com TensorFlow 2.14, recrie o ambiente. Os
modelos `.h5` deste repositorio usam formato mais novo de Keras e precisam das
versoes pinadas em `backend/requirements.txt`.

Docker:

```bash
docker compose up --build
```

Endpoints uteis:

- `GET /health`
- `GET /metrics`
- `POST /predict`

## 4. Supabase

Crie a tabela executando:

```sql
supabase/migrations/001_create_prediction_logs.sql
```

Depois configure no ambiente do backend:

```bash
SUPABASE_URL=https://SEU-PROJETO.supabase.co
SUPABASE_SERVICE_ROLE_KEY=chave_service_role_somente_no_backend
SUPABASE_PREDICTION_TABLE=prediction_logs
```

Nao coloque `SUPABASE_SERVICE_ROLE_KEY` no frontend ou em variaveis `REACT_APP_*`.

## 5. Checklist rapido

```bash
cd frontend
npm ci
npm run build

cd ..\backend
python -m compileall .
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Com a API rodando, acesse `http://localhost:8000/health`.
