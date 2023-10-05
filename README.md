# django-base

See [Usage](./USAGE.md) for instructions on how to use this repository.

## Local Development

### Prerequisites

- PostgreSQL 14 (or Docker)
- Python 3.10
- `libtidy-dev` (e.g., `apt install libtidy-dev` or `brew install tidy-html5`)

### Local Installation

- Clone the repo: `git clone git@github.com:hkhanna/django-base.git`
- Copy `.env.example` to `.env` and make any appropriate changes.
- If you have a database running, from within the repo directory, run `make all`.
- If you do not have a local database running but you do have Docker running, run `make all-docker`.

### Running Locally

- `make run` will load the application at `localhost:WEB_PORT`, where `WEB_PORT` is set in your `.env` file.
  - It also runs the `vite` server, which is needed for bundling tailwind as well as any other custom Javascript you need.

### Testing

- `make mypy` to run a manual typecheck on the repo.
- `make check` will run all tests including playwright.
- `make playwright` will run only E2E tests in headed mode.

### Updating Packages

- Python: `pip-outdated requirements/common.txt` and `pip-oudated requirements/local.txt`.

## Merging upstream "base" changes

- Ensure that there is a `base` remote pointing at the base repo on Github.
- `git fetch base`
- `git merge base/main`.

# Deployment

- Hosted on Render.
- Backend logging to Papertrail.

## How to Deploy

- Push to `origin/main` and it will automatically trigger a deploy to Render.
