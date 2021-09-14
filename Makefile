.PHONY: run api check tailwind all clean build db seed

include .env
SHELL := /bin/bash

# RUNNING AND TESTING #
run: 
	make -j2 api tailwind

api:
	@docker start ${PROJECT_SLUG}-db
	source ../venvs/${PROJECT_SLUG}/bin/activate && python manage.py runserver ${WEB_PORT}

tailwind:
	source ../venvs/${PROJECT_SLUG}/bin/activate && python manage.py tailwind start

check:
	source ../venvs/${PROJECT_SLUG}/bin/activate && py.test

# BUILD STEPS #
all: clean build seed 

clean:
	@echo "Removing python virtual environment"
	rm -rf ../venvs/${PROJECT_SLUG}
	@echo "Removing django-tailwind node_modules"
	rm -rf base/static_src/node_modules

build:
	@echo "Building python virtual environment"
	mkdir -p ../venvs
	python3 -m venv ../venvs/${PROJECT_SLUG}
	source ../venvs/${PROJECT_SLUG}/bin/activate && pip install -r requirements/local.txt
	@echo "Installing django-tailwind node dependencies"
	source ../venvs/${PROJECT_SLUG}/bin/activate && python manage.py tailwind install
	

db:
	@echo "Destroying postgres docker container"
	docker rm -f ${PROJECT_SLUG}-db || true

	@echo "Building postgres docker container"
	docker run --name ${PROJECT_SLUG}-db -e POSTGRES_HOST_AUTH_METHOD=trust -p ${DATABASE_PORT}:5432 -d postgres:13

# The port is forwarded from the standard postgres port (5432) to one that hopefully has no conflicts on the host.
# `-d` detaches the terminal from the container.
# `postgres:13` is intended to mirror the version of postgres available on Heroku.

	sleep 3
	@echo "Running migrations"
	source ../venvs/${PROJECT_SLUG}/bin/activate && python manage.py migrate

seed: db
	@echo "Seeding database"
	source ../venvs/${PROJECT_SLUG}/bin/activate && python manage.py seed_db
