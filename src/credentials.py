import os
from enum import Enum
from collections import namedtuple
from time import sleep
import json
import requests
from urllib.parse import urlsplit, parse_qs, quote_plus, unquote
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from src.config import  PATH_FILE_COOKIES, PATH_FILE_LOCALSTORAGE, PATH_WEBSOCKETS, PATH_DRIVER, HOME_URL, BEREZKA_LOGIN, BEREZKA_PASSWORD

import logging

from src.oauth2 import generate_code_verifier, get_code_challenge, get_nonce, get_state

logger = logging.getLogger('ws-berezka')

class LocalStorage:

    def __init__(self, driver) :
        self.driver = driver

    def __len__(self):
        return self.driver.execute_script("return window.localStorage.length;")

    def items(self) :
        return self.driver.execute_script( \
            "var ls = window.localStorage, items = {}; " \
            "for (var i = 0, k; i < ls.length; ++i) " \
            "  items[k = ls.key(i)] = ls.getItem(k); " \
            "return items; ")

    def keys(self) :
        return self.driver.execute_script( \
            "var ls = window.localStorage, keys = []; " \
            "for (var i = 0; i < ls.length; ++i) " \
            "  keys[i] = ls.key(i); " \
            "return keys; ")

    def get(self, key):
        return self.driver.execute_script("return window.localStorage.getItem(arguments[0]);", key)

    def set(self, key, value):
        self.driver.execute_script("window.localStorage.setItem(arguments[0], arguments[1]);", key, value)

    def has(self, key):
        return key in self.keys()

    def remove(self, key):
        self.driver.execute_script("window.localStorage.removeItem(arguments[0]);", key)

    def clear(self):
        self.driver.execute_script("window.localStorage.clear();")

    def __getitem__(self, key) :
        value = self.get(key)
        if value is None :
            raise KeyError(key)
        return value

    def __setitem__(self, key, value):
        self.set(key, value)

    def __contains__(self, key):
        return key in self.keys()

    def __iter__(self):
        return self.items().__iter__()

    def __repr__(self):
        return self.items().__str__()

class TransportCredential(Enum):
    REQUEST = 0
    SELENIUM = 1
    FILE = 2

Credentials = namedtuple('Credentials' ,'cookies localstorage websockets')

def save_to_file(data, full_path):
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False))

############################## Чтение из файлов #########################################

def read_from_file(full_path: str):
    with open(full_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def get_credentials_file() ->Credentials:
    logger.debug(f"Читаем учетные данные в файле -> COOKIES FILE ({PATH_FILE_COOKIES})")
    cookies = read_from_file(PATH_FILE_COOKIES)
    logger.debug(f"Читаем учетные данные в файле -> LOCAL STORAGE FILE ({PATH_FILE_COOKIES})")
    localstorage = read_from_file(PATH_FILE_LOCALSTORAGE)
    logger.debug(f"Читаем учетные данные в файле -> WESOCKET FILE ({PATH_WEBSOCKETS})")
    websockets = read_from_file(PATH_WEBSOCKETS)
    return Credentials(cookies, localstorage, websockets)


############################## Получение через selenium  #################################
def init_selenium_driver() -> webdriver:
        logger.debug("Настройка Selenium Driver")
        chrm_options=Options()
        chrm_caps = webdriver.DesiredCapabilities.CHROME.copy()
        chrm_caps['goog:loggingPrefs'] = { 'performance':'ALL' }
        
        logger.debug(f"Запуск Selenium Driver (executable_path={PATH_DRIVER})")
        driver = webdriver.Chrome(executable_path=PATH_DRIVER, chrome_options=chrm_options,desired_capabilities=chrm_caps)
        driver.set_window_size(768, 800)
        logger.debug(f"Переходим на домашную страницу berezka (HOME_URL={HOME_URL})")
        driver.get(HOME_URL)
        logger.debug(f"Ожидаем загрузку страницы (HOME_URL={HOME_URL})")
        el = WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(By.ID,"searchFilterText"))
        logger.debug(f"Страница загружена (HOME_URL={HOME_URL})")

        return driver

