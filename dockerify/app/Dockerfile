FROM python:3.6

ENV PYTHONUNBUFFERED 1

RUN apt-get update -y
RUN apt-get -y install binutils libproj-dev gdal-bin

RUN apt-get update && apt-get install -y \
        vim \
        postgresql-client \
        libpq-dev \
        collectl \
        build-essential \
        libssl-dev \
        swig \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
COPY ./requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

RUN mkdir -p /app/code

COPY . /app/code

WORKDIR /app/code
ENTRYPOINT /app/code/dockerify/app/entrypoint.sh
