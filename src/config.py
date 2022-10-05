import os
from dotenv import load_dotenv
import logging
from datetime import datetime
DATE_START = datetime.now()


class ColorLogFormatter(logging.Formatter):

    grey = '\x1b[38;21m'
    blue = '\x1b[38;5;39m'
    yellow = '\x1b[38;5;226m'
    red = '\x1b[38;5;196m'
    bold_red = '\x1b[31;1m'
    green = '\033[32m'
    reset = '\x1b[0m'
    
    def __init__(self, fmt):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.blue + self.fmt + self.reset,
            logging.INFO: self.green + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# PATH_DRIVER = os.path.join(BASE_DIR, 'lib', 'geckodriver')
PATH_DRIVER = os.path.join(BASE_DIR, 'lib', 'chromedriver')
HOME_URL = 'https://agregatoreat.ru/'

PATH_FILE_COOKIES = os.path.join(BASE_DIR, 'data', 'cookies.json')
PATH_FILE_LOCALSTORAGE = os.path.join(BASE_DIR, 'data', 'localstorage.json')
PATH_WEBSOCKETS = os.path.join(BASE_DIR, 'data', 'websockets.json')
PATH_DIR_LOGS = os.path.join(BASE_DIR, 'logs')

BEREZKA_LOGIN = os.getenv('BEREZKA_LOGIN')
BEREZKA_PASSWORD = os.getenv('BEREZKA_PASSWORD')

DEBUG = os.getenv('DEBUG') if os.getenv('DEBUG') is not None else False

RABBITMQ_HOST= os.getenv('RABBITMQ_HOST') if os.getenv('RABBITMQ_HOST') is not None else 'localhost'
RABBITMQ_QUEUE=os.getenv('RABBITMQ_QUEUE') if os.getenv('RABBITMQ_QUEUE') is not None else 'ws_berezka'
