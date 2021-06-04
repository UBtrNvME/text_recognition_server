import base64
import json
import re

import cv2
import numpy as np
from flask import Flask, render_template, request

from recognition import Parser

# import pdf2image

app = Flask(__name__)

PARAGRAPH = "<p>%s</p>"
LEFT_MARGIN = 220


@app.route("/recognise", methods=["POST"])
def recognise():
    file = request.files["file"]

    content = file.read()
    mimetype = file.mimetype

    p = Parser()
    if mimetype in ["image/png", "image/jpeg"]:
        nparr = np.fromstring(content, np.uint8)
        images = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    else:
        return "%s IS NOT YET IMPLEMENTED" % mimetype.upper()

    p.input(images)
    res = p.parse_v2()

    html_text = []
    paragraph = []
    for x, y, w, h, text in res.copy():
        paragraph.append(text)
        if re.match(r"([a-z,A-Z,а-я,А-Я]+\s*[.;!?:])", text):
            html_text.append(PARAGRAPH % " ".join(paragraph))
            paragraph = []

    img_str = cv2.imencode(".jpg", p.image)[1].tostring()
    return render_template(
        "index_document.html",
        image=f"data:{mimetype};base64,{base64.b64encode(img_str).decode('utf-8')}",
        boxes=json.dumps(res),
        text="".join(html_text),
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
