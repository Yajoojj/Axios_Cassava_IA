"""Recorte da folha analisada e do mapa de atenção (issue #7): fundo não vira folha nem mancha."""

from __future__ import annotations

import numpy as np

from app.hsv import around, convex_region, main_leaf_region
from app.model import attention_mask


def disk(shape, cx, cy, r):
    yy, xx = np.mgrid[0 : shape[0], 0 : shape[1]]
    return (xx - cx) ** 2 + (yy - cy) ** 2 <= r**2


def test_corner_cells_do_not_become_attention():
    cam = np.zeros((8, 8), dtype=np.float32)
    cam[0, 0] = cam[7, 7] = 1.0  # artefato de borda, mais forte que a lesão
    cam[4, 4] = 0.6
    mask = attention_mask(cam, (256, 256))
    assert mask[128:160, 128:160].any()
    assert not mask[:16, :16].any() and not mask[-16:, -16:].any()


def test_attention_keeps_only_the_region_around_the_peak():
    cam = np.zeros((8, 8), dtype=np.float32)
    cam[2, 2] = 1.0
    cam[5, 5] = 0.9
    mask = attention_mask(cam, (256, 256))
    assert mask[80, 80] and not mask[176, 176]


def test_main_leaf_is_the_one_the_network_looked_at():
    shape = (200, 300)
    big_background_leaf = disk(shape, 60, 100, 55)
    analysed_leaf = disk(shape, 230, 100, 40)
    focus = disk(shape, 230, 100, 25)
    region = main_leaf_region(big_background_leaf | analysed_leaf, focus)
    assert region[100, 230] and not region[100, 60]


def test_main_leaf_without_attention_is_the_largest():
    shape = (200, 300)
    region = main_leaf_region(disk(shape, 60, 100, 55) | disk(shape, 230, 100, 30))
    assert region[100, 60] and not region[100, 230]


def test_leaf_region_is_filled_and_lesions_on_the_edge_still_count():
    shape = (200, 200)
    leaf = disk(shape, 100, 100, 60) & ~disk(shape, 100, 100, 15)  # mancha no meio: buraco no verde
    region = main_leaf_region(leaf)
    assert region[100, 100]
    assert around(region, 0.03)[100, 163]  # ponta necrosada logo fora do verde
    assert not around(region, 0.03)[100, 190]


def test_convex_region_is_smooth_hull():
    shape = (200, 200)
    lobes = disk(shape, 60, 100, 30) | disk(shape, 140, 100, 30) | (np.abs(np.mgrid[0:200, 0:200][0] - 100) < 4)
    hull = convex_region(lobes)
    assert hull[80, 100] and not lobes[80, 100]
