FROM python:3.6.1

ENV PYTHONUNBUFFERED 1

EXPOSE 8000
WORKDIR /app


RUN apt-get update && \
    apt-get install -y --no-install-recommends netcat && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip -V

RUN pip install -r requirements.txt

COPY . ./

WORKDIR ./app/dependencies/ctpn_text_detection/lib/utils

RUN chmod +x make.sh && \
    ./make.sh

WORKDIR ../../../..

CMD uvicorn --host=0.0.0.0 app.main:app