# Job Radar MVP — Полный План Тестирования 🧪

**Дата**: Сентябрь 17, 2026  
**Версия**: 1.0  
**Статус**: Testing Phase

---

## 📋 Таблица Тестирования API

### Уже Протестировано ✅

| Endpoint | Метод | Status | Ответ |
|----------|-------|--------|-------|
| `/health` | GET | 200 | `{"status":"healthy","timestamp":"2026-09-17T08:14:19.858189","version":"0.1.0"}` |
| `/api/jobs` | GET | 200 | JSON array with 3 job cards (paginated) |

### Требует Тестирования 🔄

| Endpoint | Метод | Ожидаемый Result | Критическая? |
|----------|-------|-----------------|--------------|
| `/api/docs` | GET | Swagger/OpenAPI UI | Да (dev tools) |
| `/api/sources` | GET | JSON list of 5 sources | Нет (info endpoint) |
| `/api/jobs/{id}` | GET | Single job details | Да (detail view) |
| `/admin` | GET | Admin dashboard HTML | Нет (admin only) |
| `/webhook/telegram` | POST | Process updates | Да (bot integration) |

---

## 🔍 Отладка `/api/docs` Endpoint (Status 404)

### Возможные Причины:

1. **FastAPI не инициализирован с docs_url**
2. **Маршрут переопределен или отключен**
3. **CORS или middleware проблема**
4. **Приложение еще инициализируется**

### Пошаговое Решение:

#### Шаг 1: Проверить main.py конфигурацию

Убедитесь в `main.py` есть:

```python
from fastapi import FastAPI

app = FastAPI(
    title="Job Radar API",
    description="Job market intelligence for Trójmiasto",
    version="0.1.0",
    docs_url="/api/docs",           # ✓ Явно установлено
    redoc_url="/api/redoc",         # ✓ Альтернативная документация
    openapi_url="/api/openapi.json" # ✓ OpenAPI schema
)

# Затем все routes определены относительно app
@app.get("/health")
def health_check():
    ...

@app.get("/api/jobs")
def get_jobs():
    ...
```

#### Шаг 2: Проверить последовательность инициализации

Убедитесь:
1. ✅ `app = FastAPI(...)` определен ПЕРВЫМ
2. ✅ Все `@app.route()` определены ДО `if __name__ == "__main__"`
3. ✅ Middleware добавлены после определения routes
4. ✅ CORS конфигурация не блокирует документацию

#### Шаг 3: Перезагрузить Replit приложение

В Replit:
1. Нажмите **Run** или **Stop** → **Run** (полный перезагрузка)
2. Подождите 3-5 секунд для инициализации
3. Нажмите **Publish** получить свежий URL
4. Попробуйте доступ: `https://<your-replit-url>/api/docs`

#### Шаг 4: Проверить логи ошибок

В Replit Console посмотрите:
```
ERROR: Could not find docs endpoint
ERROR: 404 Not Found for /api/docs
```

Если видите ошибку, сообщите текст ошибки для диагностики.

#### Шаг 5: Альтернативный Доступ к Документации

Если `/api/docs` не работает, используйте:
- **Redoc**: `https://<url>/api/redoc`
- **OpenAPI Schema**: `https://<url>/api/openapi.json`
- **Swagger UI (standalone)**: https://editor.swagger.io/
  - Скопируйте URL: `https://<your-url>/api/openapi.json` в Swagger Editor

---

## 🔗 Тестирование Остальных Endpoints

### 1️⃣ Test `/api/sources` (Info Endpoint)

**Цель**: Проверить доступность источников

```bash
# cURL команда
curl -X GET "https://job-radar-2-zip--pavloborysovets.replit.app/api/sources" \
  -H "Accept: application/json"

# Ожидаемый ответ (200 OK):
{
  "sources": [
    {
      "id": 1,
      "name": "pracuj.pl",
      "url": "https://pracuj.pl",
      "status": "active",
      "last_updated": "2026-09-17T08:00:00"
    },
    {
      "id": 2,
      "name": "OLX",
      "url": "https://olx.pl",
      "status": "active",
      "last_updated": "2026-09-17T08:00:00"
    },
    // ... еще 3 источника
  ],
  "total": 5
}
```

**Проверка**:
- [ ] Status код: 200
- [ ] Возвращает массив sources
- [ ] Каждый источник имеет: id, name, url, status, last_updated

### 2️⃣ Test `/api/jobs/{id}` (Detail Endpoint)

**Цель**: Проверить детальный просмотр вакансии

```bash
# Получить первую вакансию (ID=1)
curl -X GET "https://job-radar-2-zip--pavloborysovets.replit.app/api/jobs/1" \
  -H "Accept: application/json"

# Ожидаемый ответ (200 OK):
{
  "id": 1,
  "title": "Python Developer",
  "company": "TechCorp",
  "location": "Gdańsk",
  "salary_min": 7000,
  "salary_max": 11000,
  "currency": "PLN",
  "contract_type": "Full-time",
  "remote": false,
  "description": "We are looking for...",
  "requirements": "Python 3.9+, FastAPI, PostgreSQL",
  "benefits": ["Health insurance", "Home office"],
  "source_id": 1,
  "published_at": "2026-09-17T07:30:00",
  "url": "https://pracuj.pl/job/123456"
}
```

