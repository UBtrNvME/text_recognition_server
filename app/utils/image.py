from io import BufferedIOBase
from tempfile import SpooledTemporaryFile
from typing import IO

import cv2
import numpy as np


async def to_nddarray(image: IO[bytes]) -> np.ndarray:
    if isinstance(image, BufferedIOBase):
        A_bytes = image.read()
    elif isinstance(image, SpooledTemporaryFile):
        A_bytes = image.read()
    else:
        raise TypeError("Required type is %s" % BufferedIOBase)
    buffer = np.frombuffer(A_bytes, np.uint8)
    ndarray = cv2.imdecode(buffer, -1)
    image.close()
    return ndarray
