"""
Connectionist Text Proposal Network
===================================

Module which implements connectionist text proposal network (ctpn)
which detects a text line in a sequence of fine-scale text proposals
directly in convolutional feature maps.

Simply saying it pinpoints possible text locations, and returns
all of these locations in format of list of bounding rectangles,
which later can be provided to the text recognition neural network
such as Google's Tenserflow to detect text in those rectangles
"""

import glob
import os
import shutil
import sys

import cv2
import numpy as np
import tensorflow as tf

from app.dependencies import CTPN_TEXT_DETECTION_LIB_PATH
from app.dependencies.ctpn_text_detection.lib.fast_rcnn.config import cfg, cfg_from_file
from app.dependencies.ctpn_text_detection.lib.fast_rcnn.test import test_ctpn
from app.dependencies.ctpn_text_detection.lib.networks.factory import get_network
from app.dependencies.ctpn_text_detection.lib.text_connector.detectors import (
    TextDetector,
)
from app.dependencies.ctpn_text_detection.lib.text_connector.text_connect_cfg import (
    Config as TextLineCfg,
)
from app.dependencies.ctpn_text_detection.lib.utils.timer import Timer
from app.utils import filepath

MAX_INT = 1000000
CHECKPOINT_PATH = filepath.join(CTPN_TEXT_DETECTION_LIB_PATH, cfg.TEST.checkpoints_path)


def _rescale_box(box, factor):
    box[0] = int(box[0] * factor[0])
    box[1] = int(box[1] * factor[1])
    box[2] = int(box[2] * factor[0])
    box[3] = int(box[3] * factor[1])
    box[4] = int(box[4] * factor[0])
    box[5] = int(box[5] * factor[1])
    box[6] = int(box[6] * factor[0])
    box[7] = int(box[7] * factor[1])
    return box


def rescale_boxes(boxes, image_shape: tuple, scale: float):
    factor = (image_shape[1] / scale, image_shape[0] / scale)
    for box in boxes:
        yield _rescale_box(box, factor)


def divide_and_conquer(image, scale):
    # if pass shape skip
    # else divide image into equal sizes
    # and then conquer
    if image.shape[0] > image.shape[1]:
        # rotate_image
        pass
    x_pieces = 1
    y_pieces = 1
    x_scale = image.shape[1]
    y_scale = image.shape[0]

    if image.shape[1] > scale:
        while image.shape[1] / x_pieces > scale or not image.shape[1] % x_pieces:
            x_pieces += 1
        x_scale = image.shape[1] // x_pieces

    if image.shape[0] > scale:
        while image.shape[0] / y_pieces > scale or not image.shape[0] % y_pieces:
            y_pieces += 1
        y_scale = image.shape[0] // y_pieces

    for y in range(y_pieces):
        for x in range(x_pieces):
            yield y, x, image[
                y * y_scale : y * y_scale + y_scale, x * x_scale : x * x_scale + x_scale
            ]


def group_up(boxes, threshold):
    """
    Returns group of the boxes which later
    can be recreated into one box
    """
    used_boxes = np.full((len(boxes)), fill_value=False, dtype=bool)
    for index, rect in enumerate(boxes):
        group = [rect]
        if used_boxes[index]:
            continue

        for oindex, orect in enumerate(boxes):
            if index == oindex:
                continue

            if distance_between(orect, rect) < threshold:
                group.append(orect)
                used_boxes[oindex] = True
        yield group


def merge_grouped(group):
    left = MAX_INT
    right = 0
    top = MAX_INT
    bottom = 0
    for box in group:
        left = min(left, box[0])
        right = max(right, box[2])
        top = max(top, box[1])
        bottom = max(bottom, box[5])
    return left, top, right, bottom


