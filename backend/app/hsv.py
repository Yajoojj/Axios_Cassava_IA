"""Segmentação cromática (HSV) da folha e das manchas, severidade e imagem de sobreposição.

Vem do Axios Cassava IA (backend/hsv_utils.py), com duas mudanças:
- o overlay é devolvido em RGB e convertido para BGR só na hora de codificar o PNG
  (o servidor antigo mandava RGB para o cv2.imencode e as lesões saíam azuis);
- o overlay pode receber o mapa de atenção da rede e desenhar o contorno da região
  que mais pesou no diagnóstico.
"""

from __future__ import annotations

import cv2
import numpy as np

LEAF_RGB = (87, 184, 70)
LESION_RGB = (255, 93, 93)
ATTENTION_RGB = (242, 177, 52)


def _keep_relevant_components(mask: np.ndarray, min_area: int) -> np.ndarray:
    components, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype("uint8"), 8)
    keep = np.zeros(components, dtype=bool)
    keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= min_area
    return keep[labels]


def segment_leaf(image: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    rgb = image.astype(np.int16)

    hsv_mask = cv2.inRange(hsv, np.array([24, 45, 35]), np.array([96, 255, 245]))
    green_dominance = (
        (rgb[:, :, 1] > rgb[:, :, 0] + 8)
        & (rgb[:, :, 1] > rgb[:, :, 2] + 8)
        & (rgb[:, :, 1] > 45)
    )
    mask = np.logical_and(hsv_mask > 0, green_dominance).astype("uint8") * 255

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    min_area = max(80, int(image.shape[0] * image.shape[1] * 0.002))
    return _keep_relevant_components(mask, min_area)


def segment_infection(image: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    rgb = image.astype(np.int16)

    yellow_brown = cv2.inRange(hsv, np.array([8, 90, 45]), np.array([45, 255, 235]))
    necrotic_dark = cv2.inRange(hsv, np.array([0, 35, 20]), np.array([35, 180, 125]))
    color_mask = np.logical_or(yellow_brown > 0, necrotic_dark > 0)

    not_healthy_green = ~(
        (rgb[:, :, 1] > rgb[:, :, 0] + 12)
        & (rgb[:, :, 1] > rgb[:, :, 2] + 12)
        & (hsv[:, :, 1] > 60)
    )
    mask = np.logical_and(color_mask, not_healthy_green).astype("uint8") * 255

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    min_area = max(20, int(image.shape[0] * image.shape[1] * 0.0003))
    return _keep_relevant_components(mask, min_area)


def lesion_ratio(image: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
    """Fração da folha coberta por manchas, com as máscaras da folha e das manchas.

    As manchas contam como parte da folha: uma folha muito necrosada perde o verde
    e, sem isso, a taxa passaria de 100%.
    """
    leaf = segment_leaf(image)
    lesions = segment_infection(image)
    # Manchas só contam se estiverem sobre a folha ou encostadas nela.
    near_leaf = cv2.dilate(leaf.astype("uint8"), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))) > 0
    lesions = lesions & near_leaf
    leaf_area = float((leaf | lesions).sum())
    ratio = float(lesions.sum()) / leaf_area if leaf_area > 0 else 0.0
    return ratio, leaf, lesions


def main_leaf_region(leaf: np.ndarray, focus: np.ndarray | None = None) -> np.ndarray:
    """Região preenchida da folha analisada; outras folhas, mato seco e solo ao fundo ficam de fora.

    Entre os componentes verdes, escolhe o que mais se sobrepõe à região em que a rede se apoiou
    (`focus`) ou, sem ela, o maior. O contorno externo é preenchido para que as manchas dentro da
    folha (que não são verdes) façam parte dela.
    """
    components, labels, stats, _ = cv2.connectedComponentsWithStats(leaf.astype("uint8"), 8)
    if components <= 1:
        return np.zeros(leaf.shape, dtype=bool)
    score = stats[:, cv2.CC_STAT_AREA].astype(np.float64)
    if focus is not None:
        overlap = np.bincount(labels[focus], minlength=components).astype(np.float64)
        if overlap[1:].max() > 0:
            score = overlap
    score[0] = -1
    best = (labels == int(np.argmax(score))).astype("uint8")
    contours, _ = cv2.findContours(best, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    region = np.zeros(leaf.shape, dtype="uint8")
    cv2.drawContours(region, contours, -1, 1, cv2.FILLED)
    return region > 0


def around(region: np.ndarray, fraction: float) -> np.ndarray:
    """A região mais uma faixa de `fraction` do lado maior da imagem (ponta necrosada fora do verde)."""
    k = max(3, round(max(region.shape) * fraction)) | 1
    return cv2.dilate(region.astype("uint8"), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))) > 0


def convex_region(region: np.ndarray) -> np.ndarray:
    """Envoltória convexa da região: recorte suave, sem seguir cada lóbulo da folha."""
    points = cv2.findNonZero(region.astype("uint8"))
    hull = np.zeros(region.shape, dtype="uint8")
    if points is not None:
        cv2.fillConvexPoly(hull, cv2.convexHull(points), 1)
    return hull > 0


def classify_severity(ratio: float) -> str:
    if ratio < 0.03:
        return "Leve"
    if ratio < 0.15:
        return "Moderada"
    return "Grave"


def create_overlay(
    image: np.ndarray,
    leaf_mask: np.ndarray,
    lesion_mask: np.ndarray,
    attention_mask: np.ndarray | None = None,
) -> np.ndarray:
    """Folha em verde translúcido, manchas em vermelho e, se houver, contorno amarelo da atenção da rede."""
    overlay = image.copy()
    overlay[leaf_mask] = LEAF_RGB
    overlay[lesion_mask] = LESION_RGB
    blended = cv2.addWeighted(overlay, 0.42, image, 0.58, 0)

    result = image.copy()
    result[leaf_mask] = blended[leaf_mask]
    result[lesion_mask] = overlay[lesion_mask]

    if attention_mask is not None and attention_mask.any():
        contours, _ = cv2.findContours(attention_mask.astype("uint8"), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        thickness = max(2, round(max(image.shape[:2]) / 250))
        cv2.drawContours(result, contours, -1, ATTENTION_RGB, thickness, lineType=cv2.LINE_AA)
    return result


def encode_jpeg_data_url(rgb_image: np.ndarray, quality: int = 85) -> str:
    """JPEG em vez de PNG: ~10x menor, o que pesa no tempo de resposta em rede móvel."""
    import base64

    ok, buffer = cv2.imencode(".jpg", cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise ValueError("Falha ao codificar o overlay.")
    return "data:image/jpeg;base64," + base64.b64encode(buffer.tobytes()).decode("ascii")
