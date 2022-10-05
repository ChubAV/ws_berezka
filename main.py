import os
from src.config import DEBUG, ColorLogFormatter, PATH_DIR_LOGS, DATE_START
from src.credentials import TransportCredential, get_credentials
from src.notifications import listen_notifications
import logging
from datetime import datetime, timedelta
from src.commands import send_order_in_rabbitmq


logger = logging.getLogger('berezka.main')
logger.setLevel(logging.DEBUG)

c_handler = logging.StreamHandler()
c_format = ColorLogFormatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
c_handler.setFormatter(c_format)
logger.addHandler(c_handler)

f_handler = logging.FileHandler(os.path.join(PATH_DIR_LOGS, f'berezka-main-{DATE_START}.log'))
f_format = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
f_handler.setFormatter(f_format)
f_handler.setLevel(logging.DEBUG)
logger.addHandler(f_handler)


MAX_COUNT_ERRORS = 5
def get_token(transport = TransportCredential.REQUEST):
    credentials = get_credentials(transport = transport, save_to_file=True)
    if transport == TransportCredential.SELENIUM:
        token = credentials.websockets[-1]['access_token']
    elif transport == TransportCredential.FILE:
        token = credentials.websockets[-1]['access_token']
    elif transport == TransportCredential.REQUEST:
        token = credentials.localstorage['access_token']
    logger.debug(f'Bearer token -> {token}')
    return token

def main() -> None:
    logger.info('Запуск berezka robot')
    transport = TransportCredential.REQUEST
    command = send_order_in_rabbitmq
    count_errors = 0
    last_time_error = datetime.now()
    while True:
        try:
            logger.info('Попытка получить учетные данные для авторизации')
            token = get_token(transport)
            
            logger.info('Учетные данные получины, запускаем прослушку сообщений от berezka')
            listen_notifications(token, command)
        except Exception as ex:
            logger.exception(ex)
            count_errors += 1
            now = datetime.now()
            if count_errors > MAX_COUNT_ERRORS and now - last_time_error < timedelta(seconds=30):
                logger.error('Выход из программы из-за большого количества ошибок')
                return False
            else:
                logger.warning(f'Попытка перезапустить программу. Текущее количество ошибок {count_errors}, время последней ошибки {now}')
                if now - last_time_error > timedelta(minutes=5):
                    count_errors = 1
                last_time_error = now


if __name__ == "__main__":
    if DEBUG:
        c_handler.setLevel(logging.DEBUG)
    else:
        c_handler.setLevel(logging.INFO)
    main()