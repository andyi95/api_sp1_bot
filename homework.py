import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv
from telegram.error import NetworkError, TelegramError

# Включаем поддержку записи UTF-8 в журналах
# noinspection PyArgumentList
logging.basicConfig(
    handlers=[logging.FileHandler('hw_sp_bot.log', 'a', 'utf-8')],
    format=' [%(asctime)s] %(filename)s[LINE:%(lineno)d]# '
           '%(levelname)-8s %(message)s',
    level=logging.INFO
)


load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
PRAKTIKUM_API = 'https://praktikum.yandex.ru/api/'
YA_HW_API = 'user_api/homework_statuses/'
PRAKTIKUM_URL = PRAKTIKUM_API+YA_HW_API
HW_STATUS = {
    'approved':
        'Ревьюеру всё понравилось, можно приступать к следующему уроку.',
    'rejected':
        'К сожалению в работе нашлись ошибки.'
}

bot = telegram.Bot(token=TELEGRAM_TOKEN)


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    homework_approved = homework.get('status')
    if homework_name is None or homework_approved is None:
        logging.error(
            f'Яндекс.Практикум вернул неожиданный ответ: {homework}'
        )
        return 'Сервер вернул неожиданный ответ'
    if homework_approved in HW_STATUS:
        verdict = HW_STATUS[homework_approved]
    else:
        logging.error(f'Неверный статус работы: {homework_approved}')
        return 'Не удалось определить статус работы'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    # Добавил проверку не только типа, но и диапазона возможных значений -
    # надеюсь, что до 2050 года хватит ;)
    if (type(current_timestamp) == int and
            0 <= current_timestamp <= 2524608000):
        params = {'from_date': current_timestamp}
    else:
        logging.error(f'Получено неверное значение даты: {current_timestamp}')
        # Попытаемся исправить ситуацию
        params = {'from_date': int(time.time())}
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    try:
        homework_statuses = requests.get(
            PRAKTIKUM_URL,
            headers=headers,
            params=params
        )
    except requests.RequestException as e:
        logging.error(
            f'Не удалось подключиться к серверу {PRAKTIKUM_URL}: {e} \n\t '
            f'Заголовок запроса: {headers}\n\t'
            f'Параметры запроса: {params}'
        )
        return {}
    except Exception as e:
        logging.error(
            f'Ошибка запроса к API Яндекс: {PRAKTIKUM_URL}: {e} \n\t'
            f'Заголовок запроса: {headers}\n\t'
            f'Параметры запроса: {params}'
        )
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
            time.sleep(60*5)  # Так всяко наглядней

        except Exception as e:
            logging.error(f'Бот упал с ошибкой: {e}')
            time.sleep(5)
            continue


if __name__ == '__main__':
    main()
