"""Practical implementation of Sato et al.'s six-stage TXI pipeline.

Input and output arrays are uint8 BGR images. The paper does not disclose its
bilateral-filter settings, highlight detector, or device tone curve; these are
explicit, adjustable approximations here rather than vendor-identical settings.
"""

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class TXIConfig:
    spatial_sigma: float = 15.0
    range_sigma: float = 0.12
    brightness_threshold: float = 0.25
    brightness_alpha: float = 1.0 / 1.4
    texture_gain: float = 1.2
    tone_gamma: float = 1.0
    highlight_min: float = 0.82
    highlight_max: float = 0.95
    color_knee: float = 15.0
    color_knee_output: float = 5.0
    color_end: float = 30.0


# A visibly stronger, exploratory setting for PitVis surgical video frames.
# It is not a parameter set reported by Sato et al. or validated clinically.
PITVIS_CONFIG = TXIConfig(
    spatial_sigma=25.0,
    range_sigma=0.22,
    brightness_threshold=0.45,
    brightness_alpha=0.60,
    texture_gain=1.60,
    color_knee=20.0,
    color_knee_output=8.0,
    color_end=45.0,
)


def enhance_txi(image_bgr: np.ndarray, config: TXIConfig = TXIConfig()) -> tuple[np.ndarray, np.ndarray]:
    """Return (mode1, mode2) uint8 BGR images.

    Mode 2 enhances illumination and texture. Mode 1 additionally expands
    pale-versus-red contrast in CIE Lab a* using the paper's polygonal curve.
    """
    if image_bgr.ndim != 3 or image_bgr.shape[2] != 3 or image_bgr.dtype != np.uint8:
        raise ValueError("image_bgr must be an H x W x 3 uint8 BGR array")
    if min(image_bgr.shape[:2]) < 2:
        raise ValueError("image must be at least 2 x 2 pixels")
    if not (config.spatial_sigma > 0 and config.range_sigma > 0
            and 0 < config.brightness_threshold <= 1
            and 0 < config.brightness_alpha <= 1
            and config.texture_gain >= 1 and config.tone_gamma > 0
            and 0 < config.color_knee_output < config.color_knee < config.color_end):
        raise ValueError("invalid TXI parameters")

    source = image_bgr.astype(np.float32) / 255.0

    # (1)-(6): edge-preserving SSR base/detail split. Small neutral-white
    # specular pixels go into the base so the detail gain cannot enlarge them.
    base = cv2.bilateralFilter(source, d=0,
                               sigmaColor=config.range_sigma,
                               sigmaSpace=config.spatial_sigma)
    brightest = source.max(axis=2)
    dimmest = source.min(axis=2)
    highlights = (brightest >= config.highlight_max) & (dimmest >= config.highlight_min)
    base[highlights] = source[highlights]

    # (7)-(9): raise only dark base values; use one gain for all channels.
    base_max = base.max(axis=2)
    # The paper sets h to one quarter of the input image's maximum value.
    h = max(config.brightness_threshold * float(source.max()), 1e-6)
    target_max = np.where(base_max < h,
                          h * np.power(np.maximum(base_max, 0) / h,
                                       config.brightness_alpha),
                          base_max)
    gain = np.divide(target_max, base_max, out=np.ones_like(base_max),
                     where=base_max > 1e-6)
    corrected_base = base * gain[..., None]

    # (10): the device tone curve is unknown; identity is the safe default
    # for already-rendered photographs. Gamma can be adjusted by the caller.
    mapped_base = np.power(np.clip(corrected_base, 0, 1), config.tone_gamma)

    # (11)-(12): D = I/B, D' = D^g, O2 = mapped_base * D'. Work in log
    # space for numerical stability; exact black pixels stay black.
    floor = 1.0 / 255.0
    log_detail = np.log(np.maximum(source, floor)) - np.log(np.maximum(base, floor))
    log_detail[highlights] = 0.0
    mode2 = mapped_base * np.exp(config.texture_gain * log_detail)
    mode2[source == 0] = 0
    mode2 = np.clip(mode2, 0, 1).astype(np.float32)

    # (13)-(16): polygonal a* mapping. Paper default: (0,0), (15,5),
    # (30,30), then identity. The PitVis preset broadens this interval.
    lab = cv2.cvtColor(cv2.cvtColor(mode2, cv2.COLOR_BGR2RGB), cv2.COLOR_RGB2LAB)
    a = lab[:, :, 1]
    s1, t1, s2 = config.color_knee, config.color_knee_output, config.color_end
    lab[:, :, 1] = np.where((a >= 0) & (a < s1), a * t1 / s1,
                            np.where((a >= s1) & (a < s2),
                                     t1 + (a - s1) * (s2 - t1) / (s2 - s1), a))
    mode1 = cv2.cvtColor(cv2.cvtColor(lab, cv2.COLOR_LAB2RGB), cv2.COLOR_RGB2BGR)
    return (_to_u8(mode1), _to_u8(mode2))


def _to_u8(image: np.ndarray) -> np.ndarray:
    return np.rint(np.clip(image, 0, 1) * 255).astype(np.uint8)
