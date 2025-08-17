.PHONY: run app check vite all all-docker clean build mypy ruff tsc db clear-db migrate seed docker-db

include .env
SHELL := /bin/bash
DB_NAME = $(shell basename $(CURDIR))-db

# RUNNING AND TESTING #
run: 
	(make vite & make app & wait)

app:
	uv run python manage.py runserver_plus 127.0.0.1:${WEB_PORT}

vite:
	npm run dev --prefix frontend/

check: mypy tsc ruff
	uv run py.test -n auto

mypy:
	uv run mypy .

ruff:
	uv run ruff check

tsc:
	-npm run tsc --prefix frontend/

playwright:
	uv run py.test --headed --slowmo 250 */tests/test_playwright.py

fmt:
	find -name *.html -not -path "*node_modules*" -a -not -path "*.git*" -a -not -path "*.venv*" | xargs djhtml -i -t 2

shell:
	uv run && python manage.py shell_plus

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
	uv sync
	@echo "Installing vite node dependencies"
	npm install --prefix frontend/
	@echo "Installing playwright"
	uv run playwright install

db: clear-db migrate seed

clear-db:
# Make sure this is running on local
# Presumes a local database is running on DATABASE_PORT
	@uv run python manage.py shell -c "from django.conf import settings; import sys; sys.exit(0 if settings.ENVIRONMENT == 'local' else 1)"
	@read -p "Proceed to destroy database? (y/N): " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" | uv run python manage.py dbshell; \
	else \
		echo "Operation cancelled."; \
		exit 1; \
	fi

migrate:
	@echo "Running migrations"
	uv run python manage.py migrate

seed: 
	@echo "Seeding database"
	uv run python manage.py seed_db

docker-db:
# Use docker-db to run the database in a docker container if you don't have one running locally.
# The port is forwarded from the standard postgres port (5432) to one that hopefully has no conflicts on the host.
# `-d` detaches the terminal from the container.
# `postgres:16` is intended to mirror the version of postgres available on Heroku.

	@echo "Destroying postgres docker container"
	docker rm -f ${DB_NAME} || true

	@echo "Building postgres docker container"
	docker run --name ${DB_NAME} -e POSTGRES_HOST_AUTH_METHOD=trust -p ${DATABASE_PORT}:5432 -d postgres:16

	@echo "Starting docker container"
	@docker start ${DB_NAME}

