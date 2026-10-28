# Axios Cassava IA — GreenLeaf IA v2

API de apoio à detecção de **bacteriose** em folhas de mandioca, usada pelo app GreenLeaf (PI V — DSM, FATEC Registro).
A rede (EfficientNet-B0) foi treinada no dataset público
[Cassava Leaf Disease Classification (Kaggle)](https://www.kaggle.com/competitions/cassava-leaf-disease-classification),
exportada em **ONNX** e servida por **FastAPI + ONNX Runtime**, com o mesmo contrato de API da versão anterior.

> O resultado é uma estimativa e não substitui a avaliação de um agrônomo nem um exame de laboratório.

## Resultados (teste: 2.140 fotos nunca vistas, medidas com o código da API)

| | IA v2 | Regra só por cor (v1) |
|---|---|---|
| Acurácia nas 5 classes | **85,5 %** (meta O1 do artigo: ≥ 85 %) | — |
| F1 macro nas 5 classes | 74,4 % | — |
| Bacteriose: revocação | **78,0 %** | 96,3 % |
| Bacteriose: especificidade | **95,5 %** | 7,9 % |
| Bacteriose: precisão | 48,3 % | 5,3 % |
| Bacteriose: AUC ROC | **0,92** | 0,60 |
| Tempo por foto (CPU) | ~45 ms | — |

A regra antiga "achava" quase toda bacteriose porque marcava **92 % de todas as folhas** como doentes.
Detalhes por classe e matriz de confusão: [training/reports/metrics.md](training/reports/metrics.md).
Integração com o app: [INTEGRACAO.md](INTEGRACAO.md).

## O que mudou em relação à v1

| | v1 | v2 |
|---|---|---|
| Dados | pastas `healthy/` e `infected/` (origem não documentada) | 21.397 fotos de campo do Kaggle (Uganda), rotuladas por especialistas |
| Tarefa da rede | binária (infectado × sadio) | **5 classes**: bacteriose (CBB), estria marrom (CBSD), mosqueado verde (CGM), mosaico (CMD), sadia |
| Treino | só a cabeça; EfficientNet congelada | **ajuste fino da EfficientNet-B0 inteira**, aumento de dados, pesos por classe, *label smoothing* |
| Decisão | 35 % rede + 65 % cor, limiares fixos | peso e limiar **calibrados na validação** (F2 da bacteriose) |
| Avaliação | não havia | divisão estratificada 80/10/10, teste nunca visto, métricas por classe |
| Explicação visual | manchas por cor em toda a foto (bordas, sombras e solo viravam "manchas"; lesões saíam azuis) | manchas **só onde a rede viu doença** + contorno amarelo dessa região (CAM) |
| Execução | TensorFlow (~500 MB) | ONNX Runtime (~15 MB); o mesmo `.onnx` roda no navegador |

Por que 5 classes: o mosaico (CMD) e as outras viroses também amarelam e mancham a folha. Uma IA que só conhece
"infectado × sadio" confunde essas doenças com bacteriose. Separá-las é o que torna o diagnóstico de bacteriose
confiável — e permite ao app avisar "não é bacteriose, mas a folha tem outra doença".

## Estrutura do repositório

```text
backend/      API FastAPI + ONNX Runtime (pasta pronta para Docker / Render)
  app/          main.py (rotas), analysis.py (regra de decisão), model.py (ONNX), hsv.py (cor e overlay)
  models/       greenleaf_effb0.onnx + greenleaf_effb0.json (classes, tamanho, limiar calibrado, métricas)
  tests/        testes do contrato da API
training/     pipeline de treino (PyTorch + timm), divisão usada e relatórios
frontend/     interface React antiga para upload e exibição (continua compatível)
supabase/     migração SQL para logs opcionais de predição
INTEGRACAO.md contrato da API e integração com o app GreenLeaf
DEPLOY.md     guia de publicação
```

## Execução local

```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements-dev.txt
.venv/Scripts/python -m pytest
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
```

- API: `http://localhost:8000` — Swagger: `http://localhost:8000/docs` — Health: `http://localhost:8000/health`
- Variáveis em `backend/.env.example` (copie para `backend/.env`). Deixe `CONFIDENCE_THRESHOLD` e `MODEL_WEIGHT` vazios
  para usar os valores calibrados que estão em `backend/models/greenleaf_effb0.json`.
- O frontend React antigo continua funcionando (`cd frontend && npm ci && npm start`), e os scripts `setup_local.bat` /
  `run_local.bat` sobem os dois.

## Endpoints

| Método | Rota | Descrição |
| --- | --- | --- |
| `GET` | `/` | Informações básicas da API |
| `GET` | `/health` | Status, modelo carregado, versão do modelo e Supabase |
| `GET` | `/metrics` | Total de predições e tempo médio |
| `POST` | `/predict` | Recebe a foto (campo `image`) e retorna classe, probabilidade, severidade, overlay e as 5 classes |

O contrato completo está em [INTEGRACAO.md](INTEGRACAO.md).

## Supabase (opcional)

Com `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` configuradas na API, cada predição é registrada na tabela
`prediction_logs` (migração em `supabase/migrations/001_create_prediction_logs.sql`). A chave service role fica
**somente** no servidor.

## Limitações

- **Severidade (Leve/Moderada/Grave) não é aprendida**: o Kaggle não tem rótulo de severidade. Ela vem da taxa de manchas
  medida pela cor dentro da região apontada pela rede (< 3 %, < 15 %, ≥ 15 %) e não pôde ser validada com rótulos.
- **Meta O2 (revocação ≥ 90 %) ainda não atingida**: a revocação é 78 % no limiar calibrado (0,26). Baixar o limiar
  aumenta a revocação, mas também os alarmes falsos.
- **"Chance" baixa com diagnóstico positivo**: com limiar 0,26 o app pode mostrar "33 % de chance" junto de "Sinais de
  bacteriose". Vale trocar a porcentagem por um nível de risco (baixo/médio/alto).
- **Domínio**: as fotos são de Uganda. Antes de afirmar desempenho no Vale do Ribeira é preciso testar com fotos locais.
- **Ruído de rótulo**: parte dos rótulos da competição é conhecida por estar errada; isso limita a acurácia máxima.
- A rede não recusa fotos que não são de folha de mandioca; só há checagem de tamanho e de luz.

## Licença

Este projeto está licenciado conforme os termos descritos em [LICENSE](LICENSE).
