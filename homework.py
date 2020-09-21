import logging
import os
import time

import requests
import telegram

from dotenv import load_dotenv
from telegram.error import NetworkError, TelegramError

# Включаем поддержку записи UTF-8 в журналах
logging.basicConfig(
    handlers=[logging.FileHandler('hw_sp_bot.log', 'a', 'utf-8')],
    format='%(filename)s[LINE:%(lineno)d]# '
           '%(levelname)-8s [%(asctime)s]  %(message)s',
    level=logging.INFO
)


load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
PRAKTIKUM_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'

bot = telegram.Bot(token=TELEGRAM_TOKEN)


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    homework_approved = homework.get('status')
    if homework_name is None or homework_approved is None:
        logging.error(
            f'Яндекс.Практикум вернул неожиданный ответ: {homework}'
        )
        return 'Сервер вернул неожиданный ответ'
    if homework_approved != 'approved':
        verdict = 'К сожалению в работе нашлись ошибки.'
    else:
        verdict = 'Ревьюеру всё понравилось,' \
                  ' можно приступать к следующему уроку.'
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
    except requests.RequestException as e:
        logging.error(f'Не удалось подключиться к серверу: {e}')
        return {}
    except Exception as e:
        logging.error(f'Ошибка запроса к API Яндекс: {e}')
        return {}
    return homework_statuses.json()


def send_message(message):
    try:
        msg = bot.send_message(chat_id=CHAT_ID, text=message)
    except NetworkError as e:
        logging.error(f'Ошибка подключения к Telegram API: {e}')
        return e
    except TelegramError as e:
        logging.error(f'Ошибка Telegram API: {e}')
        return e
    return msg


def main():
    current_timestamp = int(time.time())
    logging.info('Main worker has started')
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(parse_homework_status(
                    new_homework.get('homeworks')[0])
                )
                current_timestamp = new_homework.get('current_date')
            time.sleep(3)

        except Exception as e:
            logging.error(f'Бот упал с ошибкой: {e}')
            time.sleep(5)
            continue


if __name__ == '__main__':
    main()
