# Deploy da API

A API fica em `backend/` e já traz o modelo (`backend/models/greenleaf_effb0.onnx` + `.json`).
O app GreenLeaf (repositório Greenleaf-Mobile) é publicado à parte e chama esta API por `VITE_API_URL`.

## 1. Local

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env
python -m pytest
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Com a API rodando, acesse `http://localhost:8000/health`.

Docker:

```bash
docker compose up --build
```

## 2. Render

1. **New → Web Service → Docker**, *Root Directory* `backend/`.
2. Variáveis: `APP_ENV=production` e `CORS_ORIGINS=https://<domínio-do-app>`. A Render define `PORT` e o `Dockerfile`
   já usa essa variável. Não defina `CONFIDENCE_THRESHOLD`/`MODEL_WEIGHT` a não ser que queira sobrescrever os valores
   calibrados.
3. Confira `GET /health`: `model_loaded: true` e `model_version` preenchido.
4. No app, `VITE_API_URL=https://<servico>.onrender.com`.

## 3. Supabase (opcional)

Crie a tabela executando `supabase/migrations/001_create_prediction_logs.sql` e configure no ambiente da API:

```bash
SUPABASE_URL=https://SEU-PROJETO.supabase.co
SUPABASE_SERVICE_ROLE_KEY=chave_service_role_somente_na_api
SUPABASE_PREDICTION_TABLE=prediction_logs
```

Não coloque `SUPABASE_SERVICE_ROLE_KEY` no app nem em variáveis `VITE_*`.
