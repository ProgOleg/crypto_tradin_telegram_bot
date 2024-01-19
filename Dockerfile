FROM python:3.9-slim-buster as base

RUN apt-get update \
&& apt-get upgrade -qy \
&& apt-get autoremove --yes \
&& rm -rf /var/lib/{apt,dpkg,cache,log}/ \
&& apt-get clean autoclean;

FROM base as python-compile

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
RUN pip3 install --upgrade pip
COPY requirements.txt /usr/src/app/
COPY .env /usr/src/app/
COPY main.py /usr/src/app/
COPY utils /usr/src/app/utils
COPY db /usr/src/app/db
COPY migrations /usr/src/app/migrations
COPY config.py /usr/src/app/
COPY static /usr/src/app/static

RUN pip3 install --no-cache-dir -r requirements.txt

FROM python-compile AS build-image
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

CMD ["python3", "main.py"]