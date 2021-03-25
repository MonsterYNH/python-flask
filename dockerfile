# FROM nvidia/cuda:11.0-base

# RUN apt-get update && apt-get install -y software-properties-common && add-apt-repository ppa:deadsnakes/ppa && apt update && apt install -y python3.8

# RUN apt-get install -y python3-pip

# RUN pip3 install --upgrade tensorflow

# RUN mkdir /project && pip3 install Flask Flask-AppBuilder pandas pillow keras

# COPY . /project/

# WORKDIR /project/dash-board/

# FROM gw000/keras-full
FROM python:3.7

RUN mkdir /project && pip install Flask Flask-AppBuilder pandas pillow keras

RUN pip install tensorflow

COPY . /project/

WORKDIR /project/dash-board/

