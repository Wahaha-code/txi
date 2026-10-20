import unittest

import cv2
import numpy as np

from code.txi import enhance_txi


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


if __name__ == "__main__":
    unittest.main()