**Проверка**:
- [ ] Status код: 200
- [ ] Все поля присутствуют
- [ ] Данные соответствуют укладу jobs списка
- [ ] Попробуйте ID 2 и 3 тоже

### 3️⃣ Test `/admin` Dashboard

**Цель**: Проверить admin панель

```bash
# Открыть в браузере
https://job-radar-2-zip--pavloborysovets.replit.app/admin

# Ожидаемая страница должна показать:
- Statistics (total users, jobs, sources)
- User list table
- Recent jobs
- Source status
- Action buttons
```

**Проверка**:
- [ ] Страница загружается без ошибок
- [ ] HTML отображается корректно
- [ ] Таблицы содержат данные
- [ ] CSS стили применяются

---

## 🤖 Telegram Bot Testing

### Предусловия:

1. ✅ У вас есть **Telegram bot token** от BotFather
   - Если нет: https://t.me/botfather → /newbot

2. ✅ Bot token установлен в Replit Secrets как `TELEGRAM_BOT_TOKEN`

3. ✅ `DATABASE_URL` установлена на SQLite: `sqlite:///./job_radar.db`

4. ✅ Приложение запущено на Replit и имеет публичный URL

### Конфигурация Telegram Webhook:

#### Вариант A: Через API (Рекомендуется)

```bash
# Заменить <BOT_TOKEN> и <YOUR_URL>
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook" \
  -d "url=https://job-radar-2-zip--pavloborysovets.replit.app/webhook/telegram"

# Ожидаемый ответ:
{
  "ok": true,
  "result": true,
  "description": "Webhook was set"
}
```

#### Вариант B: Проверить текущий webhook

```bash
curl -X GET "https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo"

# Должен вернуть:
{
  "ok": true,
  "result": {
    "url": "https://job-radar-2-zip--pavloborysovets.replit.app/webhook/telegram",
    "has_custom_certificate": false,
    "pending_update_count": 0,
    "last_error_date": null,
    "last_error_message": null
  }
}
```

### Шаги Тестирования Bot:

#### 1️⃣ Отправить `/start` команду боту

Откройте Telegram и найдите вашего бота (название из BotFather).

Отправьте: `/start`

**Ожидаемая реакция**:
```
Привет! 👋 Добро пожаловать в Job Radar

Выберите язык / Choose language:
[Русский 🇷🇺] [English 🇬🇧] [Polski 🇵🇱] [Українська 🇺🇦]
```

**Проверка**:
- [ ] Сообщение приходит быстро (<2 сек)
- [ ] Кнопки отображаются корректно
- [ ] Сообщение на том же языке, что выбран по умолчанию

#### 2️⃣ Выбрать язык

Нажмите на кнопку **Русский 🇷🇺** (или другой)

**Ожидаемая реакция**:
```
Спасибо! Вы выбрали Русский.

Теперь давайте установим географию поиска.
Трёхместие (Gdańsk, Gdynia, Sopot) + 30km радиус
Это хорошо для вас? 

[Да, это OK ✓] [Нет, другой город ✗]
```

**Проверка**:
- [ ] Bot переходит в следующее состояние FSM
- [ ] Язык переключен на русский
- [ ] Кнопки имеют правильные эмодзи

#### 3️⃣ Подтвердить географию

Нажмите **Да, это OK ✓**

**Ожидаемая реакция**:
```
Отлично! Теперь расскажите о типе работы, которую вы ищете:

[Введите текст вручную] [Используйте голос 🎤]

Подсказка: "Python developer, full-time, начиная с 7000 PLN"
```

**Проверка**:
- [ ] Входящие кнопки пропадают
- [ ] Поле для текста готово
- [ ] Можно вводить текст

#### 4️⃣ Ввести критерии поиска

Отправьте сообщение:
```
Python developer, full-time, minimum 7000 PLN, Gdańsk or Gdynia
```

**Ожидаемая реакция**:
```
Спасибо! Вы ищете:
- Роль: Python developer
- Тип: Full-time
- Зарплата: минимум 7000 PLN
- Города: Gdańsk, Gdynia

Это правильно? 

[Да, поискать! ✓] [Нет, переделать ✗]
```

**Проверка**:
- [ ] Bot распознал основные критерии
- [ ] Критерии отображены правильно
- [ ] Кнопки подтверждения видны

#### 5️⃣ Получить результаты

Нажмите **Да, поискать! ✓**

