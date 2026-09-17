#!/usr/bin/env bash
set -e

echo "==> Running Database Migrations..."
python manage.py migrate --no-input

echo "==> Collecting Static Files..."
python manage.py collectstatic --no-input || true

if [ -f "/app/initial_data.json" ]; then
    echo "==> Checking if initial data seeding is needed..."
    python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitness.settings')
django.setup()
from fitnessApp.models import Exercise
from django.core.management import call_command
if Exercise.objects.count() == 0:
    print('==> Loading initial_data.json into database...')
    call_command('loaddata', 'initial_data.json')
else:
    print('==> Database already populated, skipping loaddata.')
" || true
fi

echo "==> Starting Server..."
exec "$@"
