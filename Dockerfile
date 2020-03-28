FROM python:latest

MAINTAINER InnovativeInventor

WORKDIR /usr/src/app
COPY . /usr/src/app

RUN pip3 install gunicorn flask Flask-Dance fuzzysearch validators dataset pytz
RUN rm index.db && python3 preprocess.py
#RUN pip3 install gunicorn flask Flask-Caching Flask-Dance
#RUN rm Dockerfile

EXPOSE 80
#CMD [ "gunicorn", "app:app", "-w", "4", "--bind", "127.0.0.1:80" ]
CMD [ "gunicorn", "app:app", "-w", "4", "--bind", "0.0.0.0:80" ]
#EXPOSE 8080
#CMD [ "gunicorn", "app:app", "-w", "4", "--bind", "127.0.0.1:8080" ]
