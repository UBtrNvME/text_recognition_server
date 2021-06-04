FROM python:3

WORKDIR usr/src/app

RUN apt-get install tesseract-ocr-eng tesseract-ocr-rus

RUN pip install opencv-python-headless

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN export FLASK_APP=server.py && flask run

