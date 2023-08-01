.PHONY: run app check vite all clean build mypy db seed

include .env
SHELL := /bin/bash
DB_NAME = $(shell basename $(CURDIR))-db

# RUNNING AND TESTING #
run: 
	make -j2 vite app

app:
	@docker start ${DB_NAME}
	source .venv/bin/activate && python manage.py runserver ${WEB_PORT}

vite:
	npm run dev --prefix frontend/

check:
	source .venv/bin/activate && py.test

mypy:
	-mypy .

playwright:
	py.test --headed --slowmo 500 */tests/playwright.py

fmt:
	find -name *.html -not -path "*node_modules*" -a -not -path "*.git*" -a -not -path "*.venv*" | xargs djhtml -i -t 2

# BUILD STEPS #
all: clean build seed 

clean:
	@echo "Removing python virtual environment"
	rm -rf .venv
	@echo "Removing vite node_modules"
	rm -rf frontend/node_modules

build:
	@echo "Building python virtual environment"
	python3.10 -m venv .venv
	pip install --upgrade pip
	source .venv/bin/activate && pip install -r requirements/local.txt
	@echo "Installing vite node dependencies"
	npm install --prefix frontend/

build-playwright:
	playwright install
	
db:
	@echo "Destroying postgres docker container"
	docker rm -f ${DB_NAME} || true

	@echo "Building postgres docker container"
	docker run --name ${DB_NAME} -e POSTGRES_HOST_AUTH_METHOD=trust -p ${DATABASE_PORT}:5432 -d postgres:14

# The port is forwarded from the standard postgres port (5432) to one that hopefully has no conflicts on the host.
# `-d` detaches the terminal from the container.
# `postgres:14` is intended to mirror the version of postgres available on Render.

	sleep 3
	@echo "Running migrations"
	source .venv/bin/activate && python manage.py migrate

seed: db
	@echo "Seeding database"
	source .venv/bin/activate && python manage.py seed_db
