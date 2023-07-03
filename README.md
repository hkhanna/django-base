# fedora

See [Usage](./USAGE.md) for instructions on how to use this repository.

## Local Development

### Prerequisites

- Docker (for postgres).
- Python 3.10
- `libtidy-dev` (e.g., `apt install libtidy-dev` or `brew install tidy-html5`)

### Local Installation

- Clone the repo: `git clone git@github.com:hkhanna/fedora.git`
- Copy `.env.example` to `.env` and make any appropriate changes.
- From within the repo directory, run `make all`

### Running Locally

- `make run` will load the application at `localhost:WEB_PORT`, where `WEB_PORT` is set in your `.env` file.
  - It also runs the `vite` server, which is needed for bundling tailwind as well as any other custom Javascript you need.

### Testing

- `make check` will run all tests. You can also directly run `py.test` if you have the virtualenv activated.

### Updating Packages

- Python: `pip-outdated requirements/common.txt` and `pip-oudated requirements/local.txt`.

## Merging upstream "base" changes

- Ensure that there is a `base` remote pointing at the base repo on Github.
- `git fetch base`
- `git merge base/origin`.

# Deployment

- Hosted on Render.
- Backend logging to Logtail.

## How to Deploy

- Push to `origin/main` and it will automatically trigger a deploy to Render.
