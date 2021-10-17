release: python manage.py migrate
web: gunicorn config.wsgi:application
# main_worker: celery --app=config.celery worker --loglevel=INFO