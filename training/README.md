# Treino da GreenLeaf IA v2

Pipeline que gerou `backend/models/greenleaf_effb0.onnx`: ajuste fino da EfficientNet-B0 (PyTorch + timm) no dataset
[Cassava Leaf Disease Classification](https://www.kaggle.com/competitions/cassava-leaf-disease-classification) com 5 classes
(bacteriose CBB, estria marrom CBSD, mosqueado verde CGM, mosaico CMD, sadia), em duas etapas: 8 épocas em 256 px e
mais 4 épocas em 384 px a partir do melhor modelo de 256 px (em 384 px as manchas pequenas ficam visíveis).

| Arquivo | O que faz |
|---|---|
| `prepare_data.py` | divisão estratificada 80/10/10 (semente 42) em `data/splits.csv` + cache das fotos (288x288 ou `--cache-size`) |
| `train.py` | ajuste fino da rede inteira (GPU AMD via DirectML, ou CPU), pesos por classe e *label smoothing*; `--init` continua de um modelo já treinado |
| `export_onnx.py` | exporta para ONNX com normalização e mapa de atenção (CAM) dentro do grafo, direto em `backend/models/` |
| `evaluate.py` | calibra o limiar na validação (F1) e mede tudo no teste usando o **código do servidor** (`backend/app`) |
| `reports/` | métricas do modelo publicado, matriz de confusão, histórico do treino e exemplos de overlay |

`data/splits.csv` é a divisão usada no modelo publicado: com ela, `evaluate.py` reproduz os números de `reports/metrics.md`.

## Reproduzir

Requisitos: Python 3.11 e o dataset do Kaggle extraído em `../cassava-leaf-disease-classification/` (ao lado do repositório)
ou na pasta indicada pela variável `CASSAVA_DATASET_DIR`.

```bash
python -m venv .venv
.venv/Scripts/pip install torch-directml timm onnx onnxruntime scikit-learn pandas pillow opencv-python-headless matplotlib fastapi "uvicorn[standard]" python-multipart python-dotenv pytest httpx
```

```bash
.venv/Scripts/python training/prepare_data.py
```

```bash
.venv/Scripts/python training/train.py --epochs 8 --img-size 256 --device dml
```

```bash
.venv/Scripts/python training/prepare_data.py --cache-size 448
```

```bash
.venv/Scripts/python training/train.py --init training/models/greenleaf_effb0.pt --img-size 384 --cache-size 448 --epochs 4 --lr 2e-4 --batch-size 12 --val-batch-size 16 --warmup 0.2 --device dml --out greenleaf_effb0_384
```

```bash
.venv/Scripts/python training/export_onnx.py --checkpoint training/models/greenleaf_effb0_384.pt --name greenleaf_effb0_384
```

```bash
.venv/Scripts/python training/evaluate.py --name greenleaf_effb0_384
```

Para publicar, copie `backend/models/greenleaf_effb0_384.onnx` e `.json` por cima de `greenleaf_effb0.onnx` e `.json`
(o nome que a API carrega); a versão do modelo fica registrada dentro do `.json`.

- `--device dml` usa a GPU AMD pelo DirectML (RX 6600: ~16 min por época em 256 px, ~29 min em 384 px); `--device cpu`
  funciona, ~2x mais lento. Em 384 px a GPU de 8 GB só comporta lote 12 (e 16 na validação): com lotes maiores a memória
  transborda para a RAM e o treino fica dezenas de vezes mais lento.
- O AdamW do PyTorch usa uma operação (`lerp`) que o DirectML não tem; por isso `train.py` traz um AdamW equivalente (`SimpleAdamW`).
- `evaluate.py` grava o limiar calibrado no `.json` do modelo, que a API lê ao iniciar. A taxa de manchas pela cor só
  entra na decisão se melhorar o F1 da validação em mais de 0,01 (hoje não melhora: a decisão vem só da rede).
- O cache (`data/cache/`) e os checkpoints (`models/*.pt`) ficam fora do Git.
