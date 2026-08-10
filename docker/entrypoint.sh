#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py ensure_superuser

if [ "${SEED_DEMO_DATA:-False}" = "True" ]; then
    python manage.py seed_demo_data
fi

exec "$@"
