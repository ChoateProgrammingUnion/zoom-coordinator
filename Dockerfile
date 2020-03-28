FROM python:latest

MAINTAINER InnovativeInventor

WORKDIR /usr/src/app
COPY . /usr/src/app

RUN pip3 install gunicorn flask Flask-Dance fuzzysearch validators dataset pytz
#RUN pip3 install gunicorn flask Flask-Caching Flask-Dance
RUN rm Dockerfile

EXPOSE 5000
CMD [ "gunicorn", "app:app", "-w", "4", "--bind", ":5000" ]