**Ожидаемая реакция**:
```
Ищу подходящие вакансии... ⏳

[После 1-2 секунд:]

Найдено 3 результата! 🎯

📋 Вакансия 1/3:
💼 Python Developer
🏢 TechCorp
📍 Gdańsk
💰 7000-11000 PLN / месяц
⏱️ Full-time
🔗 View on pracuj.pl

Соответствие: 95/100 ✨
Причина: Все критерии совпадают!

[👍 Нравится] [👎 Не нравится] [🔎 Показать больше деталей]
```

**Проверка**:
- [ ] Результаты получены в течение 3 сек
- [ ] Данные вакансии отображены корректно
- [ ] Оценка соответствия показана (0-100)
- [ ] Кнопки обратной связи видны

#### 6️⃣ Навигация по результатам

Нажмите [👍 Нравится] или [👎 Не нравится]

**Ожидаемая реакция**:
```
Спасибо за отзыв! 📝

Вот следующая вакансия:

📋 Вакансия 2/3:
💼 Construction Manager
[... similar format ...]

[After 3 cards]

Вы просмотрели все доступные вакансии из пробного периода! 

Хотите видеть больше?

💳 Upgrade to Plus Plan
- 100 вакансий в день
- Расширенный поиск
- Рейтинги компаний

[Узнать стоимость 💰] [Может быть позже ➡️]
```

**Проверка**:
- [ ] Результаты переключаются
- [ ] После 3 карточек показывается upsell
- [ ] Обратная связь сохраняется (можно проверить в БД)

### Проверка Логов и Отладка

Если bot не отвечает:

#### 1️⃣ Проверить Webhook Status

```bash
curl -s "https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo" | jq .result
```

Посмотрите на:
- `url` — правильно ли установлен URL?
- `pending_update_count` — есть ли ожидающие обновления?
- `last_error_message` — есть ли ошибки?

#### 2️⃣ Посмотреть Логи Replit

В консоли Replit должны быть логи вроде:
```
2026-09-17 08:15:23.456 | INFO | Received Telegram update from user 123456789
2026-09-17 08:15:23.457 | INFO | User state: LANGUAGE_SELECTION
2026-09-17 08:15:23.458 | INFO | Sending message: "Select language..."
```

Если видите ошибки (ERROR, EXCEPTION), скопируйте текст полностью.

#### 3️⃣ Проверить Database

Убедитесь, что база создана и имеет данные:

```bash
# На Replit, открыть Shell
python -c "
from database import SessionLocal
from models import User, SearchProfile

# Проверить пользователей
with SessionLocal() as db:
    users = db.query(User).all()
    print(f'Total users: {len(users)}')
    for u in users[:5]:
        print(f'  - {u.telegram_id}: {u.language}')
"
```

---

## ✅ Чек-лист Завершения Тестирования

### API Endpoints (3/5)
- [x] GET `/health` — PASSED
- [x] GET `/api/jobs` — PASSED
- [ ] GET `/api/docs` — TODO (fix 404)
- [ ] GET `/api/sources` — TODO
- [ ] GET `/api/jobs/{id}` — TODO

### Web Interface (1/2)
- [x] FastAPI app — RUNNING
- [ ] `/admin` dashboard — TODO

### Telegram Bot (0/6)
- [ ] Webhook configured
- [ ] /start command works
- [ ] Language selection FSM works
- [ ] Geography confirmation works
- [ ] Search criteria input works
- [ ] Results display with proper formatting

### Integration (0/3)
- [ ] Database saves user data
- [ ] Rankings algorithm works correctly
- [ ] LLM (Claude) integration (if configured)

---

## 📊 Expected Performance Metrics

```
Latency:
  /health          : <100ms ✓
  /api/jobs        : <200ms ✓
  /api/docs        : <150ms (after fix)
  Telegram response: <2 sec  (after webhook)

Accuracy:
  Job ranking      : ~85% (subjective)
  Language detect  : >90%
  Criteria parsing : ~80%

Uptime:
  Replit app       : 99%+ (free tier)
  Telegram webhook : >95% (telegram's infrastructure)
```

---

## 🔗 Полезные Ссылки

- **Telegram Bot API**: https://core.telegram.org/bots/api
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **SQLAlchemy ORM**: https://docs.sqlalchemy.org/
- **Replit Deployment**: https://docs.replit.com/
- **Your Bot**: @job_radar_bot (update with your actual bot name)

---

## 📝 Регистрация Результатов

После каждого теста заполните:

```
[Date: 2026-09-17]
[Time: 14:30 UTC]
[Tester: Pavlo]

✅ PASSED: /health endpoint
✅ PASSED: /api/jobs endpoint
❌ FAILED: /api/docs returns 404
⏳ PENDING: /api/sources (not tested yet)

Notes:
- Application responding quickly
- Need to investigate docs endpoint
- Database seeding successful

Next: Fix /api/docs, then test bot
```

---

**Status**: 🧪 In Testing Phase  
**Priority**: HIGH (Complete before production)  
**Owner**: Pavlo  

**Last Updated**: 2026-09-17 08:45 UTC
