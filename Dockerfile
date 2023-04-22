FROM python:3.11-alpine

COPY ./requirements.txt ./requirements.txt

LABEL DEVELOPER="ING MICHAEL KOFI ARMAH"

# --------------------------------------
# DOCKER FILE FOR GOOGLE SCHOLAR CRAWLER
# --------------------------------------

RUN pip install --upgrade pip

RUN pip install -r ./requirements.txt

WORKDIR /spider

COPY . .

ENV PYTHONUNBUFFERED 1