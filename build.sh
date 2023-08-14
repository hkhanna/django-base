#!/usr/bin/env bash

# exit on error
set -o errexit

# gpg --import base-fedora.asc

pip install -r requirements/production.txt
npm install --prefix frontend

npm run build --prefix frontend
python manage.py collectstatic --no-input
python manage.py migrate