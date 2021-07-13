# syntax=docker/dockerfile:1
FROM python:3.9.5
COPY . .
RUN pip3 install -r requirements.txt

CMD [ "uwsgi", "--http :5000", "--module Doorbot.API:app" ]
