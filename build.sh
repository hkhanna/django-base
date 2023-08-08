#!/usr/bin/env bash

# exit on error
set -o errexit

pip install -r requirements/production.txt
npm install --prefix frontend

npm run build --prefix frontend
python manage.py collectstatic --no-input
python manage.py rename base core
python manage.py migrate