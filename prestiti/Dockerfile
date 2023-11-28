FROM python:3.6-slim-buster

WORKDIR /prestiti/app

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY /prestiti ./

COPY . .

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=11000"]