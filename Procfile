release: python manage.py migrate
# release: python manage.py migrate && python manage.py setup_periodic_tasks
web: gunicorn config.wsgi:application
# worker: celery --app=config.celery worker --loglevel=INFO
