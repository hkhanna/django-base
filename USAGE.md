# Usage

This repository is used as a template repository that I can clone for any new Django project. Those projects should keep this repo as a "base" remote so changes to this base repository can be easily merged into the children projects.

Generally, you'll want to avoid making too many changes to the `base` app to avoid merge conflicts when you merge in updates to this base repo. In other words, put as much as you can into different apps, although some changes to the `base` app may be unavoidable.

# Creating a new Django project from `base-fedora`

- Pick a suitable project name.
- Clone the repo into the new project name directory. E.g., `git clone git@github.com:getmagistrate/base-fedora.git <project_name>`
- Rename the `origin` remote to `base`: `git remote rename origin base`
- Create a fresh Github repo for the project.
- Point the `origin` remote to a fresh Github repo.
- In the `base-fedora` repo, add the new application as it's own remote so you can cherry-pick commits if necessary.
- Remove or replace the LICENSE file.
- Update `.env.example` to the desired defaults for the new project.
- Grep for the string `base-fedora` and either replace that string with the project name or take the other described action.
- Decide if `billing` should be installed at this point.
  - You can always install billing later, but if you know for sure you need it, do it now.
  - To install `billing`:
    - [Follow the instructions](https://github.com/hkhanna/billing) to install the package.
    - Add `billing.mixins.BilingMixin` to the `SettingsView` after `LoginRequiredMixin`.
- Do the "Local Installation" described below.
- Add to `ALLOWED_HOSTS` in production settings whatever the domain is going to be.
- Update `SITE_CONFIG`.
- Update the **production** `GA_TRACKING_ID` setting if using Google Analytics. Leave as `None` to keep Google Analytics off.
- Update the **production** `SENTRY_DSN` setting if using Sentry. Leave as `None` to keep Sentry off.

# Deploy to Render

1. Make any changes to `render.yaml`. Look at the comments in the file.
1. Make sure the "Log Stream" is setup in your Render account settings. Right now, all services have to share 1 log stream, which is not ideal. It seems like that will change eventually and we will be able to have 1 Log Stream per service or service group.
1. Create a new "Blueprint" in the Render interface, and connect the repo. This will prompt you to set environment variables that are set to sync: false.
1. Using the Render shell on the dashboard:
   - Make sure there aren't any obvious issues in production. `python manage.py check --deploy`
   - Create the first superuser on production: `python manage.py createsuperuser`
   - If you want to poke around, `python manage.py shell`.
1. Update the Site name and domain in the Django admin.

## Render - Enable Celery if desired.

1. Uncomment the redis and celery worker sections of `render.yaml` including the redis env var setting.
1. In production settings, uncomment the `CELERY_BROKER_URL` setting.
1. In production settings, add `CELERY_TASK_ALWAYS_EAGER = False`.
1. Uncomment the `main_worker` entry in the `Procfile`.
1. Do a deploy.

- Update the README as appropriate.
- Delete this file.
