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

from ..dependencies.ctpn_text_detection.lib.fast_rcnn.config import cfg, cfg_from_file
from ..dependencies.ctpn_text_detection.lib.fast_rcnn.test import test_ctpn
from ..dependencies.ctpn_text_detection.lib.networks.factory import get_network
from ..dependencies.ctpn_text_detection.lib.text_connector.detectors import TextDetector
from ..dependencies.ctpn_text_detection.lib.text_connector.text_connect_cfg import (
    Config as TextLineCfg,
)
from ..dependencies.ctpn_text_detection.lib.utils.timer import Timer

sys.path.append(os.getcwd())


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


def ctpn(sess, net, image_name):
    timer = Timer()
    timer.tic()

    img = cv2.imread(image_name)
    img, scale = resize_im(
        img, scale=TextLineCfg.SCALE, max_scale=TextLineCfg.MAX_SCALE
    )
    scores, boxes = test_ctpn(sess, net, img)

    textdetector = TextDetector()
    boxes = textdetector.detect(boxes, scores[:, np.newaxis], img.shape[:2])
    draw_boxes(img, image_name, boxes, scale)
    timer.toc()
    print(
        ("Detection took {:.3f}s for " "{:d} object proposals").format(
            timer.total_time, boxes.shape[0]
        )
    )


if __name__ == "__main__":
    if os.path.exists("data/results/"):
        shutil.rmtree("data/results/")
    os.makedirs("data/results/")

    cfg_from_file("ctpn/text.yml")

    # init session
    config = tf.ConfigProto(allow_soft_placement=True)
    sess = tf.Session(config=config)
    # load network
    net = get_network("VGGnet_test")
    # load model
    print(("Loading network {:s}... ".format("VGGnet_test")), end=" ")
    saver = tf.train.Saver()

    try:
        ckpt = tf.train.get_checkpoint_state(cfg.TEST.checkpoints_path)
        print("Restoring from {}...".format(ckpt.model_checkpoint_path), end=" ")
        saver.restore(sess, ckpt.model_checkpoint_path)
        print("done")
    except Exception:
        raise "Check your pretrained {:s}".format(ckpt.model_checkpoint_path)

    im = 128 * np.ones((300, 300, 3), dtype=np.uint8)
    for i in range(2):
        _, _ = test_ctpn(sess, net, im)

    im_names = glob.glob(os.path.join(cfg.DATA_DIR, "demo", "*.png")) + glob.glob(
        os.path.join(cfg.DATA_DIR, "demo", "*.jpg")
    )

    for im_name in im_names:
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print(("Demo for {:s}".format(im_name)))
        ctpn(sess, net, im_name)
