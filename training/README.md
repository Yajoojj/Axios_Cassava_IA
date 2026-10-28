# Treino da GreenLeaf IA v2

Pipeline que gerou `backend/models/greenleaf_effb0.onnx`: ajuste fino da EfficientNet-B0 (PyTorch + timm) no dataset
[Cassava Leaf Disease Classification](https://www.kaggle.com/competitions/cassava-leaf-disease-classification) com 5 classes
(bacteriose CBB, estria marrom CBSD, mosqueado verde CGM, mosaico CMD, sadia).

| Arquivo | O que faz |
|---|---|
| `prepare_data.py` | divisão estratificada 80/10/10 (semente 42) em `data/splits.csv` + cache das fotos em 288x288 |
| `train.py` | ajuste fino da rede inteira (GPU AMD via DirectML, ou CPU), pesos por classe e *label smoothing* |
| `export_onnx.py` | exporta para ONNX com normalização e mapa de atenção (CAM) dentro do grafo, direto em `backend/models/` |
| `evaluate.py` | calibra peso/limiar na validação e mede tudo no teste usando o **código do servidor** (`backend/app`) |
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
.venv/Scripts/python training/export_onnx.py
```

```bash
.venv/Scripts/python training/evaluate.py
```

- `--device dml` usa a GPU AMD pelo DirectML (~16 min por época numa RX 6600); `--device cpu` funciona, ~2x mais lento.
- O AdamW do PyTorch usa uma operação (`lerp`) que o DirectML não tem; por isso `train.py` traz um AdamW equivalente (`SimpleAdamW`).
- `evaluate.py` grava o limiar calibrado em `backend/models/greenleaf_effb0.json`, que a API lê ao iniciar.
- O cache (`data/cache/`) e os checkpoints (`models/*.pt`) ficam fora do Git.
