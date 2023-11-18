#!/usr/bin/env bash

# exit on error
set -o errexit

pip install -r requirements/production.txt
npm install --prefix frontend

python manage.py collectstatic --no-input
python manage.py migrate
python manage.py setup_periodic_tasks