def go_to_login_page(driver: webdriver)->bool:
    logger.debug(f"Поиск верхнего меню для входа")
    link_login = driver.find_element(By.XPATH, "/html/body/app-root/div/div/app-header/header/div[2]/svg-icon")
    logger.debug(f"Нажимаем на верхнее меню входа")
    link_login.click()
    logger.debug(f"Ждем 1 секунду пока меню выпадет")
    sleep(1)
    logger.debug(f"Поиск ссылки <<Поставщик>> для перехода на страницу вход")
    link_login = driver.find_element(By.XPATH, "/html/body/app-dropdown-menu/div/div/a[1]")
    logger.debug(f"Нажимаем на ссылку <<Поставщик>> для перехода на страницу вход")
    link_login.click()
    logger.debug(f"Ждем пока загрузиться страница входа")
    el = WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(By.ID, "Username"))
    logger.debug(f"Страница входа загружена")
    return True

def login(driver: webdriver) -> bool:
    logger.debug(f"Поиск элемента input для ввода login по id - Username")
    input_username = driver.find_element(By.ID, "Username")
    logger.debug(f"Поиск элемента input для ввода password по id - passwordInput")
    input_password = driver.find_element(By.ID, "passwordInput") 
    logger.debug(f"Вводим login")
    input_username.send_keys(BEREZKA_LOGIN)
    logger.debug(f"Вводим password")
    input_password.send_keys(BEREZKA_PASSWORD)
    logger.debug(f"Вводим ENTER")
    input_password.send_keys(Keys.ENTER)
    logger.debug(f"Ждем пока произойдит авторизация в системе Berezka")
    el = WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(By.XPATH,"/html/body/app-root/div/main/app-lk/app-purchases-base/div[1]/div/div[2]/div/a[1]"))
    # print(el.text)
    # assert 'Закупки с моим участием'.upper() in el.text.upper()
    logger.debug(f"Авторизация прошла успешно")
    # print(el.text)
    # while True:
    #     pass
    return True

def get_cookies_from_selenium(driver, to_file = False)->bool:
    logger.debug(f"Получаем cookies из браузера (save_to_file={to_file})")
    cookies = driver.get_cookies()
    logger.debug(f"Cookies успешно получены -> {cookies}")
    if to_file:
        logger.debug(f"Сохраняем Cookies в файл -> {PATH_FILE_COOKIES}")
        save_to_file(cookies, PATH_FILE_COOKIES)
    return cookies


def get_localstorage_from_selenium(driver, to_file = False)->bool:
    logger.debug(f"Получаем LocalStorage из браузера (save_to_file={to_file})")
    storage = LocalStorage(driver)
    result = storage.items()
    logger.debug(f"LocalStorage успешно получены -> {result}")
    if to_file:
        logger.debug(f"Сохраняем LocalStorage в файл -> {PATH_FILE_LOCALSTORAGE}")
        save_to_file(result, PATH_FILE_LOCALSTORAGE)
    logger.debug(f"Очищаем объект LocalStorage")
    storage.clear()
    return result

def get_websockets_from_selenium(driver, to_file = False)->bool:
        logger.debug(f"Получаем сообщения об авторизации webSocket из лога браузера (save_to_file={to_file})")
        result = []
        for wsData in driver.get_log('performance'):
            # logger.debug(f"Парсим сообщения из лога браузера -> {wsData}")
            wsJson = json.loads((wsData['message']))
            # logger.debug(f"Преобразовали сообщения из лога браузера в json -> {wsJson}")
            if wsJson["message"]["method"]== "Network.webSocketCreated":
                # print(wsJson["message"]["params"]["url"])
                logger.debug(f"Нашли сообщение Network.webSocketCreate {wsJson}")
                logger.debug(f"Парсим URL")
                url = urlsplit(wsJson["message"]["params"]["url"])
                logger.debug(f"Преобразовали URL -> {url}")
                if 'signalr.agregatoreat.ru'.upper() in url.netloc.upper() and \
                    'AuthorizedHub'.upper() in url.path.upper():
                    logger.debug(f"Это нужные URL AuthorizedHub парсим его параметры -> {url.query}")
                    query = parse_qs(url.query)
                    logger.debug(f"Преобразовали параметры добавляем из в массив результатов-> {query}")
                    result.append(
                        {
                            'id': query.get('id', [''])[0],
                            'v': query.get('v', [''])[0],
                            'access_token': query.get('access_token', [''])[0],
                        }
                    )
        logger.debug(f"Собраны все запросы на соединения websockets -> {result}")
        if to_file:
            logger.debug(f"Сохраняем Websockets в файл -> {PATH_WEBSOCKETS}")
            save_to_file(result, PATH_WEBSOCKETS)
        return result


