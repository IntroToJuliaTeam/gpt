# Тётя Джулия (Модель)

Проект Тёти Джулии можно запустить без использования микросервисной архитектуры, тогда этот репозиторий будет модулем в [основном проекте](https://github.com/IntroToJuliaTeam/bot).

## Клонирование репозитория

```commandline
git clone https://github.com/IntroToJuliaTeam/bot.git
```

## Подготовка

Создайте `.env` файл по аналогии с [.env.example](.env.example).

```
FOLDER_ID=...
KEY_ID=...
ACCOUNT_ID=...
PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
...
-----END PRIVATE KEY-----"

S3_ENDPOINT=https://storage.yandexcloud.net
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
S3_BUCKET=...
S3_PREFIX=""
URL=http://localhost
PORT=8080
```

## Запуск локально

```commandline
uv sync
```

```commandline
uv run -m src.main
```

## Для локальной разработки

Перед началом работы рекомендуется прописать 

```commandline
uv run pre-commit install
```

для работы git хука с линтерами.