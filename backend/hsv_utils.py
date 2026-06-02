"""HSV segmentation helpers for cassava leaf analysis."""

import cv2
import numpy as np


def _keep_relevant_components(mask: np.ndarray, min_area: int) -> np.ndarray:
    components, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype("uint8"), 8)
    cleaned = np.zeros_like(mask, dtype="uint8")

    for label in range(1, components):
        area = stats[label, cv2.CC_STAT_AREA]
        if area >= min_area:
            cleaned[labels == label] = 255

    return cleaned


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
    mask = _keep_relevant_components(mask, min_area)

    return mask.astype(bool)


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
    mask = _keep_relevant_components(mask, min_area)

    return mask.astype(bool)


def classify_severity(ratio: float) -> str:
    if ratio < 0.03:
        return "Leve"
    if ratio < 0.15:
        return "Moderada"
    return "Grave"


def create_overlay(image: np.ndarray, leaf_mask: np.ndarray, infection_mask: np.ndarray) -> np.ndarray:
    overlay = image.copy()
    result = image.copy()

    overlay[leaf_mask] = (87, 184, 70)
    overlay[infection_mask] = (255, 93, 93)

    blended = cv2.addWeighted(overlay, 0.42, result, 0.58, 0)
    result[leaf_mask] = blended[leaf_mask]
    result[infection_mask] = overlay[infection_mask]
    return result
