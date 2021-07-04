# syntax=docker/dockerfile:1
FROM python:3.9.5
COPY . .
RUN pip3 install -r requirements.txt

ENV FLASK_APP=Doorbot.API
CMD [ "python3", "-m flask", "run" ]
