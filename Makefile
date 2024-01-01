.PHONY: run app check vite all all-docker clean build mypy db clear-db migrate seed docker-db

include .env
SHELL := /bin/bash
DB_NAME = $(shell basename $(CURDIR))-db

# RUNNING AND TESTING #
run: 
	(make vite & make app & wait)

app:
	source .venv/bin/activate && python manage.py runserver_plus ${WEB_PORT}

vite:
	npm run dev --prefix frontend/

check: mypy tsc
	source .venv/bin/activate && py.test -n auto

mypy:
	-source .venv/bin/activate && mypy .

tsc:
	-npm run tsc --prefix frontend/

playwright:
	source .venv/bin/activate && py.test --headed --slowmo 250 */tests/test_playwright.py

fmt:
	find -name *.html -not -path "*node_modules*" -a -not -path "*.git*" -a -not -path "*.venv*" | xargs djhtml -i -t 2

shell:
	source .venv/bin/activate && python manage.py shell_plus

# BUILD STEPS #
all: clean build db

all-docker: clean build docker-db migrate seed

clean:
	@echo "Removing python virtual environment"
	rm -rf .venv
	@echo "Removing vite node_modules"
	rm -rf frontend/node_modules
	rm -rf frontend/dist

build:
	@echo "Building python virtual environment"
	python3.11 -m venv .venv
	source .venv/bin/activate && pip install --upgrade pip
	source .venv/bin/activate && pip install -r requirements/local.txt
	@echo "Installing vite node dependencies"
	npm install --prefix frontend/
	@echo "Installing playwright"
	source .venv/bin/activate && playwright install

db: clear-db migrate seed

clear-db:
# Make sure this is running on local
# Presumes a local database is running on DATABASE_PORT
	@source .venv/bin/activate && python manage.py shell -c "from django.conf import settings; import sys; sys.exit(0 if settings.ENVIRONMENT == 'local' else 1)"
	@read -p "Proceed to destroy database? (y/N): " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		source .venv/bin/activate && echo "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" | python manage.py dbshell; \
	else \
		echo "Operation cancelled."; \
		exit 1; \
	fi

migrate:
	@echo "Running migrations"
	source .venv/bin/activate && python manage.py migrate

seed: 
	@echo "Seeding database"
	source .venv/bin/activate && python manage.py seed_db

docker-db:
# Use docker-db to run the database in a docker container if you don't have one running locally.
# The port is forwarded from the standard postgres port (5432) to one that hopefully has no conflicts on the host.
# `-d` detaches the terminal from the container.
# `postgres:15` is intended to mirror the version of postgres available on Render / Heroku.

	@echo "Destroying postgres docker container"
	docker rm -f ${DB_NAME} || true

	@echo "Building postgres docker container"
	docker run --name ${DB_NAME} -e POSTGRES_HOST_AUTH_METHOD=trust -p ${DATABASE_PORT}:5432 -d postgres:15

	@echo "Starting docker container"
	@docker start ${DB_NAME}

