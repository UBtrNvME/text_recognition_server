import pathlib

import cv2
import numpy as np
import pytesseract
import scipy.signal
import xlsxwriter as xl
from scipy import signal
from scipy.ndimage import interpolation as inter


def butter_highpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = signal.butter(order, normal_cutoff, btype="high", analog=False)
    print(b, a)
    return b, a


def butter_highpass_filter(data, cutoff, fs, order=5):
    b, a = butter_highpass(cutoff, fs, order=order)
    y = signal.filtfilt(b, a, data)
    return y


class Parser:
    def __init__(self):
        self.image = None

    def input(self, image):
        # preprocess image:
        # * crop not needed outer bounds
        # * noise reduction etc

        self.image = image
        angle, rotated = self._skew_correction()
        print(angle)
        self.image = rotated

    def parse(self):
        # * find tables bounds
        # * if tables found find headers
        # * parse data according to the table
        # * parse another information
        table_loc = self._find_table_bounds()
        data = []
        if table_loc:
            headers = self._get_headers(table_loc)
            data.append(self._parse_table(table_loc, headers))
        data.append(self._parse_miscelleneous(table_loc))
        return data

    def parse_v2(self):
        if self.image is None:
            return False

        result = []
        frames = self._divide_page_y()
        for frame, y in frames:
            for xframe, x in self._parse_frame(frame):
                data = pytesseract.image_to_data(
                    xframe, lang="rus+eng", output_type=pytesseract.Output.DICT
                )
                for xx, yy, w, h, text in zip(
                    data["left"],
                    data["top"],
                    data["width"],
                    data["height"],
                    data["text"],
                ):
                    text = text.strip()
                    if text:
                        result.append([int(xx + x), int(yy + y), int(w), int(h), text])
        return result

    def _divide_page_y(self):
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        lines_image = cv2.dilate(
            cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY), kernel, iterations=3
        )
        height, width = self.image.shape[:2]
        rows = np.sum((lines_image < 250), axis=1)
        # rows_filtered = butter_highpass_filter(rows, 1, 25)
        peaks, _ = scipy.signal.find_peaks(rows, height=width * 0.7, distance=20)

        pivots_y = [0]
        pivots_y.extend(peaks)
        pivots_y.append(height - 1)
        for i in range(1, len(pivots_y), 1):
            yield self.image[pivots_y[i - 1] : pivots_y[i], 0:width], pivots_y[i - 1]

    def _parse_frame(self, frame):
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 10))
        lines_image = cv2.dilate(
            cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), kernel, iterations=3
        )
        # cv2.imshow("dilate", lines_image)
        # cv2.waitKey(0)
        height, width = frame.shape[:2]
        columns = np.sum((lines_image < 150), axis=0)
        peaks, _ = scipy.signal.find_peaks(columns, height=height * 0.5, distance=20)
        pivots_x = [0]
        pivots_x.extend(peaks)
        pivots_x.append(width - 1)
        for i in range(1, len(pivots_x), 1):
            yield frame[0:height, pivots_x[i - 1] : pivots_x[i]], pivots_x[i - 1]

    def _skew_correction(self, delta=1, limit=5):
        def determine_score(arr, angle):
            data = inter.rotate(arr, angle, reshape=False, order=0)
            histogram = np.sum(data, axis=1)
            score = np.sum((histogram[1:] - histogram[:-1]) ** 2)
            return histogram, score

        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        scores = []
        angles = np.arange(-limit, limit + delta, delta)
        for angle in angles:
            histogram, score = determine_score(thresh, angle)
            scores.append(score)

        best_angle = angles[scores.index(max(scores))]

        (h, w) = self.image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, best_angle, 1.0)
        rotated = cv2.warpAffine(
            self.image,
            M,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )

        return best_angle, rotated

    def _find_table_bounds(self):
        pass

    def _get_headers(self, table_loc):
        pass

    def _parse_table(self, table_loc, headers):
        pass

    def _parse_miscelleneous(self, table_loc):
        pass

    def write_excel(self, data):
        workbook = xl.Workbook("result.xlsx")
        for key in data:
            name = "_".join(key.split(" "))
            name = name.split("_")
            name = map(lambda x: x[0].upper() if x[0].isalpha() else x, name)
            print(name)
            worksheet = workbook.add_worksheet("".join(name))
            rowi = 0
            for row in data[key]:
                maxi = 0
                for coli, col in enumerate(row):
                    i = 0
                    for val in col.split("\n\n"):
                        if val:
                            worksheet.write(rowi + i, coli, val)
                            i += 1
                    maxi = max(i, maxi)
                rowi += maxi
        workbook.close()

    def make_matrix(self, a_dict):
        for path in self.read_folder():
            p.input(cv2.imread(str(path)))
            matrix = []
            i = 0
            for frame in p._divide_page_y():
                matrix.append([])
                for xframe in p._parse_frame(frame):
                    matrix[i].append(pytesseract.image_to_string(xframe, lang="rus"))
                i += 1
            a_dict[str(path).split("/")[-1]] = matrix

    def read_folder(self):
        BASEDIR = pathlib.Path(__file__).parent / "pdffiles"
        for abspath in BASEDIR.iterdir():
            yield abspath


if __name__ == "__main__":
    p = Parser()
    a_dict = {}
    p.make_matrix(a_dict)
    p.write_excel(a_dict)
