import unittest
from dataclasses import replace

import cv2
import numpy as np

from code.txi import PITVIS_CONFIG, TXIConfig, enhance_txi


class TXITests(unittest.TestCase):
    def test_dark_region_rises_and_bright_region_stays_stable(self):
        image = np.empty((64, 128, 3), dtype=np.uint8)
        image[:, :64] = 30
        image[:, 64:] = 220
        _, mode2 = enhance_txi(image)
        self.assertGreater(int(mode2[32, 20, 0]), 30)
        self.assertLessEqual(abs(int(mode2[32, 100, 0]) - 220), 1)

    def test_mode1_expands_red_pale_lab_difference(self):
        image = np.empty((64, 64, 3), dtype=np.uint8)
        image[:32] = [135, 160, 209]  # approximately Lab a*=15
        image[32:] = [136, 149, 233]  # approximately Lab a*=30
        mode1, mode2 = enhance_txi(image)
        lab1 = cv2.cvtColor(mode1, cv2.COLOR_BGR2LAB)
        lab2 = cv2.cvtColor(mode2, cv2.COLOR_BGR2LAB)
        gap1 = abs(int(lab1[16, 16, 1]) - int(lab1[48, 16, 1]))
        gap2 = abs(int(lab2[16, 16, 1]) - int(lab2[48, 16, 1]))
        self.assertGreater(gap1, gap2)

    def test_black_remains_black(self):
        image = np.zeros((16, 16, 3), dtype=np.uint8)
        mode1, mode2 = enhance_txi(image)
        self.assertEqual(int(mode2.max()), 0)
        self.assertLessEqual(int(mode1.max()), 1)  # Lab round-trip rounding

    def test_noise_floor_limits_flat_area_changes(self):
        rng = np.random.default_rng(7)
        noise = rng.integers(-2, 3, size=(64, 64, 1), dtype=np.int16)
        image = np.clip(100 + noise, 0, 255).astype(np.uint8)
        image = np.repeat(image, 3, axis=2)
        _, paper = enhance_txi(image, replace(TXIConfig(), texture_gain=1.6))
        _, guarded = enhance_txi(image, replace(TXIConfig(), texture_gain=1.6,
                                                detail_noise_floor=0.035))
        paper_delta = np.abs(paper.astype(np.int16) - image.astype(np.int16)).mean()
        guarded_delta = np.abs(guarded.astype(np.int16) - image.astype(np.int16)).mean()
        self.assertLess(guarded_delta, paper_delta)

    def test_surgical_preset_preserves_dark_field_boundary(self):
        image = np.zeros((64, 64, 3), dtype=np.uint8)
        image[8:56, 8:56] = (5, 8, 10)
        image[16:48, 16:48] = (20, 40, 60)
        image[20:24, 20:24] = (200, 200, 200)
        mode1, mode2 = enhance_txi(image, PITVIS_CONFIG)
        self.assertTrue(np.array_equal(mode1[0, 0], image[0, 0]))
        self.assertTrue(np.array_equal(mode2[9, 9], image[9, 9]))
        self.assertFalse(np.array_equal(mode2[32, 32], image[32, 32]))


if __name__ == "__main__":
    unittest.main()
