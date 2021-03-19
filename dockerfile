FROM python:3.7

RUN mkdir /project && pip install Flask Flask-AppBuilder pandas psycopg2

COPY . /project/

WORKDIR /project/dash-board/