def get_credentials_selenium(save_to_file = False) -> Credentials:
    try:
        logger.debug("Подготовка Selenium Driver")
        driver = init_selenium_driver() # заходим нас тартовую страницу и ждем загрузку
        logger.debug("Переходим на страницу ввод логина и пароля")
        go_to_login_page(driver) # переходим на страницу входа и ждем загрузку
        logger.debug("Пытаемся войти")
        login(driver) # вводим имя и пароль и входим 
        logger.debug("Получаем cookies")
        cookies = get_cookies_from_selenium(driver, save_to_file)
        logger.debug("Получаем  local storage")
        local_storage = get_localstorage_from_selenium(driver, save_to_file)
        logger.debug("Получаем websockets")
        websock = get_websockets_from_selenium(driver, save_to_file)
        return Credentials(cookies, local_storage, websock)

    except Exception as ex:
        print(f'error - {ex}')
    finally:
        driver.close()
        driver.quit()

############################## Получение через requests  ################################

def create_request_instance():
    """
    Создает сессию для запросов к berezka.
    Т.к. для некоторых запросов нужны cookies
    """
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Encoding':'gzip, deflate, br',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Connection': 'keep-alive',
        # 'Content-Type': 'application/x-www-form-urlencoded',
        # 'Origin': 'https://login.agregatoreat.ru',
        # 'Host': 'login.agregatoreat.ru',
        # 'Referer': payload['Referer'],
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:105.0) Gecko/20100101 Firefox/105.0',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1'
	
    }
    instance = requests.Session()
    instance.headers.update(headers)
    return instance

# **************************************************************** #
def prepare_params_oauth2():
    """
    Генерирует параметры для протокола аутентификации oauth2
    """
    CODE_VERIFIER = generate_code_verifier()
    CODE_CHALLENGE = get_code_challenge(CODE_VERIFIER)
    CODE_VERIFIER=CODE_VERIFIER.decode()
    CODE_CHALLENGE=CODE_CHALLENGE.decode()
    NONCE = get_nonce()
    STATE = get_state()
    result = {
        'client_id': 'eat_ui',
        'redirect_uri': 'https://agregatoreat.ru',
        'response_type': 'code',
        'scope':'openid profile ui-api',
        'nonce': NONCE,
        'state': STATE,
        'code_challenge': CODE_CHALLENGE,
        'code_challenge_method': 'S256',
        'registerUrl': 'https://agregatoreat.ru/register/supplier',
        'code_verifier': CODE_VERIFIER
    } 
    return result

# **************************************************************** #
def request_login_page(request_instance, params_oauth2):
    """
    Запрос у приложения berezka страницы Login и Password
    """
    url = "https://login.agregatoreat.ru/connect/authorize"

    payload=params_oauth2.copy()
    payload.pop('code_verifier')

    logger.debug(f"Запрос у приложения berezka страницы Login и Password по URL -> {url}")
    logger.debug(f"Параметры запрос страницы Login и Password по URL -> {payload}")

    response = request_instance.request("GET", url, params=payload, allow_redirects=False)
    logger.debug(f"Запрос прошел статус ответа (status) -> {response.status_code}")
    logger.debug(f"Заголовки ответа (headers) -> {response.headers}")

    result = response.headers.get('Location', None)
    logger.debug(f"Cтраница Login и Password находится по URL -> {result}")
    return result

