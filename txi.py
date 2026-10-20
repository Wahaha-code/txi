"""Enhance one image with the TXI mode 1 and/or mode 2 pipeline."""

import argparse
from dataclasses import replace
from pathlib import Path

import cv2
import numpy as np

from code.txi import PITVIS_CONFIG, TXIConfig, enhance_txi


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="input photograph (PNG, JPEG, TIFF, etc.)")
    parser.add_argument("--mode", choices=("1", "2", "both"), default="both")
    parser.add_argument("--output", type=Path, help="output path when one mode is selected")
    parser.add_argument("--preset", choices=("paper", "pitvis"), default="paper")
    parser.add_argument("--spatial-sigma", type=float)
    parser.add_argument("--range-sigma", type=float)
    parser.add_argument("--tone-gamma", type=float)
    args = parser.parse_args()
    if args.mode == "both" and args.output is not None:
        parser.error("--output requires --mode 1 or --mode 2")

    try:
        raw = cv2.imdecode(np.frombuffer(args.input.read_bytes(), np.uint8),
                           cv2.IMREAD_UNCHANGED)
    except OSError as exc:
        parser.error(str(exc))
    if raw is None:
        parser.error(f"cannot decode image: {args.input}")
    if raw.dtype == np.uint16:
        raw = np.rint(raw.astype(np.float32) / 65535.0 * 255).astype(np.uint8)
    if raw.ndim == 2:
        raw = cv2.cvtColor(raw, cv2.COLOR_GRAY2BGR)
    alpha = None
    if raw.ndim == 3 and raw.shape[2] == 4:
        alpha = raw[:, :, 3].copy()
        raw = cv2.cvtColor(raw, cv2.COLOR_BGRA2BGR)
    if raw.ndim != 3 or raw.shape[2] != 3 or raw.dtype != np.uint8:
        parser.error("supported images are 8/16-bit grayscale, RGB, or RGBA")

    try:
        config = TXIConfig() if args.preset == "paper" else PITVIS_CONFIG
        overrides = {key: value for key, value in {
            "spatial_sigma": args.spatial_sigma,
            "range_sigma": args.range_sigma,
            "tone_gamma": args.tone_gamma,
        }.items() if value is not None}
        mode1, mode2 = enhance_txi(raw, replace(config, **overrides))
    except ValueError as exc:
        parser.error(str(exc))

    outputs = {"1": mode1, "2": mode2}
    selected = ("1", "2") if args.mode == "both" else (args.mode,)
    for mode in selected:
        label = "txi" if args.preset == "paper" else "txi_pitvis"
        path = args.output or args.input.with_name(f"{args.input.stem}_{label}_mode{mode}.png")
        path.parent.mkdir(parents=True, exist_ok=True)
        result = outputs[mode]
        if alpha is not None and path.suffix.lower() == ".png":
            result = np.dstack((result, alpha))
        ok, encoded = cv2.imencode(path.suffix or ".png", result)
        if not ok:
            parser.error(f"cannot encode output: {path}")
        path.write_bytes(encoded.tobytes())
        print(path)


if __name__ == "__main__":
    main()
