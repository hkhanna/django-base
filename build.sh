#!/usr/bin/env bash

# exit on error
set -o errexit

pip install -r requirements/production.txt
npm install --prefix base/frontend

npm run build --prefix base/frontend
python manage.py collectstatic --no-input
python manage.py migrate