# **************************************************************** #
def parse_login_page(txt):
    """
    Парсит страницу для ввода Login и Password
    Нужно найти ReturnUrl и __RequestVerificationToken
    """
    
    logger.debug(f"Загружаем html страницы входа в BeautifulSoup")
    soup = BeautifulSoup(txt, 'lxml')
    
    logger.debug(f"Поиск тега <script id='login'>...</script>")
    script_body =soup.find(id='login')
    sub_soup =  BeautifulSoup(script_body.text, 'lxml')

    logger.debug(f"Поиск тега <input id='ReturnUrl'>...</input>")
    el_return_url = sub_soup.find(id="ReturnUrl")
    return_url = el_return_url.attrs['value']
    logger.debug(f"Значение ReturnUrl -> {el_return_url}")

    logger.debug(f"Поиск тега <input name='_RequestVerificationToken'>...</input>")
    el_request_verification_token = sub_soup.find('input', {'name':"__RequestVerificationToken"})
    request_verification_token = el_request_verification_token.attrs['value']
    logger.debug(f"Значение __RequestVerificationToken -> {el_return_url}")
    
    return {
        'ReturnUrl':return_url,
        '__RequestVerificationToken':request_verification_token,
    }

# **************************************************************** #
def request_go_to_login_page(request_instance, login_url):
    """
    Загружает страницу для ввода Login и Password
    """
    url = login_url
    logger.debug(f"Запрос контента страницы для ввода Login и Password по URL -> {url}")
    response = request_instance.request("GET", url, allow_redirects=False)
    logger.debug(f"Запрос контента страницы для ввода Login и Password прошел статус ответа -> {response.status_code}")
    logger.debug(f"Заголовки ответа (headers) -> {response.headers}")
    logger.debug(f"Тело ответа (html) -> {response.text}")
    # result = parse_login_page(response.text)
    return response.text

# **************************************************************** #
def request_login(request_instance, payload):
    # url = unquote(unquote(login_url))
    url = f'https://login.agregatoreat.ru/Account/Login'
    data=payload.copy()
    data.pop('Referer')
    params={'ReturnUrl': payload['ReturnUrl']}
    headers = {
        'Origin': 'https://login.agregatoreat.ru',
        'Host': 'login.agregatoreat.ru',
        'Referer': payload['Referer'],
    }
    logger.debug(f"POST запрос аутентификации по URL -> {url}")
    logger.debug(f"Параметры(params) запроса аутентификации -> {params}")
    logger.debug(f"Тело(data) запроса аутентификации -> {data}")
    response = request_instance.request("POST", url, headers=headers,  params=params, data=data, allow_redirects=False)
    logger.debug(f"Запрос аутентификации прошел статус(status_code) ответа -> {response.status_code}")
    logger.debug(f"Заголовки(headers) ответа аутентификации -> {response.headers}")
    result = response.headers.get('Location', None)
    logger.debug(f"Ссылка на страницу по которой можно будет получить коды для token -> {result}")
    return result

# **************************************************************** #
def request_go_to_code_page(request_instance, code_url):
    """
    Загрузка страницы которая содержит коды для запроса token
    """
    url = f'https://login.agregatoreat.ru{code_url}'

    logger.debug(f"Запрос кодов после удачное аутентификации по URL -> {url}")
    response = request_instance.request("GET", url, allow_redirects=False)
    logger.debug(f"Запрос кодов прошел статус ответа -> {response.status_code}")
    logger.debug(f"Заголовки (headers) ответа -> {response.headers}")
    # logger.debug(f"Тело (body) ответа -> {response.headers}")

    url_with_code  =  response.headers.get('Location', None)
    logger.debug(f"Получили ссылку с кодами {url_with_code}")

    logger.debug(f"Парсим ссылку с кодами")
    url_with_code = urlsplit(url_with_code)
    query = parse_qs(url_with_code.query)
    logger.debug(f"Получили code -> {query.get('code', [])[-1]}")
    logger.debug(f"Получили state -> {query.get('state', [])[-1]}")
    logger.debug(f"Получили session_state -> {query.get('session_state', [])[-1]}")

    return {
        'code': query.get('code', [])[-1],
        'state': query.get('state', [])[-1],
        'session_state': query.get('session_state', [])[-1],
    }

