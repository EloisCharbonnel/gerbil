"""Synthetic photos for the tests: a sherd and a printed checkerboard scale (1 cm squares, two rows),
on a light background or on dark felt (with a paper label). Nothing real: the repository holds no photo."""
import math
import numpy as np
import cv2


def sherd_polygon(cx, cy, r, seed=1, n=11):
    rng = np.random.default_rng(seed)
    angles = np.sort(rng.uniform(0, 2 * math.pi, n))
    radii = r * rng.uniform(0.7, 1.0, n)
    return np.array([[cx + a * math.cos(t), cy + a * math.sin(t)] for a, t in zip(radii, angles)], np.int32)


def scale_image(px_cm, n_cm=10):
    """A checkerboard scale: two rows of 1 cm x 0.5 cm squares, black and white, on a white card."""
    sq_h = int(round(0.5 * px_cm))
    m = int(round(0.15 * px_cm))
    w, h = int(round(n_cm * px_cm)) + 2 * m, 2 * sq_h + 2 * m
    card = np.full((h, w, 3), 245, np.uint8)
    for i in range(n_cm):
        x0, x1 = m + int(round(i * px_cm)), m + int(round((i + 1) * px_cm))
        top = (20, 20, 20) if i % 2 == 0 else (245, 245, 245)
        bottom = (245, 245, 245) if i % 2 == 0 else (20, 20, 20)
        card[m:m + sq_h, x0:x1] = top
        card[m + sq_h:m + 2 * sq_h, x0:x1] = bottom
    # "10 cm" printed in the last white squares of the bottom row, as on real scales (and a learned
    # scale needs such marks: a bare checkerboard repeats itself)
    fs = sq_h / 30
    for i, text in ((n_cm - 4, str(n_cm)), (n_cm - 2, "cm")):              # white squares of the bottom row
        x = m + int(round(i * px_cm)) + int(0.15 * px_cm)
        cv2.putText(card, text, (x, m + 2 * sq_h - int(0.12 * px_cm)), cv2.FONT_HERSHEY_DUPLEX, fs,
                    (20, 20, 20), max(1, int(fs * 2)))
    return card


def photo(px_cm=100.0, dark=False, label=False, size=(2000, 3000), seed=1, shadow=False):
    """(rgb image, sherd mask, px_cm) - the sherd in the upper middle, the scale below it; with
    shadow, the sherd casts a soft shadow down and to the right (light from the upper left)."""
    H, W = size
    rng = np.random.default_rng(seed)
    if dark:
        img = np.full((H, W, 3), (14, 15, 20), np.float32)
    else:
        yy, xx = np.mgrid[0:H, 0:W]
        img = np.dstack([232 - 10 * yy / H, 230 - 8 * xx / W, 226 - 6 * yy / H]).astype(np.float32)
    img += rng.normal(0, 2.0, img.shape)
    mask = np.zeros((H, W), np.uint8)
    cv2.fillPoly(mask, [sherd_polygon(W // 2, int(H * 0.38), int(H * 0.22), seed)], 1)
    if shadow:                                  # darker background, soft edge (penumbra), offset by 0.6 cm
        off = int(0.6 * px_cm)
        sh = np.zeros((H, W), np.float32)
        sh[off:, off:] = mask[:-off, :-off]
        sh = cv2.GaussianBlur(sh, (0, 0), 0.25 * px_cm)
        img *= (1 - 0.35 * sh)[..., None]
    tex = rng.normal(0, 6, (H, W, 1)) + np.array([176, 126, 92], np.float32)
    img = np.where(mask[..., None] > 0, tex, img)
    card = scale_image(px_cm).astype(np.float32)
    y0, x0 = int(H * 0.72), (W - card.shape[1]) // 2
    img[y0:y0 + card.shape[0], x0:x0 + card.shape[1]] = card
    img = np.clip(img, 0, 255).astype(np.uint8)
    if label:
        ly, lx = int(H * 0.12), int(W * 0.08)
        img[ly:ly + int(2.5 * px_cm), lx:lx + int(4 * px_cm)] = (238, 240, 246)
        cv2.putText(img, "QSR-A5/0073", (lx + 20, ly + int(1.4 * px_cm)), cv2.FONT_HERSHEY_SIMPLEX, 1.6,
                    (60, 60, 150), 4)
    return img, mask > 0, px_cm
