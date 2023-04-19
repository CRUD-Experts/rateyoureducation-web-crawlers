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

ENV MONGODB_CONNECTION_STRING mongodb+srv://mk-armah:71122263@africa.vbm2ys7.mongodb.net/?retryWrites=true&w=majority&authSource=admin
