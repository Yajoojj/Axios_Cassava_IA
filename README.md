# Axios Cassava IA

Aplicacao para deteccao de bacteriose em folhas de mandioca usando uma API FastAPI com TensorFlow/EfficientNet, segmentacao HSV e uma interface React para envio de imagens.

## Estrutura

```text
backend/   API FastAPI, modelo, segmentacao HSV e integracao opcional Supabase
frontend/  Interface React publicada na Vercel
supabase/  SQL de criacao da tabela de logs
```

## Rodar Localmente

Backend:

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd frontend
npm ci
npm start
```

Acesse:

- Frontend: `http://localhost:3000`
- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

## Configuracao

Backend (`backend/.env`):

```bash
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
MODEL_PATH=models/cassava_effnet.h5
CONFIDENCE_THRESHOLD=0.30
MODEL_WEIGHT=0.50
MAX_UPLOAD_MB=8
```

Frontend:

```bash
REACT_APP_API_URL=http://localhost:8000/predict
```

Em producao, altere `REACT_APP_API_URL` para a URL publica do backend.

## Supabase

A integracao com Supabase e opcional. Quando `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` estiverem configuradas no backend, cada predicao sera registrada na tabela `prediction_logs`.

O SQL esta em:

```text
supabase/migrations/001_create_prediction_logs.sql
```

## Deploy

Veja [DEPLOY.md](DEPLOY.md).
