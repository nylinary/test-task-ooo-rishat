# Тестовое задание: Django + Stripe

Небольшой магазин, продающий товары через [Stripe](https://stripe.com): Checkout для
отдельных товаров и целых заказов (со скидками и налогами), плюс встроенная оплата через
Payment Intent.

Архитектура по [HackSoft Django Styleguide](https://github.com/HackSoftware/Django-Styleguide):
тонкие вью, бизнес-логика в **сервисах**, выборка данных в **селекторах**, Stripe SDK
изолирован в интеграционном слое.

## Эндпоинты

| Метод | Путь                          | Описание                                                              |
|-------|-------------------------------|------------------------------------------------------------------------|
| GET   | `/item/{id}`                  | HTML-страница товара с кнопкой **Buy**                                 |
| GET   | `/buy/{id}`                   | JSON `{id, url}` Stripe Checkout Session для товара                    |
| GET   | `/orders/{id}`                | HTML-страница заказа (товары, скидка, налог, итог)                     |
| GET   | `/orders/{id}/buy`            | Checkout Session на весь заказ (с купоном и налоговой ставкой)         |
| GET   | `/orders/{id}/payment-intent` | JSON `{id, client_secret, ...}` Payment Intent на сумму заказа         |
| GET   | `/`                           | Главная страница со списком товаров и заказов                          |
| GET   | `/admin/`                     | Django-админка (товары, заказы, скидки, налоги)                        |

Все ошибки в одном формате: `{"message": "...", "extra": {...}}`.

## Выполненные бонусные задачи

- ✅ Docker / docker-compose (с Postgres)
- ✅ Вся конфигурация через environment variables
- ✅ Все модели доступны в Django-админке
- ✅ Готово к деплою из коробки (Railway: учитываются `$PORT`, `RAILWAY_PUBLIC_DOMAIN`, `DATABASE_URL`)
- ✅ Модель `Order`, объединяющая несколько товаров в один платёж
- ✅ Модели `Discount` / `Tax`, передаваемые в Stripe как **Coupon** и **Tax Rate** — Checkout-форма
  показывает их отдельными строками
- ✅ Поле `Item.currency` (USD / EUR) с отдельным Stripe-кейпаром на каждую валюту — валюта товара
  выбирает кейпар; обе валюты падают обратно на дефолтную пару `STRIPE_*`, так что для запуска
  достаточно одной
- ✅ Stripe **Payment Intent** (встроенный Payment Element на странице заказа) в дополнение
  к Checkout Session

## Быстрый старт (Docker)

```bash
cp .env.example .env   # впишите свои тестовые ключи Stripe
docker compose up --build
```

Откройте <http://localhost:8000>. На старте контейнер применяет миграции, создаёт админа из
`DJANGO_SUPERUSER_*` и (при `SEED_DEMO_DATA=True`) наполняет базу демо-товарами и заказами.

Админка: <http://localhost:8000/admin/> — креды берутся из `.env`
(`admin` / `admin12345` с примером из репозитория).

Оплата тестовой картой Stripe: `4242 4242 4242 4242`, любой будущий срок, любой CVC.

## Быстрый старт (без Docker)

Зависимости управляются через [uv](https://docs.astral.sh/uv/) (`pyproject.toml` + `uv.lock`):

```bash
uv sync                # создаёт .venv из лок-файла, включая dev-инструменты
cp .env.example .env   # впишите свои тестовые ключи Stripe

uv run python manage.py migrate
uv run python manage.py ensure_superuser   # читает DJANGO_SUPERUSER_* из .env
uv run python manage.py seed_demo_data     # опционально: демо-товары и заказы
uv run python manage.py runserver
```

## Конфигурация

Всё настраивается через environment variables (см. [.env.example](.env.example)):

| Переменная | Назначение |
|------------|-----------|
| `STRIPE_PUBLISHABLE_KEY` / `STRIPE_SECRET_KEY` | Дефолтный кейпар Stripe (для валют без собственного) |
| `STRIPE_USD_*` / `STRIPE_EUR_*` | Опциональные кейпары на валюту (два Stripe-аккаунта) |
| `DATABASE_URL` | Строка подключения к Postgres; без неё — файл SQLite |
| `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS` | Стандартные настройки Django; секретный ключ **обязателен** при выключенном `DJANGO_DEBUG`, а список хостов вне DEBUG по умолчанию `localhost,127.0.0.1` (+ домен Railway) |
| `DJANGO_SUPERUSER_USERNAME` / `_PASSWORD` / `_EMAIL` | Аккаунт админа, создаваемый `manage.py ensure_superuser` |
| `SEED_DEMO_DATA` | `True` → наполнить базу демо-данными на старте контейнера |
| `DJANGO_SECURE_HTTPS_ONLY` | Принудительный HTTPS (куки, редиректы); на Railway включается сам |

## Деплой на Railway

1. Создайте проект из этого репозитория — Railway сам соберёт `Dockerfile`.
2. Добавьте сервис Postgres; Railway прокинет `DATABASE_URL` в приложение через референс
   (`${{Postgres.DATABASE_URL}}`).
3. Задайте переменные: `DJANGO_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_SECRET_KEY`,
   `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD` и, при желании, `SEED_DEMO_DATA=True`
   для демо-контента.
4. Сгенерируйте публичный домен сервиса — `RAILWAY_PUBLIC_DOMAIN` подхватится автоматически
   (allowed hosts, CSRF origins, HTTPS-настройки). Для собственного домена добавьте его в
   `DJANGO_ALLOWED_HOSTS` и `DJANGO_CSRF_TRUSTED_ORIGINS` вручную.

## Тесты, линтер, типы

**uv** для зависимостей и **ruff** для линтинга/форматирования (оба — [Astral](https://astral.sh)),
**mypy + django-stubs** для проверки типов: плагин понимает ORM (дескрипторы полей, менеджеры,
nullable FK), поэтому типы проверяются по-настоящему, без отключённых правил.

```bash
uv run pytest              # Stripe замокан на границе интеграции - ключи не нужны
uv run ruff check .        # линт (flake8-django, bugbear, isort и др.)
uv run ruff format --check .
uv run mypy                # типы (django-stubs + drf-stubs)
```

## Структура проекта

```
config/               # settings, urls, wsgi/asgi
pyproject.toml        # зависимости под uv + конфиг ruff/ty/pytest; uv.lock пинит всё
shop/
  api/                # DRF exception handler (единый формат ошибок)
  catalog/            # модель Item, селекторы, админка
  orders/             # Order/OrderItem/Discount/Tax, селектор итогов, сервис order_create
  payments/           # сервисы, маппящие модели в объекты Stripe; JSON API (/buy/{id}, ...)
  integrations/stripe # изоляция Stripe SDK: клиенты по валютам + типизированный gateway
  web/                # серверные страницы (тонкие вьюхи, только селекторы)
  core/               # BaseModel, money-хелперы, ApplicationError, management-команды
templates/, static/   # UI
```

### Заметки о маппинге в Stripe

- **Checkout Session для заказа** отправляет реальные line items и прикрепляет скидку как Stripe
  Coupon, а налог как Stripe Tax Rate — Checkout-форма показывает их отдельными строками.
  Созданные объекты Stripe кэшируются на моделях с ключом из валюты, процента и названия:
  `percent_off` купона в Stripe неизменяем, переименования обрабатываются так же, поэтому любая
  правка в админке создаёт новый купон/ставку вместо устаревших значений в Checkout.
- **У Payment Intent нет line items**, поэтому итог (скидка до налога — в том же порядке, что
  и у Stripe) считается селектором `order_totals` и списывается одной суммой.
- Заказ строго в одной валюте — платёж Stripe проходит в одной валюте через один кейпар;
  это проверяют и админка, и сервисы.
