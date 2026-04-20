# PoC классификации SMS SPAM/HAM (Ollama + FastAPI + Docker)

Этот репозиторий содержит proof-of-concept сервис для анализа SMS на спам с помощью LLM. Выполнено задание на четвёрку.

## Что реализовано

- Контейнер на базе Ubuntu с Python (без slim-образа).
- Сервер Ollama работает внутри контейнера.
- Модель `qwen2.5:0.5b` загружается и используется внутри контейнера.
- FastAPI-обертка с единым endpoint для пересылки запроса в Ollama:
  - `POST /generate`
- Порт FastAPI проброшен наружу через Docker Compose (`8000:8000`).

## Файлы проекта

- `Dockerfile` - сборка образа Ubuntu + Python + Ollama + приложение
- `docker-compose.yml` - конфигурация сервиса и публикация порта
- `start.sh` - старт Ollama, ожидание готовности, проверка/загрузка модели, запуск FastAPI
- `app/main.py` - FastAPI приложение и endpoint `POST /generate`
- `requirements.txt` - Python-зависимости

## Воспроизводимая инструкция по установке и запуску

### Предусловия

1. Запущен Docker.
2. Доступен порт `8000` на хосте.
3. Выполняете команды из папки проекта.

### Первый запуск (установка)

```bash
cd /home/nero/Projects/nlp_l2
docker compose up --build -d
```

Проверка, что контейнер поднят:

```bash
docker compose ps
```

Ожидаемый статус: `Up` у сервиса `llm-service`/контейнера `llm-spam-poc`.

Проверка, что модель есть внутри контейнера:

```bash
docker exec llm-spam-poc ollama list
```

Ожидается строка с `qwen2.5:0.5b`.

### Проверка Ollama внутри контейнера

```bash
docker exec llm-spam-poc curl -sS http://127.0.0.1:11434/api/tags

docker exec llm-spam-poc curl -sS -X POST http://127.0.0.1:11434/api/generate \
  -H 'Content-Type: application/json' \
  -d '{"model":"qwen2.5:0.5b","prompt":"Classify: FREE money now, click link. Reply only SPAM or HAM.","stream":false}'
```

### Проверка FastAPI снаружи контейнера

```bash
curl -sS http://127.0.0.1:8000/health
```

Ожидаемый ответ:

```json
{"status":"ok"}
```

Проверка endpoint проксирования:

```bash
curl -sS -X POST http://127.0.0.1:8000/generate \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Вы — классификатор SMS-спама. Верните ровно один токен: SPAM или HAM. SMS: Вы выиграли 10000 рублей, нажмите http://fake-bank.example"}'
```

Ожидаемый формат ответа:

```json
{"model":"qwen2.5:0.5b","response":"SPAM"}
```

## Повторный запуск БЕЗ повторной загрузки Ollama/модели

Остановить и запустить заново (модель сохранится в Docker volume):

```bash
cd /home/nero/Projects/nlp_l2
docker compose down
docker compose up -d
```

Важно: не используйте команды, удаляющие volume, иначе модель придется скачивать заново.

Не выполнять:

- `docker compose down -v`
- `docker volume rm nlp_l2_ollama_models`
- `docker system prune --volumes`

## Остановка сервиса

```bash
cd /home/nero/Projects/nlp_l2
docker compose down
```

## Примеры prompt и фактические результаты (SPAM/HAM)

Ниже примеры из реального запуска этого PoC через `POST /generate`.

### Пример 1 (SPAM)

Prompt:

```text
You are an SMS anti-spam classifier. Return exactly one token: SPAM or HAM.
SMS: Поздравляем! Вы выиграли 100000 рублей. Перейдите по ссылке http://fast-cash.example
```

Результат:

```json
{"model":"qwen2.5:0.5b","response":"SPAM"}
```

### Пример 2 (HAM)

Prompt:

```text
You are an SMS anti-spam classifier. Return exactly one token: SPAM or HAM.
SMS: Папа, купи хлеб и молоко по дороге домой.
```

Результат:

```json
{"model":"qwen2.5:0.5b","response":"HAM"}
```

### Пример 3 (HAM)

Prompt:

```text
You are an SMS anti-spam classifier. Return exactly one token: SPAM or HAM.
SMS: Напоминаю о визите к врачу завтра в 10:30.
```

Результат:

```json
{"model":"qwen2.5:0.5b","response":"HAM"}
```

### Пример 4 (ошибка модели)

Prompt:

```text
You are an SMS anti-spam classifier. Return exactly one token: SPAM or HAM.
SMS: Мама, я задерживаюсь на 20 минут, буду дома к 19:30.
```

Фактический результат этого запуска:

```json
{"model":"qwen2.5:0.5b","response":"SPAM"}
```

Это нормальный эффект для маленькой модели 0.5B и как раз демонстрирует исследовательский характер PoC.
