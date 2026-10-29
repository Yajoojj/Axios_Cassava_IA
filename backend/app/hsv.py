"""Segmentação cromática (HSV) da folha e das manchas, severidade e imagem de sobreposição.

Vem do Axios Cassava IA (backend/hsv_utils.py), com mudanças:
- amarelo é folha, não mancha: só necrose (marrom, escuro, acinzentado) conta como lesão;
- o overlay é devolvido em RGB e convertido para BGR só na hora de codificar o JPEG
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


def _channels(image: np.ndarray):
    rgb = image.astype(np.float32)
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV).astype(np.int16)
    return rgb[..., 0], rgb[..., 1], rgb[..., 2], hsv[..., 0], hsv[..., 1], hsv[..., 2]


def segment_leaf(image: np.ndarray) -> np.ndarray:
    """Tecido de folha: verde e também amarelo.

    Amarelo (clorose do mosaico, folha velha ou sem nutriente) continua sendo folha, não lesão de
    bacteriose. Contá-lo como mancha pintava de vermelho folhas amareladas inteiras.
    """
    r, g, b, h, s, v = _channels(image)
    green = (h >= 24) & (h <= 96) & (s >= 45) & (v >= 35) & (v <= 245) & (g > r + 8) & (g > b + 8) & (g > 45)
    yellow = (g >= 0.80 * r) & (g <= r + 8) & (r >= 110) & (b <= 0.72 * g) & (s >= 70) & (h >= 15) & (h <= 40)
    mask = (green | yellow).astype("uint8") * 255

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    min_area = max(80, int(image.shape[0] * image.shape[1] * 0.002))
    return _keep_relevant_components(mask, min_area)


def fill_small_holes(mask: np.ndarray, max_hole: int) -> np.ndarray:
    """Preenche buracos de até `max_hole` px (manchas dentro da folha); os maiores são fundo entre folhas."""
    _, labels, stats, _ = cv2.connectedComponentsWithStats((~mask).astype("uint8"), 4)
    x, y, w, h, area = stats.T
    height, width = mask.shape
    fill = ~((x == 0) | (y == 0) | (x + w == width) | (y + h == height)) & (area <= max_hole)
    fill[0] = False
    return mask | fill[labels]


def segment_lesions(image: np.ndarray, leaf: np.ndarray) -> np.ndarray:
    """Necrose: marrom ou marrom-arroxeado dentro do contorno da folha; escuro ou acinzentado em buracos dela.

    Sombras, solo e galhos ao lado da folha não entram: o contorno é o da folha "fechada"
    (fechamento morfológico), que cobre as mordidas de necrose na borda sem avançar sobre o fundo.
    """
    area = image.shape[0] * image.shape[1]
    inside = fill_small_holes(leaf, int(area * 0.01))
    r, g, b, h, s, v = _channels(image)
    petiole = (h >= 140) & (s > 120)  # pecíolo vermelho/roxo da mandioca
    brown = (g < 0.80 * r) & (b < g) & (r >= 50) & (s >= 60) & (v <= 225) & (h <= 25)
    purple_brown = ((h >= 160) | (h <= 8)) & (r > g + 15) & (s >= 35) & (s <= 150) & (v >= 40) & (v <= 200) & ~petiole
    dark = (v >= 15) & (v < 95) & (g <= r + 4) & (b <= g + 6) & (s >= 30)
    grey_tan = (r >= g) & (b <= g) & (s < 90) & (v >= 50) & (v <= 210)
    k = max(3, round(max(image.shape[:2]) * 0.03)) | 1
    outline = cv2.morphologyEx(inside.astype("uint8"), cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))) > 0
    mask = ((brown | purple_brown) & outline) | ((dark | grey_tan) & inside & ~leaf)
    mask = mask.astype("uint8") * 255

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return _keep_relevant_components(mask, max(20, int(area * 0.0003)))


def lesion_ratio(image: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
    """Fração da folha coberta por necrose, com as máscaras da folha e das manchas.

    A área da folha inclui as manchas e os buracos pequenos dentro dela: uma folha muito
    necrosada perde o verde e, sem isso, a taxa passaria de 100%.
    """
    leaf = segment_leaf(image)
    lesions = segment_lesions(image, leaf)
    leaf_area = fill_small_holes(leaf, int(image.shape[0] * image.shape[1] * 0.01)) | lesions
    total = float(leaf_area.sum())
    ratio = float(lesions.sum()) / total if total > 0 else 0.0
    return ratio, leaf_area & ~lesions, lesions


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