# **************************************************************** #
def request_token(payload):
    """
    Запрос token
    """
    url = 'https://login.agregatoreat.ru/connect/token'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:105.0) Gecko/20100101 Firefox/105.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        # 'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://agregatoreat.ru',
        'Connection': 'keep-alive',
        'Referer': 'https://agregatoreat.ru/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
    }

    data = f'grant_type=authorization_code&client_id=eat_ui&code_verifier={payload["code_verifier"]}&code={payload["code"]}&redirect_uri=https://agregatoreat.ru'

    logger.debug(f"Запрос(post) token по URL-> {url}")
    logger.debug(f"Параметры(data) запрос -> {data}")
    response = requests.post(url, headers=headers, data=data)
    logger.debug(f"Запрос token прошел. Cтатус ответа (status) -> {response.status_code}")
    logger.debug(f"Заголовки(headers) ответа -> {response.headers}")
    logger.debug(f"Тело(body) ответа -> {response.text}")

    return response.json()

# **************************************************************** #
def get_credentials_request(to_file = False) -> Credentials:
    logger.debug("Создаем сессию у requests (для сохраниения cookies)")
    request_instance = create_request_instance()
    
    logger.debug("Создаем параметры OAuth2 для начала авторизации на стороне клиента (state, nonce, code_verifier, т.д.)")
    params_oauth2 = prepare_params_oauth2()
    logger.debug(f"Успешно сгенерированы параметры -> {params_oauth2}")
    
    logger.debug(f"Попытка запросить у berezka url страницы для ввода Login и Password")
    login_url = request_login_page(request_instance, params_oauth2)
    
    logger.debug(f"Попытка загрузить страницу для ввода Login и Password")
    html_login_page = request_go_to_login_page(request_instance, login_url)
    
    logger.debug(f"Парсим HTML страницы ввода Login и Password")
    payload_login_page = parse_login_page(html_login_page)
    
    logger.debug(f"Создаем словарь параметров для аутентификации добавляем нужные параметры к к ReturnUrl, __RequestVerificationToken")
    payload_login_page['Username'] = BEREZKA_LOGIN
    payload_login_page['Password'] = BEREZKA_PASSWORD
    payload_login_page['button'] = 'login'
    payload_login_page['RememberLogin'] = 'false'
    payload_login_page['Referer'] = login_url
    
    logger.debug(f"Попытка пройти аутентификацию в приложения BEREZKA")
    code_url = request_login(request_instance, payload_login_page)
    
    logger.debug(f"Попытка загрузить страницу с кодами после удачного аутентификации")
    code_params = request_go_to_code_page(request_instance,code_url)
    
    logger.debug(f"Обновляем словарь со всеми сгенерированными и полученными кодами params_oauth2")
    params_oauth2.update(code_params)

    logger.debug(f"Попытка получить token berezka")
    result = request_token(params_oauth2)
    
    if to_file:
        logger.debug(f"Сохраняем token в localstorage -> {PATH_FILE_LOCALSTORAGE}")
        save_to_file(result, PATH_FILE_LOCALSTORAGE)
    
    return  Credentials({}, result, {})

def get_credentials(transport: TransportCredential = TransportCredential.REQUEST, save_to_file = False) -> Credentials:
    result = None
    if transport == TransportCredential.FILE:
        logger.info("Получение учетных данных через ранее сохраненные файлы -> FILE")
        result = get_credentials_file()
    elif transport == TransportCredential.SELENIUM:
        logger.info("Получить учетные данные через -> SELENIUM")
        result = get_credentials_selenium(save_to_file)
    elif transport == TransportCredential.REQUEST:
        logger.info("Получить учетные данные через -> REQUEST")
        result = get_credentials_request(save_to_file)
    return result