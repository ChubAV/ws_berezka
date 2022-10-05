import os
import pika
from src.config import RABBITMQ_HOST, RABBITMQ_QUEUE, ColorLogFormatter, DEBUG, PATH_DIR_LOGS, DATE_START

import logging
logger = logging.getLogger('berezka.commands')
logger.setLevel(logging.DEBUG)

c_handler = logging.StreamHandler()
c_format = ColorLogFormatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
c_handler.setFormatter(c_format)
logger.addHandler(c_handler)

f_handler = logging.FileHandler(os.path.join(PATH_DIR_LOGS, f'berezka-commands-{DATE_START}.log'))
f_format = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
f_handler.setFormatter(f_format)
f_handler.setLevel(logging.DEBUG)
logger.addHandler(f_handler)

if DEBUG:
    c_handler.setLevel(logging.DEBUG)
else:
    c_handler.setLevel(logging.INFO)

def send_order_in_rabbitmq(order):
    connection = None
    try:
        logger.debug(f'Попытка отправить сообщение в Rabbitmq')
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=RABBITMQ_QUEUE)
        logger.debug(f'Отправка сообщения (host -> {RABBITMQ_HOST}, queue -> {RABBITMQ_QUEUE}, message -> {order})')
        channel.basic_publish(exchange='',
                            routing_key=RABBITMQ_QUEUE,
                            body=order)
    except Exception as ex:
        logger.exception(ex)
        raise ex
    finally:
        if connection is not None:
            logger.debug(f'Закрываем соединение с Rabbitmq')
            connection.close()
