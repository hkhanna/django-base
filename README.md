# base-django

This repository is used as a template repository that I can clone for any new Django project. Those projects should keep this repo as a "base" remote so changes to this base repository can be easily merged into the children projects.

Generally, you'll want to avoid making too many changes to the `base` app to avoid merge conflicts when you merge in updates to this base repo. In other words, put as much as you can into different apps, although some changes to the `base` app may be unavoidable.

## Creating a new Django project from `base-django`

I'll write this when it happens, but I envision a process that might look like this:

- Pick a project name and make sure it's available on Heroku.
- Clone the repo and rename the `origin` remote to `base`.
- Point the `origin` remote to a fresh Github repo.
- Remove or replace the LICENSE file.
- Find and replace `base-django` with the new project name.
- Update `SITE_CONFIG`
- Create a Postmark server if using email
- Deploy to Heroku
  1. Create the application in the Heroku web interface with the project name.
  1. Provision the postgresql add-on in the Heroku web interface
     - Note: if you didn't do this, a Heroku postgres database would be automatically provisioned and added to the `DATABASE_URL` environment variable if your app were successfully deployed. However, because deployment requires that variable to be set, a deployment will fail unless the database is provisioned first.
  1. If using celery, provision the redis add-on in the Heroku web interface which will automatically set the `REDIS_URL` environment variable used by celery.
  1. Set environment variables in production though the dashboard.
     - `DJANGO_SETTINGS_MODULE=config.settings.production`
     - `DJANGO_SECRET_KEY=<random key>`
       - You can generate this random key with something like `openssl rand -base64 64`.
     - `LOGLEVEL=INFO`
       - Without this, it will use the default of `DEBUG`.
     - `STRIPE_API_KEY` if using billing.
     - `POSTMARK_API_KEY` if using email
  1. The nodejs buildpack was added to support Tailwind CSS with `heroku buildpacks:add --index 1 heroku/nodejs --app <project_name>`. (Update this if this fails because this is being done before the first deployment, the python buildpack might not be detected yet.)
  1. Connect Heroku to Github. Enable Automatic Deploys from `main` once CI has passed. You can push directly to `main` or do a PR into `main` and it will deploy once CI passes.
  1. Make sure Heroku is installed
  1. `heroku login` to log into Heroku account if you are not already logged in (check with `heroku auth:whoami`).
  1. Set up postgres backups: `heroku pg:backups schedule --at '02:00 America/New_York' DATABASE_URL --app <project_name>`
  1. Make sure there aren't any obvious issues in production: `heroku run python manage.py check --deploy --app <project_name>`
  1. If using celery, give the celery worker one dyno: `heroku ps:scale main_worker=1 --app <project_name>`
  1. If the web worker doesn't seem to be running, give it one dyno: `heroku ps:scale web=1 --app <project_name>`
  1. Add papertrail via the Heroku interface and set up alerts as per "Deployment" below.
  1. Create the first superuser on production: `heroku run python manage.py createsuperuser --app <project_name>`
  1. Update the Site name and domain in the Django admin.
  1. You should be good to go. If you want to poke around, you can run `heroku run python manage.py shell --app <project_name>`.
- Update "Deployment", below, as appropriate.
- **Delete everything in this README** until "Local Development" and add anything appropriate to the new README.

## Local Development

### Prerequisites

- Docker (for postgres).
- Python 3.8+

### Local Installation

- Clone the repo: `git clone git@github.com:hkhanna/base-django.git`
- From within the repo directory, run `make all`
  - N.B. that the Makefile assumes or creates a folder named `../venvs/` outside of this project directory where you keep all your venvs.

### Running Locally

- `make run` will load the application at `localhost:8007`.
  - The `django-tailwind` packages allows us to use TailwindCSS. The `make tailwind` command builds and watches the development `styles.css`. If you don't run that command (or `make run` which includes that command) and start adding classes to templates, styles randomly won't work because of the way the jit builder works.

### Testing

- `make check` will run all tests. You can also directly run `py.test` if you have the virtualenv activated.

### Updating Packages

- Python: `piprot` is not maintained but really useful. I'd use that for now.

# Deployment

- Hosted on Heroku
- The database is the PostgreSQL Heroku add-on which has automated nightly backups.
- Backend logging to Papertrail via Heroku.
  - Papertrail sends a pushover anytime the the logs match `at=ERROR OR at=CRITICAL`. It should send the email a maximum of once a day.
  - You cannot just look for `error` because they will match admin filtering for errors. You cannot look for `error -at=INFO` because something is emitting a log in Heroku with every request that doesn't include the `at=LEVEL`. It could be gunicorn, but after spending half a day on it, I've given up.

## How to Deploy

- Push to `origin/main` and it will automatically trigger a deploy to Heroku (after CI passes).

## Production Environment Variables

- `DJANGO_SETTINGS_MODULE=config.settings.production`
- `DJANGO_SECRET_KEY=<random key>`
  - You can generate this random key with something like `openssl rand -base64 64`.
- `LOGLEVEL=INFO`
  - Without this, it will use the default of `DEBUG`.
