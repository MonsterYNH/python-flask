FROM python:3.7

RUN mkdir /project && pip install Flask Flask-AppBuilder pandas psycopg2 pillow keras tensorflow

COPY . /project/

WORKDIR /project/dash-board/
