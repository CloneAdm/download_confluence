Проект скачивает все страницы с вложениями и мета-информацией с целевого пространства со структурой (в виде папок на диске)

Для работы в файле **main** необходимо задать переменную **page_ids** - указать массив из page_id
Если page_id узнать не удаётся - можно получить нужное пространство чезез:

```python
space_page_id = confluence.get_page_id(space="space", title="title")
```
Можно увидеть в адресной строке вида:
```html
https://some_site/display/[space]/[title]
```

Для запуска скачивания, можно на выбор: 
- скопировать файл [SECRETS_DEFAULT.py](SECRETS_DEFAULT.py) с именем [SECRETS.py](SECRETS.py) и внести все параметры работы в него (по образцам)
- установить переменные окружения (имена переменных аналогичны настройкам в SECRETS.py)
- передать в виде аргументов ```python main.py --help```

запуск: ```python main.py```

API: https://docs.atlassian.com/ConfluenceServer/rest/7.20.0/
