# Deploy do Axios Cassava IA

Este projeto tem duas partes:

- `frontend/`: interface React, recomendada para Vercel.
- `backend/`: API FastAPI com ONNX Runtime/OpenCV, recomendada para Docker (Render) ou servidor Python persistente.

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
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Se voce ja tinha um `venv` da versao antiga (TensorFlow), recrie o ambiente: a v2 usa ONNX Runtime.

Render (Docker): **New -> Web Service -> Docker**, *Root Directory* `backend/`. Configure
`APP_ENV=production` e `CORS_ORIGINS=https://<dominio-do-app>`. A Render define `PORT` e o
`Dockerfile` ja usa essa variavel. Confira em `GET /health` que `model_loaded` e `true`.

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
python -m pytest
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Com a API rodando, acesse `http://localhost:8000/health`.
