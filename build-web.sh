#!/usr/bin/env bash

# exit on error
set -o errexit

# install -d -m 700 /opt/render/project/gnupg && gpg --import django-base.asc

pip install -r requirements/production.txt
npm install --prefix frontend

npm run build --prefix frontend
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py setup_periodic_tasks