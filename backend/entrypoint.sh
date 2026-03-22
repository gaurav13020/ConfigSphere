#!/bin/sh

echo "Waiting for PostgreSQL to be ready..."

while ! python -c "
import psycopg2, os, sys
try:
    psycopg2.connect(
        dbname=os.environ.get('DB_NAME', 'configsphere'),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', 'postgres'),
        host=os.environ.get('DB_HOST', 'db'),
        port=os.environ.get('DB_PORT', '5432'),
    )
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
    echo "  PostgreSQL not ready yet — retrying in 1s..."
    sleep 1
done

echo "PostgreSQL is ready."

echo "Running migrations..."
python manage.py migrate --noinput

echo "Starting server..."
exec python manage.py runserver 0.0.0.0:8000
