# Usage

This repository is used as a template repository that I can clone for any new Django project. Those projects should keep this repo as a "base" remote so changes to this base repository can be easily merged into the children projects.

Generally, you'll want to avoid making too many changes to the `base` app to avoid merge conflicts when you merge in updates to this base repo. In other words, put as much as you can into different apps, although some changes to the `base` app may be unavoidable.

# Creating a new Django project from `base-django`

- Pick a suitable project name.
- Clone the repo into the new project name directory. E.g., `git clone git@github.com:hkhanna/base-django.git <project_name>`
- Rename the `origin` remote to `base`: `git remote rename origin base`
- Create a fresh Github repo for the project.
- Point the `origin` remote to a fresh Github repo.
- In the `base-django` repo, add the new application as it's own remote so you can cherry-pick commits if necessary.
- Remove or replace the LICENSE file.
- Update `.env.example` to the desired defaults for the new project.
- Find and replace `base-django` with the new project name.
- Decide if `billing` should be installed at this point.
  - You can always install billing later, but if you know for sure you need it, do it now.
  - To install `billing`:
    - [Follow the instructions](https://github.com/hkhanna/billing) to install the package.
    - Add `billing.mixins.BilingMixin` to the `SettingsView` after `LoginRequiredMixin`.
- Do the "Local Installation" described below.
- Update `SITE_CONFIG`.
- Update the **production** `GA_TRACKING_ID` setting if using Google Analytics. Leave as `None` to keep Google Analytics off.
- Update the **production** `SENTRY_DSN` setting if using Sentry. Leave as `None` to keep Sentry off.
- Update the terms and privacy policy.

# Deploy to Heroku

1. Create the application in the Heroku web interface. A good name for the Heroku application is is `kl-<project_name>`.
1. Provision the postgresql add-on in the Heroku web interface
   - Note: if you didn't do this, a Heroku postgres database would be automatically provisioned and added to the `DATABASE_URL` environment variable if your app were successfully deployed. However, because deployment requires that variable to be set, a deployment will fail unless the database is provisioned first.
1. Set environment variables in production though the dashboard.
1. If using LogRocket, set the `LOGROCKET_APP_ID` environment variable and add it to the list of production environment variables at the bottom of the README. If not using LogRocket, simply don't set the env var.
1. Make sure the heroku CLI is installed
1. `heroku login` to log into Heroku account if you are not already logged in (check with `heroku auth:whoami`).
1. The nodejs buildpack was added to support Vite / Tailwind CSS with `heroku buildpacks:add heroku/nodejs --app <app_name>`.
1. Because we are manually specifying the buildpack, we also need to specify python: `heroku buildpacks:add heroku/python --app <app_name>`.
1. Note that the order that you specify the buildpacks is (probably) important, so do them in that order (first node, then python).
1. Connect Heroku to Github. Enable Automatic Deploys from `main` once CI has passed. You can push directly to `main` or do a PR into `main` and it will deploy once CI passes.
1. Set up postgres backups: `heroku pg:backups schedule --at '02:00 America/New_York' DATABASE_URL --app <app_name>`
1. Make sure there aren't any obvious issues in production: `heroku run python manage.py check --deploy --app <app_name>`
1. If the web worker doesn't seem to be running, give it one dyno: `heroku ps:scale web=1 --app <app_name>`
1. Add papertrail via the Heroku interface and set up alerts as per "Deployment" below.
1. Create a Postmark server if using email
1. Create the first superuser on production: `heroku run python manage.py createsuperuser --app <app_name>`
1. Update the Site name and domain in the Django admin.
1. You should be good to go. If you want to poke around, you can run `heroku run python manage.py shell --app <app_name>`.

## Heroku - Enable Celery if desired.

1. Add "`REDIS_URL` is set by Heroku" to the envrionment variables list under Deployment (below).
1. In Heroku, provision the redis add-on in the Heroku web interface which will automatically set the `REDIS_URL` environment variable.
1. In production settings, uncomment the `CELERY_BROKER_URL` setting.
1. In production settings, add `CELERY_TASK_ALWAYS_EAGER = False`.
1. Uncomment the `main_worker` entry in the `Procfile`.
1. Do a deploy.
1. Give the celery worker one dyno: `heroku ps:scale main_worker=1 --app <app_name>`

- Update the README as appropriate.
- Delete this file.
