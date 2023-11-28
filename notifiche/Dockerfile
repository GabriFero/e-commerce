FROM python:3.6-slim-buster

WORKDIR /notifiche/app.py

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY /notifiche/app.py ./

CMD [ "python3","app.py" ]
