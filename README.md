# Blogicum

Сайт для блогов на самые различные темы от путешествий до дизайна.
Пользователи могут писать посты, выбирая время их публикации, прикреплять к ним фото, находить посты по интересующей категории или локации и оставлять к ним комментарии.

## Стек технология

- Python (3.9)
- Django (3.2.16)
- django-bootstrap5 (22.2)

## Как запустить проект

Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:RavenIV/django_sprint4.git
cd django_sprint4
```

Создать и активировать виртуальное окружение:

```
python3 -m venv env
```

- Если у вас Linux/macOS

```
source env/bin/activate
```

- Если у вас windows

```
source env/scripts/activate
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Перейти в директорию /blogicum и выполнить миграции:

```
cd blogicum
python manage.py migrate
```

Перед запуском проекта можно загрузить фикстуры в базу данных:

```
python manage.py loaddata
```

Запустить приложение:
```
python manage.py runserver
```

## Разработчики

* [Irina Vorontsova](https://github.com/RavenIV)