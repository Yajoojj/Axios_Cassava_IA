"""Funções utilitárias para segmentação em HSV e criação de sobreposições.

Estas rotinas isolam a região da folha usando thresholds de cor no espaço
HSV e identificam áreas potencialmente infectadas. Também fornecem
funções para calcular a severidade da infecção e para gerar uma imagem
com sobreposição de cores (verde para tecido saudável e vermelho para
regiões infectadas).
"""

import numpy as np
import cv2


def segment_leaf(image: np.ndarray) -> np.ndarray:
    """Segmenta a folha na imagem usando thresholds no espaço HSV.

    A função assume que a folha apresenta tonalidades de verde, enquanto o
    fundo possui cores distintas (solo, céu). Converte a imagem para HSV
    e aplica thresholds em H, S e V para isolar a área da folha. Em
    seguida, aplica operações morfológicas para refinar a máscara.

    Args:
        image: array NumPy no formato BGR (OpenCV) ou RGB convertido.

    Returns:
        Máscara binária booleana com `True` nas regiões da folha.
    """
    # Converte para HSV (OpenCV espera BGR por padrão, mas nossa imagem é RGB)
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    # Define intervalos de cor para verde (valores aproximados)
    lower_green = np.array([20, 40, 40])
    upper_green = np.array([100, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)
    # Remove ruídos com abertura e fechamento
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    # Converte para booleano
    return mask.astype(bool)


def segment_infection(image: np.ndarray) -> np.ndarray:
    """Segmenta áreas possivelmente infectadas usando thresholds HSV.

    Esta rotina tenta isolar regiões com tonalidades amareladas a marrons
    saturadas, que são típicas de lesões bacterianas. Para reduzir
    falsos positivos causados por solo, galhos ou sombra, utilizamos
    thresholds mais restritivos em saturação e valor. Esses limites
    foram calibrados empiricamente para exigir maior saturação (≥120) e
    brilho moderado (≥50), melhorando a precisão da máscara de infecção.

    Args:
        image: array NumPy no formato RGB.

    Returns:
        Máscara binária booleana indicando pixels suspeitos de infecção.
    """
    # Converte a imagem para HSV para facilitar a segmentação por cor
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    # Intervalo de cores para tons amarelados/marrons com alta saturação
    # e brilho. Ajustes mais estreitos ajudam a evitar a detecção de
    # áreas neutras ou pálidas que não representam infecção.
    lower_inf = np.array([10, 120, 50])
    upper_inf = np.array([50, 255, 255])
    mask = cv2.inRange(hsv, lower_inf, upper_inf)
    # Aplica operações morfológicas para remover pequenos ruídos e
    # preencher buracos nas regiões detectadas.
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask.astype(bool)


def classify_severity(ratio: float) -> str:
    """Classifica a severidade da infecção a partir da proporção infectada.

    Args:
        ratio: fração da área da folha que está infectada (0 a 1).

    Returns:
        Uma string representando a severidade: 'Leve', 'Moderada' ou 'Grave'.
    """
    if ratio < 0.1:
        return "Leve"
    elif ratio < 0.25:
        return "Moderada"
    else:
        return "Grave"


def create_overlay(image: np.ndarray, leaf_mask: np.ndarray, infection_mask: np.ndarray) -> np.ndarray:
    """Gera uma imagem com sobreposição verde/vermelha indicando regiões.

    Os pixels da folha serão coloridos de verde, enquanto as regiões
    infectadas serão coloridas de vermelho. A cor original é preservada
    apenas em áreas fora da folha.

    Args:
        image: imagem original em formato RGB.
        leaf_mask: máscara booleana para a folha.
        infection_mask: máscara booleana para regiões infectadas.

    Returns:
        Uma imagem RGB com dimensões iguais à original e sobreposição aplicada.
    """
    # Copia para não modificar a original e converte para BGR para OpenCV
    overlay = image.copy()
    # Define cores em BGR (pois usaremos cv2 para desenhar)
    green = (0, 255, 0)
    red = (255, 0, 0)
    # Aplica cor verde na folha
    overlay[leaf_mask] = green
    # Aplica cor vermelha nas regiões infectadas
    overlay[infection_mask] = red
    return overlay
