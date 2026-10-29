# Axios Cassava IA — GreenLeaf IA v2.1

API de apoio à detecção de **bacteriose** em folhas de mandioca, usada pelo app GreenLeaf (PI V — DSM, FATEC Registro).
A rede (EfficientNet-B0) foi treinada no dataset público
[Cassava Leaf Disease Classification (Kaggle)](https://www.kaggle.com/competitions/cassava-leaf-disease-classification),
exportada em **ONNX** e servida por **FastAPI + ONNX Runtime**, com o mesmo contrato de API da versão anterior.

> O resultado é uma estimativa e não substitui a avaliação de um agrônomo nem um exame de laboratório.

## Resultados (teste: 2.140 fotos nunca vistas, medidas com o código da API)

| | IA v2.1 (atual) | IA v2.0 | Regra só por cor (v1) |
|---|---|---|---|
| Acurácia nas 5 classes | **87,2 %** (meta O1 do artigo: ≥ 85 %) | 85,5 % | — |
| F1 macro nas 5 classes | **77,6 %** | 74,4 % | — |
| Bacteriose: precisão (alarmes corretos) | **61,4 %** | 48,3 % | 5,3 % |
| Bacteriose: revocação (bacterioses encontradas) | 64,2 % | 78,0 % | 96,3 % |
| Bacteriose: especificidade | **97,8 %** | 95,5 % | 7,9 % |
| Alarmes falsos (em 2.031 folhas sem bacteriose) | **44** | 91 | 1.870 |
| Bacterioses perdidas (de 109) | 39 | 24 | 4 |
| Folhas sadias com bacteriose como classe mais provável | **17** | 39 | — |
| Bacteriose: AUC ROC | **0,93** | 0,92 | 0,60 |
| Tempo por análise (PC; ~2 s na Render gratuita) | ~0,2 s | ~0,1 s | — |

A v2.1 troca revocação por precisão: corta pela metade os alarmes falsos (91 → 44), mas deixa passar mais
bacterioses (24 → 39). O ponto de corte muda sem retreinar: `CONFIDENCE_THRESHOLD=0.16` volta a ~81 % de revocação no
teste, com ~100 alarmes falsos. A regra antiga "achava" quase toda bacteriose porque marcava **92 % de todas as folhas**
como doentes.
Detalhes por classe e matriz de confusão: [training/reports/metrics.md](training/reports/metrics.md).
Integração com o app: [INTEGRACAO.md](INTEGRACAO.md).

## O que mudou na v2.1

- **Rede em 384 px** (era 256): 4 épocas de ajuste fino a partir da v2.0. Manchas pequenas ficam visíveis: +1,7 ponto de
  acurácia e menos da metade das folhas sadias tomadas por bacteriose (39 → 17). O mapa de atenção passou de 8x8 para 12x12.
- **Limiar escolhido pelo F1** (equilíbrio entre alarme falso e bacteriose perdida) em vez do F2 (que favorecia achar
  toda bacteriose e gerava muitos alarmes falsos).
- **Amarelo é folha, não mancha**: clorose (mosaico, folha velha, falta de nutriente) não é lesão de bacteriose. Antes, uma
  folha amarelada saía toda vermelha e "Grave". Agora só necrose conta: marrom, marrom-arroxeado, escuro ou acinzentado.
- **Sem bacteriose, sem vermelho**: quando a decisão é "não é bacteriose", o overlay não marca "manchas suspeitas" e a
  taxa volta 0.
- **A cor não entra na decisão**: sozinha, a taxa de manchas tem AUC 0,43 no teste (não distingue bacteriose de estria
  marrom, sombra ou solo). A calibração só a usaria se melhorasse o F1 da validação em mais de 0,01.

## O que mudou em relação à v1

| | v1 | v2 |
|---|---|---|
| Dados | pastas `healthy/` e `infected/` (origem não documentada) | 21.397 fotos de campo do Kaggle (Uganda), rotuladas por especialistas |
| Tarefa da rede | binária (infectado × sadio) | **5 classes**: bacteriose (CBB), estria marrom (CBSD), mosqueado verde (CGM), mosaico (CMD), sadia |
| Treino | só a cabeça; EfficientNet congelada | **ajuste fino da EfficientNet-B0 inteira** (256 px e depois 384 px), aumento de dados, pesos por classe, *label smoothing* |
| Decisão | 35 % rede + 65 % cor, limiares fixos | limiar **calibrado na validação** (F1 da bacteriose); a cor só entraria se ajudasse |
| Avaliação | não havia | divisão estratificada 80/10/10, teste nunca visto, métricas por classe |
| Explicação visual | manchas por cor em toda a foto (amarelo, bordas, sombras e solo viravam "manchas"; lesões saíam azuis) | necrose **só na folha analisada e só quando é bacteriose** + contorno amarelo da região que mais pesou (CAM) |
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
- Também roda com Docker: `docker compose up --build`.

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

- **Severidade (Leve/Moderada/Grave) não é aprendida**: o Kaggle não tem rótulo de severidade. Ela vem da taxa de necrose
  medida pela cor na folha analisada (< 3 %, < 15 %, ≥ 15 %) e não pôde ser validada com rótulos. Como o amarelo deixou
  de contar, a maioria das bacterioses sai Leve ou Moderada.
- **Meta O2 (revocação ≥ 90 %) não atingida**: a revocação é 64 % no limiar de equilíbrio (0,28) e ~81 % com
  `CONFIDENCE_THRESHOLD=0.16`, ao custo de mais que o dobro de alarmes falsos. A escolha é da equipe.
- **"Chance" baixa com diagnóstico positivo**: com limiar 0,28 o app pode mostrar "30 % de chance" junto de "Sinais de
  bacteriose". Vale trocar a porcentagem por um nível de risco (baixo/médio/alto).
- **Mancha acinzentada**: a cor ainda não marca bem lesões de centro cinza ou bege; a rede as reconhece, mas o vermelho
  pode não aparecer nelas.
- **Domínio**: as fotos são de Uganda. Antes de afirmar desempenho no Vale do Ribeira é preciso testar com fotos locais.
- **Ruído de rótulo**: parte dos rótulos da competição é conhecida por estar errada; isso limita a acurácia máxima.
- **Overlay em mato denso**: a folha analisada é separada do fundo pela cor. Quando toda a vegetação verde se encosta,
  ou quando a folha doente quase não tem verde (amarelada, seca), não dá para isolá-la: o contorno não é recortado e
  a cor pode marcar folhagem seca ao redor. O diagnóstico não muda (vem só da rede). Oriente a foto de **uma folha só,
  de perto, com fundo liso**.
- O contorno amarelo vem de um mapa de atenção 12x12 ampliado: mostra a região que mais pesou na decisão, de forma
  aproximada, não a forma exata da lesão.
- A rede não recusa fotos que não são de folha de mandioca; só há checagem de tamanho e de luz.

## Licença

Este projeto está licenciado conforme os termos descritos em [LICENSE](LICENSE).
