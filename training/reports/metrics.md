# Resultados — GreenLeaf IA v2

Modelo `greenleaf_effb0-2026-10-28`, conjunto de **teste** com 2140 fotos do Kaggle nunca usadas no treino nem na calibração (divisão estratificada 80/10/10, semente 42). Medido com o mesmo código do servidor.

## Classificação das 5 classes

| Classe | Precisão | Revocação | F1 | Fotos |
|---|---|---|---|---|
| Bacteriose (CBB) | 53.4% | 64.2% | 58.3% | 109 |
| Estria marrom (CBSD) | 73.5% | 82.2% | 77.6% | 219 |
| Mosqueado verde (CGM) | 82.8% | 70.6% | 76.2% | 238 |
| Mosaico (CMD) | 94.9% | 94.8% | 94.9% | 1316 |
| Sadia | 66.7% | 63.6% | 65.1% | 258 |
| **Acurácia global** | | | **85.5%** | |
| **F1 macro** | | | **74.4%** | |

![Matriz de confusão](confusion_matrix.png)

## Bacteriose sim/não (o que o app mostra)

Regra: `probabilidade = 1.0 × P(CBB) + 0.00 × prob. pela cor`, bacteriose se ≥ **0.26** (escolhido por F2 na validação).

| Métrica | GreenLeaf v2 | Regra só por cor (v1) |
|---|---|---|
| Revocação (bacterioses encontradas) | 78.0% | 96.3% |
| Precisão (alarmes corretos) | 48.3% | 5.3% |
| Especificidade (não-bacterioses descartadas) | 95.5% | 7.9% |
| F1 | 59.6% | 10.1% |
| Acurácia | 94.6% | 12.4% |
| AUC ROC | 91.9% | 59.6% |
| Verdadeiros positivos / falsos negativos | 85 / 24 | 105 / 4 |
| Falsos positivos / verdadeiros negativos | 91 / 1940 | 1870 / 161 |

Tempo médio por foto em CPU (rede + cor, sem rede de celular): **43 ms**.

A severidade (Leve/Moderada/Grave) vem da taxa de manchas medida pela cor; o dataset não tem rótulo de severidade,
então ela não entra nestas métricas.
