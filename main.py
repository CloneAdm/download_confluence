import os
import re
import sys
import logging
import unicodedata
import pathlib
from atlassian import Confluence
from atlassian.errors import ApiNotFoundError
import requests
import SETTINGS
from SETTINGS import logger


def clean_folder_name(folder_name):
    # Удаление Unicode символов из имени папки
    cleaned_name = ''.join(c for c in folder_name if unicodedata.category(c)[0] != 'C')

    all_quotes = r"~'\"“”‘’«»„‚⹂〝〞〟＂＇＜＞［］｢｣'"
    all_hyphens = r"‐‑‒–—―⁃−—➖—"
    cleaned_name = re.sub("[" + re.escape(all_quotes) + "]", "'", cleaned_name)
    cleaned_name = re.sub("[" + re.escape(all_hyphens) + "]", "-", cleaned_name)
    cleaned_name = cleaned_name.rstrip(' .,-')  # удалим символы в конце строки (любое количество)

    # Запрещенные символы в именах папок на разных ОС
    if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
        forbidden_chars = '/'
        translation_table = str.maketrans(forbidden_chars, '_' * len(forbidden_chars))
        cleaned_name = cleaned_name.translate(translation_table)
        return cleaned_name
    elif sys.platform.startswith('win'):
        forbidden_chars = r'\/:*?<>|'
        translation_table = str.maketrans(forbidden_chars, '_' * len(forbidden_chars))
        cleaned_name = cleaned_name.translate(translation_table)
        return cleaned_name
    else:
        raise NotImplementedError("Unsupported operating system")


def download_attachments_from_page(cf_conn, page_id, path):
    attachments_path = os.path.join(path, "attachments")
    if os.path.exists(attachments_path):
        logging.info(f"Папка 'attachments' уже существует (вложения уже скачены) {page_id=}")
        return None
    else:
        try:
            attachments = cf_conn.get_attachments_from_content(page_id=page_id)["results"]
            if not attachments:
                return None
            pathlib.Path(attachments_path).mkdir(parents=True, exist_ok=True)
            for attachment in attachments:
                file_name = attachment["title"]
                if not file_name:
                    file_name = attachment["id"]  # if the attachment has no title, use attachment_id as a filename
                download_link = cf_conn.url + attachment["_links"]["download"]
                r = cf_conn._session.get(f"{download_link}")
                file_path = os.path.join(attachments_path, clean_folder_name(file_name))
                with open(file_path, "wb") as f:
                    f.write(r.content)
        except NotADirectoryError:
            raise NotADirectoryError("Verify if directory path is correct and/or if directory exists")
        except PermissionError:
            raise PermissionError(
                "Directory found, but there is a problem with saving file to this directory. Check directory permissions"
            )
        except Exception as e:
            raise e
        return len(attachments)


def get_src_page(cf_conn, page_id):
    headers = cf_conn.form_token_headers
    url = f"plugins/viewsource/viewpagesrc.action?pageId={page_id}"
    if cf_conn.api_version == "cloud":
        url = cf_conn.get_pdf_download_url_for_confluence_cloud(url)
        if not url:
            logger.error("Failed to get download SRC url.")
            raise ApiNotFoundError("Failed to export page as SRC", reason="Failed to get download SRC url.")
        # To download the SRC file, the request should be with no headers of authentications.
        return requests.get(url, timeout=75).content
    return cf_conn.get(url, headers=headers, not_json_response=True)


def get_storage_page(cf_conn, page_id):
    headers = cf_conn.form_token_headers
    url = f"plugins/viewstorage/viewpagestorage.action?pageId={page_id}"
    if cf_conn.api_version == "cloud":
        url = cf_conn.get_pdf_download_url_for_confluence_cloud(url)
        if not url:
            logger.error("Failed to get download STORAGE url.")
            raise ApiNotFoundError("Failed to export page as SRC", reason="Failed to get download STORAGE url.")
        # To download the STORAGE file, the request should be with no headers of authentications.
        return requests.get(url, timeout=75).content
    return cf_conn.get(url, headers=headers, not_json_response=True)


