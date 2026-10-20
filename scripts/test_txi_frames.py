"""Run TXI mode 1 and mode 2 on every PNG frame in a directory."""

import argparse
import csv
from pathlib import Path
import sys

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from code.txi import PITVIS_CONFIG, TXIConfig, enhance_txi


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--preset", choices=("paper", "pitvis"), default="paper")
    args = parser.parse_args()

    frames = sorted(args.input_dir.glob("video_*_frame_*.png"))
    if not frames:
        parser.error(f"no video frames found in {args.input_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = args.input_dir / "manifest.csv"
    metadata = {}
    if metadata_path.exists():
        with metadata_path.open(newline="", encoding="utf-8") as stream:
            metadata = {row["file"]: row for row in csv.DictReader(stream)}

    rows = []
    strips = []
    config = TXIConfig() if args.preset == "paper" else PITVIS_CONFIG
    for path in frames:
        source = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if source is None:
            raise RuntimeError(f"cannot read {path}")
        mode1, mode2 = enhance_txi(source, config)
        names = [f"{path.stem}_mode1.png", f"{path.stem}_mode2.png"]
        for image, name in zip((mode1, mode2), names):
            out = args.output_dir / name
            if not cv2.imwrite(str(out), image):
                raise RuntimeError(f"cannot write {out}")
            check = cv2.imread(str(out), cv2.IMREAD_COLOR)
            if check is None or check.shape != source.shape:
                raise RuntimeError(f"output verification failed: {out}")

        # Difference is measured within the visible field, excluding black border.
        visible = source.max(axis=2) > 20
        source_luma = cv2.cvtColor(source, cv2.COLOR_BGR2GRAY)
        dark = visible & (source_luma <= np.percentile(source_luma[visible], 25))
        # Only compare gradients inside tissue, away from the circular border.
        interior = cv2.erode(visible.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
        reference_grad = cv2.Laplacian(source_luma.astype(np.float32), cv2.CV_32F)
        textured = interior & (np.abs(reference_grad) > 3)

        def mean_change(result):
            difference = np.abs(result.astype(np.int16) - source.astype(np.int16))
            return round(float(difference[visible].mean()), 3) if visible.any() else 0.0

        def quality_indicators(result):
            result_luma = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
            dark_gain = (np.median(result_luma[dark].astype(np.float32) -
                                   source_luma[dark]) if dark.any() else 0)
            newly_clipped = visible & (source.max(axis=2) < 250) & (
                result.max(axis=2) >= 250)
            clipping_percent = 100 * newly_clipped.sum() / max(visible.sum(), 1)
            result_grad = cv2.Laplacian(result_luma.astype(np.float32), cv2.CV_32F)
            gradient_ratio = (np.mean(np.abs(result_grad[textured])) /
                              np.mean(np.abs(reference_grad[textured]))
                              if textured.any() else 1)
            return (round(float(dark_gain), 3), round(float(clipping_percent), 3),
                    round(float(gradient_ratio), 3))

        m1_dark, m1_clip, m1_grad = quality_indicators(mode1)
        m2_dark, m2_clip, m2_grad = quality_indicators(mode2)

        rows.append({"source": path.name,
                     "preset": args.preset,
                     "timestamp_s": metadata.get(path.name, {}).get("timestamp_s", ""),
                     "mode1": names[0], "mode2": names[1],
                     "mode1_mean_abs_change": mean_change(mode1),
                     "mode2_mean_abs_change": mean_change(mode2),
                     "mode1_dark_luma_gain": m1_dark,
                     "mode2_dark_luma_gain": m2_dark,
                     "mode1_new_clipping_percent": m1_clip,
                     "mode2_new_clipping_percent": m2_clip,
                     "mode1_gradient_ratio": m1_grad,
                     "mode2_gradient_ratio": m2_grad})

        previews = [cv2.resize(image, (384, 216), interpolation=cv2.INTER_AREA)
                    for image in (source, mode1, mode2)]
        strip = np.concatenate(previews, axis=1)
        cv2.putText(strip, path.stem.rsplit("_", 1)[-1], (8, 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        strips.append(strip)
        print(f"{path.name} -> {names[0]}, {names[1]}", flush=True)

    with (args.output_dir / "results.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    header = np.zeros((48, 1152, 3), dtype=np.uint8)
    for column, label in enumerate(("Original", "TXI mode 1", "TXI mode 2")):
        cv2.putText(header, label, (column * 384 + 12, 33),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
    overview = np.concatenate([header, *strips], axis=0)
    if not cv2.imwrite(str(args.output_dir / "comparison.png"), overview):
        raise RuntimeError("cannot write comparison.png")


if __name__ == "__main__":
    main()
