import asyncio
import websockets
import requests
import json
import re
import os
from datetime import datetime

from src.config import ColorLogFormatter, DEBUG, PATH_DIR_LOGS, DATE_START

import logging


logger = logging.getLogger('berezka.notifications')
logger.setLevel(logging.DEBUG)

c_handler = logging.StreamHandler()
c_format = ColorLogFormatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
c_handler.setFormatter(c_format)
logger.addHandler(c_handler)

f_handler = logging.FileHandler(os.path.join(PATH_DIR_LOGS, f'berezka-notifications-{DATE_START}.log'))
f_format = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
f_handler.setFormatter(f_format)
f_handler.setLevel(logging.DEBUG)
logger.addHandler(f_handler)

if DEBUG:
    c_handler.setLevel(logging.DEBUG)
else:
    c_handler.setLevel(logging.INFO)

def negotiate(token):
    endpoint = "https://signalr.agregatoreat.ru/AuthorizedHub/Negotiate?v=1"
    headers = {"Authorization": f"Bearer {token}"}
    logger.debug(f'Запрос ID у berezka (url={endpoint})')
    r = requests.post(endpoint, headers=headers)
    result = None
    logger.debug(f'Запрос отработал.')
    if r.status_code == 200:
        logger.debug(f'Запрос вернул статус 200. Парсим результаты')
        result = r.json()['connectionId']
    else:
        logger.warning(f'Запрос вернул статус {r.status_code}')

    return result

def parse_args_new_notificatios(arguments):
    result = []
    for arg in arguments:
        r = re.search(r"\d{18}", arg)
        if r:
            # print(f'нашел новую закупку под номером {r[0]}')
            result.append(r[0])
    return result

async def listen_websockets(credentials, callback):
    wss_url = f"wss://signalr.agregatoreat.ru/AuthorizedHub?id={credentials['id']}&"\
        f"v={credentials['v']}&access_token={credentials['token']}"
    logger.debug(f'Попытка запустить обмен по websockets')
    async with websockets.connect(wss_url) as websocket:
        logger.debug('Соединение по websockets прошло успешно. Пытаемся отправить первое сообщение -> {"protocol":"json","version":1}')
        await websocket.send('{"protocol":"json","version":1}\x1e')
        logger.debug('Первое сообщение отправлено. Ждем ответ')
        response = await websocket.recv()
        logger.debug(f'Ответ получен {response}')
        logger.debug(f'Переходим в бесконечный цикл обмена сообщениями')
        while True:
            raw_response = await websocket.recv()
            now = datetime.now()
            logger.info(f'Получили сырое сообщение -> {raw_response}')
            try:
                logger.debug('Парсим сообщение')
                response = json.loads(raw_response.replace('\x1e', ''))
                if response['type'] == 6:
                    logger.debug('Получили служебное сообщение отправляем ответ <- {"type":6}')
                    await websocket.send('{"type":6}\x1e')
                elif response['type'] == 1 and response['target'] == 'NewInternalNotificationCame':
                    logger.debug('Получили сообщение о публикации нового конкурса. Парсим номер конкурса!')
                    list_number_procedure = parse_args_new_notificatios(response['arguments'])
                    logger.info(f'Найдены сообщение о публикации следующих процедур {list_number_procedure}')
                    for order in list_number_procedure:
                        callback(order, now)
                else:
                    logger.debug('Ничего интересного пропускаем')


            except Exception as ex:
                logger.exception(ex)

def listen_notifications(token, callback):
    logger.debug('Попытка получить id сессии для websockets')
    id = negotiate(token)
    logger.debug(f'ID сессии для websockets получен, пытаемся запустить websockets для прослушки (id={id})')
    asyncio.run(listen_websockets({'id': id, 'v':1, 'token':token},callback))
    











# async def listen_websockets(credentials)->None:
#     # print(credentials)
#     logging.basicConfig(
#     format="%(message)s",
#     level=logging.DEBUG,
# )
#     credential = credentials['websockets'][0]

#     wss_url = f"wss://signalr.agregatoreat.ru/AuthorizedHub?id={credential['id']}&"\
#         f"v={credential['v']}&access_token={credential['access_token']}"
#     # wss_url = f"wss://signalr.agregatoreat.ru/AuthorizedHub?"\
#     #     f"v={credential['v']}&access_token={credential['access_token']}"
#     try:
#         async with websockets.connect(wss_url) as websocket:
#             # print(dir(websocket))
#             data = {'protocol':'json', 'version': 1}
#             await websocket.send('{"protocol":"json","version":1}\x1e')
#             # response = await websocket.recv()
#             while True:
#                 raw_response = await websocket.recv()
                
#                 try:
#                     response = json.loads(raw_response.replace('\x1e', ''))
#                     if response['type'] == 6:
#                         await websocket.send('{"type":6}\x1e')
#                 except Exception as ex:
#                     print(ex)
                


#                 # print(type(raw_response))
#                 # print(raw_response)
#                 # print(response)


#             # print(response)
#             # while True:
#             #     data = {'protocol':'json', 'version': 1}
#             #     # data = {'type':6}

#             #     print("------ send ------")
#             #     response = await websocket.send(json.dumps(data))
#             #     print(response)
#             #     print("******* send *******")
#             #     sleep(15)
#             #     data = {'type':6}
#             #     response = await websocket.send(json.dumps(data))
#             #     response = await websocket.recv()
#             #     print("------ resp ------")
#             #     print(response)
#             #     print("******* resp ******")

#     except Exception as ex:
#         print("------ ERROR ------")
#         print(ex)  
#         print("******* ERROR *******")
    
