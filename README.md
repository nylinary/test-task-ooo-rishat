# Django + Stripe test task

A small shop that sells items through [Stripe](https://stripe.com): hosted Checkout for single
items and whole orders (with discounts and taxes), plus an embedded Payment Intent flow.

Structured after the [HackSoft Django Styleguide](https://github.com/HackSoftware/Django-Styleguide):
thin views, business logic in **services**, data fetching in **selectors**, and the Stripe SDK
isolated behind an integration layer.

## Endpoints

| Method | Path                          | Description                                                        |
|--------|-------------------------------|--------------------------------------------------------------------|
| GET    | `/item/{id}`                  | HTML page for an item with a **Buy** button                        |
| GET    | `/buy/{id}`                   | JSON `{id, url}` of a Stripe Checkout Session for the item         |
| GET    | `/orders/{id}`                | HTML page for an order (items, discount, tax, total)               |
| GET    | `/orders/{id}/buy`            | Checkout Session for the whole order (coupon + tax rate attached)  |
| GET    | `/orders/{id}/payment-intent` | JSON `{id, client_secret, ...}` of a Payment Intent for the order  |
| GET    | `/`                           | Landing page listing items and orders                              |
| GET    | `/admin/`                     | Django admin (items, orders, discounts, taxes)                     |

Errors follow one contract: `{"message": "...", "extra": {...}}`.

## Implemented bonus tasks

- ✅ Docker / docker-compose (with Postgres)
- ✅ Environment variables for all configuration
- ✅ Django admin for all models
- ✅ Deployable out of the box (Railway-ready: honours `$PORT`, `RAILWAY_PUBLIC_DOMAIN`, `DATABASE_URL`)
- ✅ `Order` model combining several items into one payment
- ✅ `Discount` / `Tax` models, passed to Stripe as a **Coupon** and a **Tax Rate**, so the
  Checkout form itemises them
- ✅ `Item.currency` (USD / EUR) with a Stripe keypair per currency — the item's currency picks
  the keypair; both fall back to the default `STRIPE_*` keypair, so one pair is enough to run
- ✅ Stripe **Payment Intent** (embedded Payment Element on the order page) in addition to
  Checkout Sessions

## Quick start (Docker)

```bash
cp .env.example .env   # put your Stripe test keys in
docker compose up --build
```

Then open <http://localhost:8000>. On start the container applies migrations, creates the admin
user from `DJANGO_SUPERUSER_*`, and (when `SEED_DEMO_DATA=True`) seeds demo items and orders.

Admin: <http://localhost:8000/admin/> — credentials come from `.env`
(`admin` / `admin12345` with the example file).

Pay with Stripe's test card: `4242 4242 4242 4242`, any future expiry, any CVC.

## Quick start (no Docker)

Dependencies are managed with [uv](https://docs.astral.sh/uv/) (`pyproject.toml` + `uv.lock`):

```bash
uv sync                # creates .venv from the lockfile, dev tools included
cp .env.example .env   # put your Stripe test keys in

uv run python manage.py migrate
uv run python manage.py ensure_superuser   # reads DJANGO_SUPERUSER_* from .env
uv run python manage.py seed_demo_data     # optional demo items/orders
uv run python manage.py runserver
```

## Configuration

Everything is configured through environment variables (see [.env.example](.env.example)):

| Variable | Purpose |
|----------|---------|
| `STRIPE_PUBLISHABLE_KEY` / `STRIPE_SECRET_KEY` | Default Stripe keypair (used for every currency without its own) |
| `STRIPE_USD_*` / `STRIPE_EUR_*` | Optional per-currency keypairs (two Stripe accounts) |
| `DATABASE_URL` | Postgres connection string; SQLite file when unset |
| `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS` | Standard Django settings |
| `DJANGO_SUPERUSER_USERNAME` / `_PASSWORD` / `_EMAIL` | Admin account created by `manage.py ensure_superuser` |
| `SEED_DEMO_DATA` | `True` → seed demo data on container start |
| `DJANGO_SECURE_HTTPS_ONLY` | Force HTTPS-only cookies/redirects (auto-on on Railway) |

## Deploying to Railway

1. Create a project from this repo — Railway builds the `Dockerfile` automatically.
2. Add a Postgres service; Railway injects `DATABASE_URL` into the app when referenced
   (`${{Postgres.DATABASE_URL}}`).
3. Set the variables: `DJANGO_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_SECRET_KEY`,
   `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD`, and optionally `SEED_DEMO_DATA=True`
   for demo content.
4. Generate a public domain for the service — `RAILWAY_PUBLIC_DOMAIN` is picked up automatically
   (allowed hosts, CSRF origins, HTTPS hardening).

## Tests, linting, types

The toolchain is [Astral](https://astral.sh)'s: **uv** for dependencies, **ruff** for linting and
formatting, **ty** for type checking.

```bash
uv run pytest              # 25 tests; Stripe is mocked at the integration boundary
uv run ruff check .        # lint (incl. flake8-django, bugbear, isort)
uv run ruff format --check .
uv run ty check            # type check (Django-descriptor rules off - no Django plugin yet)
```

## Project layout

```
config/               # settings, urls, wsgi/asgi
pyproject.toml        # uv-managed deps + ruff/ty/pytest config; uv.lock pins everything
shop/
  api/                # DRF exception handler (single error contract)
  catalog/            # Item model, selectors, admin
  orders/             # Order/OrderItem/Discount/Tax, totals selector, order_create service
  payments/           # services mapping models -> Stripe objects; JSON APIs (/buy/{id}, ...)
  integrations/stripe # Stripe SDK isolation: per-currency clients + typed gateway calls
  web/                # server-rendered pages (thin views, selectors only)
  core/               # BaseModel, money helpers, ApplicationError, management commands
templates/, static/   # UI
```

### Notes on the Stripe mapping

- **Checkout Session for an order** sends real line items and attaches the discount as a Stripe
  Coupon and the tax as a Stripe Tax Rate, so the Checkout form shows them as separate lines.
  Created Stripe objects are cached on the models per currency/percentage (Stripe coupons are
  immutable — editing a discount produces a new coupon).
- **Payment Intent** has no line items, so the total (discount applied before tax, mirroring
  Stripe's own order of operations) is computed by `order_totals` and charged as one amount.
- An order must be single-currency — a Stripe payment happens in one currency against one
  keypair; the admin and the services both enforce this.
