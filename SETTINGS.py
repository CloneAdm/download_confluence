import logging
import pathlib
import signal
import sys
import os
import argparse


# LOGGING
#
_log_name = "download_confluence"
_log_path = "logs"
_log_filename = f"{_log_name}.log"
pathlib.Path(_log_path).mkdir(parents=True, exist_ok=True)
LOG_LEVEL = os.getenv("LOG_LEVEL", default="INFO").upper()
DEBUG = os.getenv("DEBUG") is not None
if DEBUG:
    LOG_LEVEL = "DEBUG"
logger = logging.getLogger(_log_name)
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(levelname)-8s - %(message)s [%(module)s %(funcName)s %(lineno)d]",
    handlers=[
        logging.FileHandler(filename=f"{_log_path}/{_log_filename}", mode='a'),
        logging.StreamHandler(),
    ],
)
logger.info(f"=============== НАЧАЛО СЕСИИ ===============")


# Обработка SIGINT и SIGTERM
#
def _signal_handler(sig, frame):
    logger.info(f"Принудительное завершение работы {sig=}, {frame=}")
    sys.exit(0)


signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)
# print('Press Ctrl+C')
# signal.pause()


# SECRETS
#
CONFLUENCE_URL = os.getenv("CONFLUENCE_URL", default="")
CONFLUENCE_AUTH_TOKEN = os.getenv("CONFLUENCE_AUTH_TOKEN", default="")
CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME", default="")
CONFLUENCE_PASSWORD = os.getenv("CONFLUENCE_PASSWORD", default="")
TARGET_DIRECTORY = os.getenv("TARGET_DIRECTORY", default="")
CONFLUENCE_SPACES = os.getenv("CONFLUENCE_SPACES", default="")
CONFLUENCE_PAGE_IDS = os.getenv("CONFLUENCE_PAGE_IDS", default="")

# Создаем парсер аргументов командной строки
parser = argparse.ArgumentParser(description="Скрипт для скачивания с Confluence структуры статей с вложениями и мета-информацией")

# Добавляем параметры запуска скрипта с описанием на русском языке и проверкой типов
parser.add_argument('--confluence-url', type=str, default="", help="URL-адрес Confluence")
parser.add_argument('--confluence-auth-token', type=str, default="", help="Токен аутентификации Confluence")
parser.add_argument('--confluence-username', type=str, default="", help="Имя пользователя Confluence")
parser.add_argument('--confluence-password', type=str, default="", help="Пароль пользователя Confluence")
parser.add_argument('--target-directory', type=str, default="", help="Целевая директория")
parser.add_argument('--confluence-spaces', type=str, nargs='+', default=[], help="Пространства имён Confluence")
parser.add_argument('--confluence-page-ids', type=str, nargs='+', default=[], help="ID страниц Confluence")
parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                    default='INFO', help="Уровень логирования ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']")
parser.add_argument('--debug', action='store_true', help="Включить отладочный режим (имеет приоритет над --log-level)")

# Парсим аргументы командной строки
args = parser.parse_args()

# обновим параметры логирования
if args.debug:
    logging.basicConfig(level=logging.DEBUG)
    logger.setLevel(logging.DEBUG)
else:
    logging.basicConfig(level=args.log_level)
    logger.setLevel(args.log_level)


filename_SECRETS = "SECRETS.py"
if pathlib.Path(filename_SECRETS).is_file():
    import SECRETS

    if hasattr(SECRETS, 'CONFLUENCE_URL'):
        CONFLUENCE_URL = SECRETS.CONFLUENCE_URL

    if hasattr(SECRETS, 'CONFLUENCE_AUTH_TOKEN'):
        CONFLUENCE_AUTH_TOKEN = SECRETS.CONFLUENCE_AUTH_TOKEN

    if hasattr(SECRETS, 'CONFLUENCE_USERNAME'):
        CONFLUENCE_USERNAME = SECRETS.CONFLUENCE_USERNAME

    if hasattr(SECRETS, 'CONFLUENCE_PASSWORD'):
        CONFLUENCE_PASSWORD = SECRETS.CONFLUENCE_PASSWORD

    if hasattr(SECRETS, 'TARGET_DIRECTORY'):
        TARGET_DIRECTORY = SECRETS.TARGET_DIRECTORY

    if hasattr(SECRETS, 'CONFLUENCE_SPACES'):
        CONFLUENCE_SPACES = SECRETS.CONFLUENCE_SPACES

    if hasattr(SECRETS, 'CONFLUENCE_PAGE_IDS'):
        CONFLUENCE_PAGE_IDS = SECRETS.CONFLUENCE_PAGE_IDS

    logger.debug(f"Загрузили файл с секретами: ({filename_SECRETS})")
