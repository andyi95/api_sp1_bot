FROM python:3.8
LABEL description="A telegram bot for checking Yandex.Praktikum homework status"
LABEL version="1.0"
RUN mkdir /app/
ADD homework.py /app/
ADD requirements.txt /app/
ADD .env /app/
RUN pip install -r requirements.txt
CMD [ "python",  "./app/homework.py"]