def distance_between(rect1, rect2):
    ds = [
        abs(rect1[0] - rect2[0]),
        abs(rect1[0] + rect1[2] - rect2[0]),
        abs(rect1[0] - rect2[0] + rect2[2]),
        abs(rect1[0] + rect1[2] - rect2[0] + rect2[2]),
        abs(rect1[1] - rect2[1]),
        abs(rect1[1] + rect1[3] - rect2[1]),
        abs(rect1[1] - rect2[1] + rect2[3]),
        abs(rect1[1] + rect1[3] - rect2[1] + rect2[3]),
    ]
    return min(ds)


def _assign_original_position(rect, offset):
    rect[0] = rect[0] + offset[0]
    rect[1] = rect[1] + offset[1]
    rect[2] = rect[2] + offset[0]
    rect[3] = rect[3] + offset[1]
    rect[4] = rect[4] + offset[0]
    rect[5] = rect[5] + offset[1]
    rect[6] = rect[6] + offset[0]
    rect[7] = rect[7] + offset[1]
    return rect


def resize_im(im, scale, max_scale=None):
    f = float(scale) / min(im.shape[0], im.shape[1])
    if max_scale is not None and f * max(im.shape[0], im.shape[1]) > max_scale:
        f = float(max_scale) / max(im.shape[0], im.shape[1])
    return cv2.resize(im, None, None, fx=f, fy=f, interpolation=cv2.INTER_LINEAR), f


def draw_boxes(img, image_name, boxes, scale):
    for box in boxes:
        if box[8] >= 0.9:
            color = (0, 255, 0)
        elif box[8] >= 0.8:
            color = (255, 0, 0)
        cv2.line(img, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), color, 2)
        cv2.line(img, (int(box[0]), int(box[1])), (int(box[4]), int(box[5])), color, 2)
        cv2.line(img, (int(box[6]), int(box[7])), (int(box[2]), int(box[3])), color, 2)
        cv2.line(img, (int(box[4]), int(box[5])), (int(box[6]), int(box[7])), color, 2)

    base_name = image_name.split("/")[-1]
    img = cv2.resize(
        img, None, None, fx=1.0 / scale, fy=1.0 / scale, interpolation=cv2.INTER_LINEAR
    )
    cv2.imwrite(os.path.join("data/results", base_name), img)


def ctpn(sess, net, image):
    all_boxes = []
    textdetector = TextDetector()

    image = divide_and_conquer(image, TextLineCfg.MAX_SCALE)
    for part in image:
        tmp_image, scale = resize_im(
            part[2], scale=TextLineCfg.SCALE, max_scale=TextLineCfg.MAX_SCALE
        )
        scores, boxes = test_ctpn(sess, net, tmp_image)
        boxes = textdetector.detect(boxes, scores[:, np.newaxis], tmp_image.shape[:2])
        for i, box in enumerate(boxes):
            boxes[i] = _assign_original_position(box, (part[0], part[1]))
        all_boxes.extend(rescale_boxes(boxes, image_shape=tmp_image.shape, scale=scale))

    grouped_boxes = group_up(all_boxes, 15)
    result = []
    for box in grouped_boxes:
        result.append(merge_grouped(box))
    return {"boxes": result}


def detect(image):
    cfg_from_file(filepath.path("services/config.yaml"))

    # init session
    config = tf.ConfigProto(allow_soft_placement=True)
    sess = tf.Session(config=config)
    # load network
    net = get_network("VGGnet_test")
    # load model
    print(("Loading network {:s}... ".format("VGGnet_test")), end=" ")
    saver = tf.train.Saver()

    try:
        ckpt = tf.train.get_checkpoint_state(CHECKPOINT_PATH)
        print("Restoring from {}...".format(ckpt.model_checkpoint_path), end=" ")
        saver.restore(sess, ckpt.model_checkpoint_path)
        print("done")
    except Exception:
        raise "Check your pretrained {:s}".format(ckpt.model_checkpoint_path)

    # for i in range(2):
    #     _, _ = test_ctpn(sess, net, im)

    return ctpn(sess, net, image)
