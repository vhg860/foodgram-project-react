# Проект Foodgram 
 
[![Build Status](https://github.com/vhg860/foodgram-project-react/actions/workflows/main.yml/badge.svg)](https://github.com/vhg860/foodgram-project-react/actions) 
 
Foodgram - это веб-приложение, предоставляющее пользователям возможность делиться и находить рецепты, добавлять их в избранное, а также создавать список покупок для приготовления блюд. 
 
## Описание проекта 
 
Этот проект представляет собой полностью функциональное приложение, состоящее из бэкенд-части, разработанной на Django, и фронтенд-части на React. В проекте использован стек технологий, включающий: 
 
- **Backend**: Django, PostgreSQL (используется в качестве базы данных) 
- **Frontend**: React 
- **Сборка и развертывание**: Docker, GitHub Actions 
 
## Развертывание проекта 
 
Для развертывания проекта необходимо выполнить следующие шаги: 
 
1. Клонировать репозиторий. 
2. Заполнить файл `env` с необходимыми переменными окружения. 
3. Выполнить развертывание с помощью команды `docker-compose up`.
4. Выполнить слудеющие команды:
```
docker compose -f docker-compose.yml exec backend python manage.py migrate
docker compose -f docker-compose.yml exec backend python manage.py load_data
docker compose -f docker-compose.yml exec backend python manage.py load_tags
docker compose -f docker-compose.yml exec backend python manage.py collectstatic
docker compose -f docker-compose.yml exec backend cp -r /app/collected_static/. /backend_static/static
```
## Заполнение файлов окружения (env) 
 
Вам нужно создать файл `.env` и заполнить его следующими переменными окружения: 
 
```dotenv 
Настройки для подключения к базе данных PostgreSQL 
POSTGRES_DB=foodgram 
POSTGRES_USER=foodgram_user 
POSTGRES_PASSWORD=kfoodgram_password 
DB_NAME=foodgram 
DB_PORT=5432 
``` 
### Автор 
[Дмитрий](https://github.com/vhg860)
