# Usage

This repository is used as a template repository that I can clone for any new Django project. Those projects should keep this repo as a "base" remote so changes to this base repository can be easily merged into the children projects.

Generally, you'll want to avoid making too many changes to the `core` app to avoid merge conflicts when you merge in updates to this base repo. In other words, put as much as you can into different apps, although some changes to the `core` app may be unavoidable.

## Creating a new Django project from `django-base`

- Pick a suitable project name.
- Clone the repo into the new project name directory. E.g., `git clone git@github.com:hkhanna/django-base.git <project_name>`
- Rename the `origin` remote to `base`: `git remote rename origin base`
- In the project directory, create a branch where you can keep a copy of `django-base`: `git branch base`.
- Create a fresh Github repo for the project.
- Point the `origin` remote to a fresh Github repo.
- In the `django-base` repo, add the new application as it's own remote so you can cherry-pick commits if necessary.
- Remove or replace the LICENSE file.
- Update `.env.example` to the desired defaults for the new project.
- Create an AWS bucket for media ideally named `<project>-production` and the appropriate keys. This will hold things like attachments to EmailMessages.
- Grep for the string `django-base` (excluding this file) and either replace that string with the project name or take the other described action.
- Either disable social auth by removing it from the installed apps or obtain the relevant secrets and add them to local `.env`.
- Do the "Local Installation" in the README.
- Add to `ALLOWED_HOSTS` in production settings whatever the domain is going to be.
- Update `SITE_CONFIG`.
- Update the **production** `SENTRY_DSN` setting if using Sentry. Leave as `None` to keep Sentry off.
- Update `SENTRY_DSN` in `frontend/src/js/react.tsx` if you want to track errors in the frontend. This will only be used in prod.

# Enable Google Authentication if desired

- Create a Google OAuth2 client ID and secret at https://console.cloud.google.com/apis/credentials
- Create separate client IDs for local development and production.
- Add the local development client ID and secret to the appropriate `.env` files.
- In `settings/common.py` set `SOCIAL_AUTH_GOOGLE_ENABLED` = True

## Enable AWS for backups if desired

1. Generate a passphrase and store it safely in 1Password.
1. Uncomment common.py and production.py STORAGES["backup"]
1. Uncomment python-gnupg in requirements/common.txt
1. Set ENABLE_DATABASE_BACKUPS to True in common.py
1. This will automatically enable the celery job contained in core.tasks.
1. If using Render: uncomment the BACKUP_ENCRYPTION_PASSPHRASE environment variable in render.yaml.
1. If using Heroku: add the BACKUP_ENCRYPTION_PASSPHRASE environment variable to the Heroku dashboard.

Note that an AWS lifecycle rule ("Prune Backups") will expire backups after approximately six months and permanently delete them approximately six months later.

### Create the AWS IAM User to obtain the access keys

