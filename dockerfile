FROM --platform=arm64 python:3.7

RUN mkdir /project && pip install Flask Flask-AppBuilder pandas psycopg2

COPY dash-board /project

WORKDIR /project/dash-board/