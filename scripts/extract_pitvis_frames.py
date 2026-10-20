"""Extract evenly spaced, unlabeled frames from a local PitVis MP4 video."""

import argparse
import csv
from pathlib import Path

import cv2
import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--source-doi", default="10.5522/04/26531686.v3")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")

    video = cv2.VideoCapture(str(args.video))
    if not video.isOpened():
        parser.error(f"cannot open video: {args.video}")
    try:
        total = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = video.get(cv2.CAP_PROP_FPS)
        if total < args.count or fps <= 0:
            parser.error("video has too few frames or invalid FPS")

        # Sample the interior of the video, avoiding opening/closing slates.
        indices = np.rint(np.linspace(0.05, 0.95, args.count) * (total - 1)).astype(int)
        if len(set(indices)) != args.count:
            parser.error("sampling produced duplicate frame indices")
        args.output_dir.mkdir(parents=True, exist_ok=True)

        rows = []
        for index in indices:
            video.set(cv2.CAP_PROP_POS_FRAMES, int(index))
            ok, frame = video.read()
            if not ok:
                raise RuntimeError(f"could not decode frame {index}")
            name = f"{args.video.stem}_frame_{index:06d}.png"
            path = args.output_dir / name
            if not cv2.imwrite(str(path), frame):
                raise RuntimeError(f"could not write {path}")
            rows.append({"file": name, "source_video": args.video.name,
                         "source_doi": args.source_doi, "frame_index": int(index),
                         "timestamp_s": f"{index / fps:.3f}",
                         "width": frame.shape[1], "height": frame.shape[0]})
            print(f"{path}  t={index / fps:.3f}s", flush=True)

        with (args.output_dir / "manifest.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    finally:
        video.release()


if __name__ == "__main__":
    main()
