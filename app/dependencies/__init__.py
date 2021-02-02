import sys

from app.utils.filepath import directory, join

CTPN_TEXT_DETECTION_LIB_PATH = join(directory(__file__), "ctpn_text_detection")
sys.path.append(CTPN_TEXT_DETECTION_LIB_PATH)
