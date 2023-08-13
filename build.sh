#!/usr/bin/env bash

# exit on error
set -o errexit

pip install -r requirements/production.txt
npm install --prefix frontend
# gpg --import <project>.asc

npm run build --prefix frontend
python manage.py collectstatic --no-input
python manage.py migrate