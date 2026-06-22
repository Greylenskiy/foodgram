# Foodgram - сервис для публикации рецептов
[![Python](https://img.shields.io/badge/-Python-464646?style=flat&logo=Python&logoColor=56C0C0&color=008080)](https://www.python.org/)
[![Django](https://img.shields.io/badge/-Django-464646?style=flat&logo=Django&logoColor=56C0C0&color=008080)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/-Django%20REST%20Framework-464646?style=flat&logo=Django%20REST%20Framework&logoColor=56C0C0&color=008080)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-464646?style=flat&logo=PostgreSQL&logoColor=56C0C0&color=008080)](https://www.postgresql.org/)
[![Nginx](https://img.shields.io/badge/-NGINX-464646?style=flat&logo=NGINX&logoColor=56C0C0&color=008080)](https://nginx.org/ru/)
[![gunicorn](https://img.shields.io/badge/-gunicorn-464646?style=flat&logo=gunicorn&logoColor=56C0C0&color=008080)](https://gunicorn.org/)
[![Docker](https://img.shields.io/badge/-Docker-464646?style=flat&logo=Docker&logoColor=56C0C0&color=008080)](https://www.docker.com/)
[![Docker-compose](https://img.shields.io/badge/-Docker%20compose-464646?style=flat&logo=Docker&logoColor=56C0C0&color=008080)](https://www.docker.com/)
[![Docker Hub](https://img.shields.io/badge/-Docker%20Hub-464646?style=flat&logo=Docker&logoColor=56C0C0&color=008080)](https://www.docker.com/products/docker-hub)
[![GitHub%20Actions](https://img.shields.io/badge/-GitHub%20Actions-464646?style=flat&logo=GitHub%20actions&logoColor=56C0C0&color=008080)](https://github.com/features/actions)

## 📝 Описание проекта

Foodgram —. это веб-приложение, где пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное, подписываться на других авторов и формировать список покупок из выбранных рецептов.

**Основные возможности:**
- Регистрация и авторизация пользователей
- Создание, редактирование и удаление рецептов
- Добавление рецептов в избранное
- Формирование списка покупок с ингредиентами
- Подписка на авторов
- Фильтрация рецептов по тегам
- Скачивание списка покупок в формате `.txt`

---

## 🌐 Ссылка на работающий сайт

**[Foodgram](http://foodgrey1711.ddns.net/)**

---

## 🛠 Стек технологий

**Бэкенд:**
- Python 3.11
- Django 4.2
- Django REST Framework 3.14
- Djoser (аутентификация)
- PostgreSQL 15
- Gunicorn (WSGI-сервер)

**Фронтенд:**
- React 18
- Redux Toolkit

**Инфраструктура:**
- Docker и Docker Compose
- Nginx (веб-сервер)
- GitHub Actions (CI/CD)
- Yandex Cloud (хостинг)

---

## 🔄 CI/CD

Проект использует GitHub Actions для автоматического деплоя при пуше в ветку `main`.

**Что делает CI/CD:**
1. Проверяет код на соответствие PEP8 (flake8)
2. Запускает тесты
3. Собирает Docker-образы для бэкенда и фронтенда
4. Пушит образы в Docker Hub
5. Подключается к серверу по SSH
6. Обновляет контейнеры на сервере

---

## 🚀 Локальное развертывание с Docker

### 1. Клонирование репозитория

```bash
git clone git@github.com:Greylenskiy/foodgram.git
cd foodgram
```

### 2. Настройка переменных окружения
Создайте файл .env в корне проекта (рядом с docker-compose.yml):
```bash
# PostgreSQL
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=your_password_here
DB_HOST=db
DB_PORT=5432

# Django
DB_ENGINE=django.db.backends.postgresql
SECRET_KEY=your_secret_key_here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,your_domain.com
```

### 3.  Запуск контейнеров

```bash
docker compose up -d
```

### 4.  Подготовка базы данных

```bash
# Применение миграций
docker compose exec backend python manage.py migrate

# Создание суперпользователя
docker compose exec backend python manage.py createsuperuser

# Загрузка ингредиентов
docker compose exec backend python manage.py load_ingredients
```

### 5.  Сборка статики

```bash
docker compose exec backend python manage.py collectstatic --noinput
```

### 6.  Проверка работы

| Адрес                 | Описание |
|:----------------------|:---------|
| http://localhost/             | Главная страница |
| http://localhost/admin/       | Админ-панель |
| http://localhost/api/docs/    | API-документация |

### Используемые библиотеки (Python):

| Библиотка               | Назначение |
|:----------------------|:---------|
|  Django               |  Веб-фреймворк|
| djangorestframework   |REST API |
| djoser                | Аутентификация |
| Pillow                |  Работа с изображениями|
| psycopg2-binary       |Драйвер PostgreSQL |
| gunicorn              | WSGI-сервер |
| python-dotenv         |Переменные окружения |
| gunicorn              | Фильтрация данных |
