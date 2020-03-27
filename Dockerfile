FROM python:latest

MAINTAINER InnovativeInventor

WORKDIR /usr/src/app
COPY . /usr/src/app

RUN pip3 install gunicorn flask Flask-Dance
#RUN pip3 install gunicorn flask Flask-Caching Flask-Dance
RUN rm Dockerfile

EXPOSE 8000
CMD [ "gunicorn", "app:app", "-w", "4", "--bind", ":8000" ]
