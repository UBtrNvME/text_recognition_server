# -*- coding: utf8 -*-
import base64
import json
import re

import cv2
import numpy as np
from flask import Flask, render_template, request

from recognition import Parser

import pdf2image

app = Flask(__name__)

LEFT_MARGIN = 220


@app.route("/recognise", methods=["POST"])
def recognise():
    file = request.files["file"]

    content = file.read()
    mimetype = file.mimetype

    p = Parser()
    pages = []
    res = {"Document": {}}
    if mimetype in ["image/png", "image/jpeg"]:
        nparr = np.fromstring(content, np.uint8)
        pages.append(cv2.imdecode(nparr, cv2.IMREAD_COLOR))
    elif mimetype == "application/pdf":
        pdf_pages = pdf2image.convert_from_bytes(content)
        for page in pdf_pages:
            pages.append(np.array(page))
    else:
        return "%s IS NOT YET IMPLEMENTED" % mimetype.upper()
    images = []
    for i, page in enumerate(pages):
        p.input(page)
        res["Document"][f"page_{i + 1}"] = p.parse_v2()
        pages[i] = None
        img_str = cv2.imencode(".jpg", p.image)[1].tostring()
        images.append(img_str)

    return render_template(
        "visualise_page.html",
        images=[
                f"data:image/jpeg;base64,{base64.b64encode(image).decode('utf-8')}"
                for image in images],
        boxes=json.dumps(res),
    )


@app.route("/")
def index():
    return """
    <!doctype html>
    <title>File to Recognise</title>
    <form method="POST" action="/recognise" enctype="multipart/form-data">
     <div>
       <label for="file">Choose file to upload</label>
       <input type="file" id="file" name="file" multiple>
     </div>
     <div>
       <button>Submit</button>
     </div>
    </form>
    """


if __name__ == "__main__":
    app.run(host="0.0.0.0")