# Функция для получения иерархии страниц и создания файлов
def dl_all(cf_conn, page_id, current_directory, skip_existing=False):
    page_title = ""
    try:
        page_info = cf_conn.get_page_by_id(page_id)
        page_title = page_info['title']
        logging.info(f"Обработка страницы: {page_id=} {page_title=}")

        # Создаём папку, если она не существует
        folder_name = clean_folder_name(page_title)
        current_path = os.path.join(current_directory, folder_name)
        pathlib.Path(current_path).mkdir(parents=True, exist_ok=True)

        # Проверяем наличие JSON файла
        json_file_path = os.path.join(current_path, 'page_info.json')
        if not os.path.exists(json_file_path) or not skip_existing:
            logging.info(f"Создаём JSON файл: {json_file_path}")
            with open(json_file_path, 'w', encoding='utf-8') as file:
                file.write(str(page_info))
        else:
            logging.info(f"JSON файл уже существует: {json_file_path}")

        # Проверяем наличие PDF файла
        pdf_file_path = os.path.join(current_path, f'{folder_name}.pdf')
        if not os.path.exists(pdf_file_path) or not skip_existing:
            logging.info(f"Скачиваем PDF файл: {pdf_file_path}")
            with open(pdf_file_path, 'wb') as file:
                file.write(cf_conn.get_page_as_pdf(page_id))
        else:
            logging.info(f"PDF файл уже существует: {pdf_file_path}")

        # Проверяем наличие SRC файла
        src_file_path = os.path.join(current_path, f'{folder_name}.src')
        if not os.path.exists(src_file_path) or not skip_existing:
            logging.info(f"Скачиваем SRC файл: {src_file_path}")
            with open(src_file_path, 'wb') as file:
                file.write(get_src_page(cf_conn, page_id))
        else:
            logging.info(f"SRC файл уже существует: {src_file_path}")

        # Проверяем наличие STORAGE файла
        storage_file_path = os.path.join(current_path, f'{folder_name}.storage')
        if not os.path.exists(storage_file_path) or not skip_existing:
            logging.info(f"Скачиваем STORAGE файл: {storage_file_path}")
            with open(storage_file_path, 'wb') as file:
                file.write(get_storage_page(cf_conn, page_id))
        else:
            logging.info(f"STORAGE файл уже существует: {storage_file_path}")

        # Скачиваем прикрепленные файлы
        attachments = download_attachments_from_page(cf_conn, page_id, path=current_path)
        if attachments is not None:
            logging.info(f"Скачали прикреплённые файлы: {attachments} шт.")

        logging.info(f"Страница успешно обработана: {page_id=} {page_title=}")

        # Рекурсивно обрабатываем все дочерние объекты
        children = cf_conn.get_page_child_by_type(page_id, 'page')
        for child in children:
            child_id = child['id']
            dl_all(cf_conn, child_id, current_path, skip_existing)
    except UnicodeEncodeError as e:
        logging.error(f"Ошибка UnicodeEncodeError при обработке страницы: {page_id=} {page_title=}, ошибка: {e}")
    # except FileNotFoundError as e:
    #     logging.error(f"Ошибка FileNotFoundError при обработке страницы: {page_id=} {page_title=}, ошибка: {e}")


def main():
    if SETTINGS.CONFLUENCE_AUTH_TOKEN is not None or SETTINGS.CONFLUENCE_AUTH_TOKEN == "":
        cf = Confluence(url=SETTINGS.CONFLUENCE_URL, token=SETTINGS.CONFLUENCE_AUTH_TOKEN)
    else:
        cf = Confluence(url=SETTINGS.CONFLUENCE_URL, username=SETTINGS.CONFLUENCE_USERNAME, password=SETTINGS.CONFLUENCE_PASSWORD)

    if not pathlib.Path(SETTINGS.TARGET_DIRECTORY).exists():
        pathlib.Path(SETTINGS.TARGET_DIRECTORY).mkdir(parents=True, exist_ok=True)
        logger.info(f"Создаём локальное хранилище: {SETTINGS.TARGET_DIRECTORY}")

    if SETTINGS.CONFLUENCE_SPACES is not None:
        for el in SETTINGS.CONFLUENCE_SPACES:
            space = el.get("space", "")
            title = el.get("title", "")
            if all(param for param in [space, title]):
                space_page_id = cf.get_page_id(space=space, title=title)
                if space_page_id is not None and space_page_id != '':
                    dl_all(cf, space_page_id, SETTINGS.TARGET_DIRECTORY, skip_existing=True)
                else:
                    logger.error(f'По указанным параметрам ({space=}, {title=}) поиск стартовой страницы не удался!')
            else:
                logger.error(f'Переданные параметры не валидны! {space=} {title=}')

    if SETTINGS.CONFLUENCE_PAGE_IDS is not None:
        for page_id in SETTINGS.CONFLUENCE_PAGE_IDS:
            if page_id is not None and page_id != '':
                dl_all(cf, page_id, SETTINGS.TARGET_DIRECTORY, skip_existing=True)
            else:
                logger.error(f'Переданные параметры не валидны! {page_id=}')

    logger.info("Скачивание файлов завершено.")


if __name__ == "__main__":
    main()
