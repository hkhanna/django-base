.PHONY: run api check tailwind all clean build db seed

# include .env
SHELL := /bin/bash

# RUNNING AND TESTING #
run: 
	make -j2 api tailwind

api:
	@docker start base-django-db
	source ../venvs/base-django/bin/activate && python manage.py runserver 8008

tailwind:
	source ../venvs/base-django/bin/activate && python manage.py tailwind start

check:
	source ../venvs/base-django/bin/activate && py.test

# BUILD STEPS #
all: clean build seed 

clean:
	@echo "Removing python virtual environment"
	rm -rf ../venvs/base-django
	@echo "Removing django-tailwind node_modules"
	rm -rf base/static_src/node_modules

build:
	@echo "Building python virtual environment"
	mkdir -p ../venvs
	python3 -m venv ../venvs/base-django
	source ../venvs/base-django/bin/activate && pip install -r requirements/local.txt
	@echo "Installing django-tailwind node dependencies"
	source ../venvs/base-django/bin/activate && python manage.py tailwind install
	

db:
	@echo "Destroying postgres docker container"
	docker rm -f base-django-db || true

	@echo "Building postgres docker container"
	docker run --name base-django-db -e POSTGRES_HOST_AUTH_METHOD=trust -p 5441:5432 -d postgres:13

# The `--name` option makes it so I can easily use commands like `docker stop base-django-db` or `docker start base-django-db`. If I want to remove it completely, `docker rm base-django-db`.
# The port is forwarded from the standard postgres port (5432) to one that hopefully has no conflicts on the host (5438). Feel free to replace 5438 with a different port, but you will then need to set a `DATABASE_URL` environment variable.
# `-d` detaches the terminal from the container.
# `postgres:13` is intended to mirror the version of postgres available on Heroku.

	sleep 3
	@echo "Running migrations"
	source ../venvs/base-django/bin/activate && python manage.py migrate

seed: db
	@echo "Seeding database"
	source ../venvs/base-django/bin/activate && python manage.py seed_db
