import os
import pika
from src.config import RABBITMQ_HOST, RABBITMQ_QUEUE
import json

import logging
logger = logging.getLogger('ws-berezka')


def send_order_in_rabbitmq(order, now):
    connection = None
    try:
        logger.debug(f'Попытка отправить сообщение в Rabbitmq')
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=RABBITMQ_QUEUE)
        logger.debug(f'Отправка сообщения (host -> {RABBITMQ_HOST}, queue -> {RABBITMQ_QUEUE}, message -> {order})')
        body = json.dumps({'transport':'websockets', 'order': order, 'date':str(now)})
        channel.basic_publish(exchange='',
                            routing_key=RABBITMQ_QUEUE,
                            body=body)
    except Exception as ex:
        logger.exception(ex)
        raise ex
    finally:
        if connection is not None:
            logger.debug(f'Закрываем соединение с Rabbitmq')
            connection.close()
