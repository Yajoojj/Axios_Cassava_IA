"""Servidor FastAPI para detecção de bacteriose em folhas de mandioca.

Este módulo define o endpoint `/predict` que recebe uma imagem de folha via
upload multipart, carrega um modelo EfficientNet previamente treinado,
processa a imagem para gerar a probabilidade de infecção e também calcula
a proporção e severidade da área infectada usando segmentação no espaço
HSV. A resposta inclui uma sobreposição colorida em base64 para fácil
visualização na interface web.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import numpy as np
from PIL import Image
import cv2
import base64
from io import BytesIO
import os

from model_utils_dl import load_trained_model, preprocess_image
from hsv_utils import segment_leaf, segment_infection, classify_severity, create_overlay


# Instanciação da aplicação FastAPI
app = FastAPI(title="Cassava Blight Detection API", version="1.0.0")

# Configuração de CORS para permitir requisições de qualquer origem.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique domínios confiáveis
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Caminho padrão do modelo. Altere se necessário.
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "cassava_effnet.h5")

# Carregamento do modelo. Caso o arquivo não exista, a função
# `load_trained_model` construirá um modelo novo com pesos ImageNet.
try:
    model = load_trained_model(MODEL_PATH)
except Exception as exc:
    # Se houver erro ao carregar, levante exceção informativa.
    raise RuntimeError(f"Erro ao carregar o modelo em {MODEL_PATH}: {exc}")


@app.post("/predict")
async def predict(image: UploadFile = File(...)) -> JSONResponse:
    """Recebe uma imagem de folha e retorna a predição de infecção.

    Parâmetros:
        image (UploadFile): arquivo da imagem enviado via formulário.

    Retorna:
        JSONResponse: dicionário com probabilidade, classe prevista,
        proporção de área infectada, severidade e overlay em base64.
    """
    # Verifica se o conteúdo é uma imagem compatível.
    if image.content_type not in {"image/jpeg", "image/png", "image/jpg"}:
        raise HTTPException(status_code=400, detail="Formato de imagem não suportado.")

    # Lê o conteúdo do arquivo enviado
    contents = await image.read()
    try:
        pil_image = Image.open(BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Não foi possível abrir a imagem enviada.")

    # Converte para array NumPy para segmentação
    np_image = np.array(pil_image)

    # Pré-processa a imagem para o modelo (redimensiona, normaliza)
    input_tensor = preprocess_image(pil_image)

    # Realiza a predição com o modelo profundo (TensorFlow). A saída é uma
    # lista [[probabilidade]] representando a confiança de infecção. Contudo,
    # modelos recém-treinados ou com poucos dados podem tender a ficar perto
    # de 0,5 para muitas imagens, fornecendo pouca distinção. Para aumentar
    # a sensibilidade, combinaremos essa probabilidade com a proporção de
    # infecção calculada via segmentação HSV (veja abaixo).
    preds = model.predict(input_tensor)
    probability_model = float(preds[0][0])

    # Segmentação da folha e da infecção em HSV
    leaf_mask = segment_leaf(np_image)
    infection_mask = segment_infection(np_image)
    # Mantém somente as regiões infectadas dentro da folha
    infection_mask = np.logical_and(leaf_mask, infection_mask)

    # Cálculo da proporção de área infectada (evita divisão por zero)
    total_leaf_pixels = float(leaf_mask.sum()) if leaf_mask.sum() > 0 else 1.0
    ratio = float(infection_mask.sum() / total_leaf_pixels)

    # Classificação da severidade com base na proporção
    severity = classify_severity(ratio)

    # ------------------------------------------------------------------
    # Combinação de probabilidades: modelo + segmentação HSV
    #
    # Para gerar uma probabilidade final mais estável, calculamos a média
    # ponderada entre a probabilidade prevista pelo modelo (probability_model)
    # e a proporção de área infectada (ratio). Essa média equaliza a influência
    # de cada componente e evita que o modelo domine completamente o resultado
    # quando seus pesos ainda não estão bem ajustados. O peso 0.5 é escolhido
    # empiricamente, mas pode ser ajustado conforme a performance.
    probability = 0.5 * probability_model + 0.5 * ratio

    # Definição da classe final:
    # - Se a severidade for Moderada ou Grave (identificada pela segmentação),
    #   forçamos a classe "Infectado". Isso dá maior confiança quando a
    #   segmentação detectar lesões extensas.
    # - Caso contrário, usamos a probabilidade combinada: se >= 0.3, "Infectado",
    #   senão "Saudável". O limiar 0.3 é menos conservador que 0.5, permitindo
    #   detectar infecções mais cedo, uma prática recomendada para monitoramento
    #   de doenças em campo【301892444382090†screenshot】.
    if severity in ("Moderada", "Grave") or probability >= 0.3:
        predicted_class = "Infectado"
    else:
        predicted_class = "Saudável"

    # Gera a imagem de sobreposição colorida
    overlay_image = create_overlay(np_image, leaf_mask, infection_mask)

    # Codifica a sobreposição em PNG e depois para base64
    success, buffer = cv2.imencode(".png", overlay_image)
    if not success:
        raise HTTPException(status_code=500, detail="Erro ao gerar overlay da imagem.")
    encoded_overlay = base64.b64encode(buffer).decode("utf-8")

    return JSONResponse(
        content={
            "probability": probability,
            "class": predicted_class,
            "ratio": ratio,
            "severity": severity,
            "overlay": f"data:image/png;base64,{encoded_overlay}",
        }
    )
