FROM python:3

EXPOSE 5000
WORKDIR usr/src/app

RUN apt-get update && \
	apt-get install -y --no-install-recommends tesseract-ocr-eng tesseract-ocr-rus && \
	rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN pip install --upgrade pip && \
    pip -V

RUN pip install opencv-python-headless

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["python"]
CMD ['server.py']