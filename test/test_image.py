from unittest import TestCase

import cv2
import numpy as np

from app.utils import filepath
from app.utils.image import to_nddarray


class Test(TestCase):
    def test_to_nddarray(self):
        path_to_image = filepath.path("samples/test_image.png")
        img = open(path_to_image, "rb")
        nddarray1 = to_nddarray(img)
        nddarray2 = cv2.imread(path_to_image)
        self.assertTrue(
            np.all(nddarray1 == nddarray2),
            "Result of imread and to_ndarray are different!",
        )