Because django-storages is required, an IAM user will be needed with the following inline policy. If you're not using the automated backups, you can remove the first statement, but it doesn't hurt to keep it there in case you enable backups someday.

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject"
            ],
            "Resource": [
               "arn:aws:s3:::<backup-bucket-name>/<project>/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": [
                "arn:aws:s3:::<project>-production/*"
            ]
        }
    ]
}
```

Then, generate the access key and secret key and hold onto it for the deploy to Render.

## Deploy to Render

1. Make any changes to `render.yaml`. Look at the comments in the file.
1. Make sure the "Log Stream" is setup in your Render account settings. Right now, all services have to share 1 log stream, which is not ideal. It seems like that will change eventually and we will be able to have 1 Log Stream per service or service group.
1. Create a new "Blueprint" in the Render interface, and connect the repo. This will prompt you to set environment variables that are set to sync: false.
1. Using the Render shell on the dashboard:
   - Make sure there aren't any obvious issues in production. `python manage.py check --deploy`
   - Create the first superuser on production: `python manage.py createsuperuser`
   - If you want to poke around, `python manage.py shell`.
1. If you're using social auth, add the appropriate `Social Applications`.

### Render - Enable Celery if desired.

1. Uncomment the redis and celery worker sections of `render.yaml` including the redis env var setting.
1. In production settings, uncomment the `CELERY_BROKER_URL` setting.
1. In production settings, add `CELERY_TASK_ALWAYS_EAGER = False`.
1. Do a deploy.

### Render - Remove Heroku if desired.

1. Delete requirements.txt, runtime.txt, Procfile, and package.json.

## Deploy to Heroku

1. Create the application in the Heroku web interface.
1. Provision the postgresql add-on in the Heroku web interface
   - Note: if you didn't do this, a Heroku postgres database would be automatically provisioned and added to the `DATABASE_URL` environment variable if your app were successfully deployed. However, because deployment requires that variable to be set, a deployment will fail unless the database is provisioned first.
1. Set environment variables in production though the dashboard. See "Heroku - Production Environment Variables" below for an initial list.
1. `heroku login` to log into Heroku account if you are not already logged in (check with `heroku auth:whoami`).
1. The nodejs buildpack was added to support Vite / Tailwind CSS with `heroku buildpacks:add heroku/nodejs --app <app_name>`.
1. Because we are manually specifying the buildpack, we also need to specify python: `heroku buildpacks:add heroku/python --app <app_name>`.
1. Note that the order that you specify the buildpacks is (probably) important, so do them in that order (first node, then python).
1. Connect Heroku to Github. Enable Automatic Deploys from `main` once CI has passed. You can push directly to `main` or do a PR into `main` and it will deploy once CI passes.
1. Set up postgres backups: `heroku pg:backups schedule --at '02:00 America/New_York' DATABASE_URL --app <app_name>`
1. Make sure there aren't any obvious issues in production: `heroku run python manage.py check --deploy --app <app_name>`
1. If the web worker doesn't seem to be running, give it one dyno: `heroku ps:scale web=1 --app <app_name>`
1. Add papertrail via the Heroku interface.
1. Create a Postmark server if using email.
1. Create the first superuser on production: `heroku run python manage.py createsuperuser --app <app_name>`
1. If you're using social auth, add the appropriate `Social Applications`.

### Heroku - Production Environment Variables

If you're using Heroku, at a minimum, these are the environment variables that must be set in production:

- `DJANGO_SETTINGS_MODULE=config.settings.production`
- `DJANGO_SECRET_KEY=<random key>`
  - You can generate this random key with something like `openssl rand -base64 64`.
- `LOGLEVEL=INFO`
  - Without this, it will use the default of `DEBUG`.
- `POSTMARK_API_KEY=<postmark key>`
- `EVENT_SECRET`
- `AWS_S3_ACCESS_KEY_ID`
- `AWS_S3_SECRET_ACCESS_KEY`
- `ADMIN_URL_PATH`
  - Optional. Defaults to `admin/`.
- `BACKUP_ENCRYPTION_PASSPHRASE`
  - Optional if you're using the automated backups.
- `SOCIAL_AUTH_GOOGLE_CLIENT_ID` and `SOCIAL_AUTH_GOOGLE_CLIENT_SECRET`
  - Optional if you're using social auth.

### Heroku - Enable Celery if desired.

1. In Heroku, provision the redis add-on in the Heroku web interface which will automatically set the `REDIS_URL` environment variable.
1. In production settings, uncomment the `CELERY_BROKER_URL` setting.
1. In production settings, add `CELERY_TASK_ALWAYS_EAGER = False`.
1. In the `Procfile`, replace the uncommented `release` entry with the commented one and uncomment the `main_worker` entry.
1. Do a deploy.
1. Give the celery worker one dyno: `heroku ps:scale main_worker=1 --app <app_name>`

### Heroku - Remove Render if desired.

1. Delete render.yaml, build-web.sh, and build-worker.sh.

## Override templates if desired

The `core` app contains some default application layouts in `core/templates/core/layouts`. The `core` views like those related to authentication use these layouts. But the layouts can be overriden by creating a `templates/core/layouts` directory in an app that comes above `core` in `INSTALLED_APPS`.

Avoid making changes directly to the `core` directory to avoid merge conflicts when we update the `base` repo.

## Finalize Differentiation

- Update the README as appropriate.
- Delete this file.

## Orgs, Plans & Settings

There are 2 types of settings, settings for an `Org` (`OrgSetting`) and settings for an `OrgUser` (`OrgUserSetting`).
They are related to` Orgs`, `OrgUsers` and `Plans` in different ways.

- `OrgSettings` are primarily related to a payment `Plan`. An `Org` may override an `OrgSetting`, in which case it will not look to the `Plan` for that `OrgSetting`.
- If a `Plan` is queried for an `OrgSetting`, and that `OrgSetting` is not set on the `Plan`, it will materialize the setting on the `Plan` with the `OrgSetting`'s default.
- `OrgUserSettings` should have defaults set by the `Org`. If an `Org` is accessed for an `OrgUserSetting` default and it's not there, it will materialize it on the `Org`.
  - We set an `owner_value` on the base `OrgUserSetting` that is always used for the `Org` owner, who is kind of a superuser.
- If an `OrgSetting` or `OrgUserSetting` does not exist but is queried, that setting will autocreate with a default of `False` and an owner_value of `True`.

### Development Notes:

- At this point, it doesn't seem useful to attach `OrgUserSetting` defaults to a `Plan`, so we don't. We can easily change this down the road though.
- A one-time payment situation would probably only use the default `Plan` and override `OrgSettings` as the purchase is made.

### Built-in OrgUserSettings

- `can_invite_members`: the `OrgUser` can invite and cancel invitations to an `Org`.
- `can_remove_members`: the `OrgUser` can remove members from an `Org`.
