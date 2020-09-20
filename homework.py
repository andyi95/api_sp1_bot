import logging
import os
import requests
import datetime
import telegram
from telegram.error import (TelegramError, Unauthorized, BadRequest, TimedOut, ChatMigrated, NetworkError)
import time
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    filename="homework.log",
    format="%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s",
)

PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
PRAKTIKUM_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
try:
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
except TimedOut:
    logging.error('Telegram Bot: превышено время ожидания')
except NetworkError:
    logging.error('Telegram Bot: ошибка подключения')
except TelegramError as e:
    logging.error(f'Telegram Bot: ошибка {e}')


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    homework_approved = homework.get('status')
    if homework_name is None or homework_approved is None:
        logging.error(f'Яндекс.Практикум вернул неожиданный ответ: {homework}')
        return 'Сервер вернул неожиданный ответ'
    if homework_approved != 'approved':
        verdict = 'К сожалению в работе нашлись ошибки.'
    else:
        verdict = 'Ревьюеру всё понравилось, можно приступать к следующему уроку.'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    params = {'from_date': current_timestamp}
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    try:
        homework_statuses = requests.get(
            PRAKTIKUM_URL,
            headers=headers,
            params=params
        )
    except ConnectionError as e:
        logging.error('Не удалось подключиться к серверу', e)
    return homework_statuses.json()


def send_message(message):
    return bot.send_message(chat_id=CHAT_ID, text=message)


def main():
    current_timestamp = int(time.time())  # начальное значение timestamp
    # current_timestamp = int(0) # 2020-09-14
    # current_timestamp =  int(time.mktime(time.strptime('14/09/2020 00:00:00', "%d/%m/%Y %H:%M:%S")))
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(parse_homework_status(new_homework.get('homeworks')[0]))
            current_timestamp = new_homework.get('current_date')  # обновить timestamp
            time.sleep(300)  # опрашивать раз в пять минут

        except Exception as e:
            print(f'Бот упал с ошибкой: {e}')
            time.sleep(5)
            continue


if __name__ == '__main__':
    main()
