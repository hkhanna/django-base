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

## Enable Google Authentication if desired

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

## Organizations

The concept of organizations (`Org`) is available for use, but not required. To use the organizations functionality, you'll need to add `core.middleware.OrgMiddleware` to the middleware. In addition to the various settings infrastucture (below), you have a couple other goodies you can use:

- `core.services.org_switch()` which is a function to switch the active org for the current request. It should be used with an org switcher widget on the frontend.
- `OrgUserSettingPermissionMixin(UserPassesTestMixin)` for testing OrgUserSettings before allowing access to a view

If you create a model that relies on the `Org` model or other of the other models related to `Org`, you'll need to handle the case that there is no active org. This can happen:

- when a user initially signs up;
- a User is removed from or leaves an org; or
- an org is deleted.

You must not assume that a `user` has an org or that `request.org` is not None.

### Org-related Settings

There are 2 types of settings, settings for an `Org` (`OrgSetting`) and settings for an `OrgUser` (`OrgUserSetting`).
They are related to` Orgs`, `OrgUsers` and `Plans` in different ways.

- `OrgSettings` are primarily related to a payment `Plan`. An `Org` may override an `OrgSetting`, in which case it will not look to the `Plan` for that `OrgSetting`.
- If a `Plan` is queried for an `OrgSetting`, and that `OrgSetting` is not set on the `Plan`, it will materialize the setting on the `Plan` with the `OrgSetting`'s default.
- `OrgUserSettings` should have defaults set by the `Org`. If an `Org` is accessed for an `OrgUserSetting` default and it's not there, it will materialize it on the `Org`.
  - We set an `owner_value` on the base `OrgUserSetting` that is always used for the `Org` owner, who is kind of a superuser.
- If an `OrgSetting` or `OrgUserSetting` does not exist but is queried, that setting will autocreate with a default of `False` and an owner_value of `True`.

#### Development Notes:

- At this point, it doesn't seem useful to attach `OrgUserSetting` defaults to a `Plan`, so we don't. We can easily change this down the road though.
- A one-time payment situation would probably only use the default `Plan` and override `OrgSettings` as the purchase is made.

### Org-related Product Decisions

You will need to make a few product decisions, and write code to handle the following:

- Can a user create an org?
- Is there a limit to the number of orgs a user can own?
- Does deleting an Org hard delete it or set Org.is_active to false? And if it's soft deleted, users should no longer be able to access the org.
- Can only the org's owner delete it? Should whether an org be deleted be configureable as an OrgSetting or a GlobalSetting?
- Should changing org information like it's name be limited to the owner, or should it be available in an OrgUserSetting?
- If you create the ability for users to delete their accounts, should they be able to delete their account if they are the owner of an org? If so, what should happen to the org?
- Can an owner transfer ownership of an org?
- Should you prevent an owner from leaving an org before transfering it?
- Can a user leave an org? Should this be configurable as an OrgSetting?
- Can a user be removed and if so, is there an OrgUserSetting for this permission or can only the owner do it? If there is a setting, an org owner should probably not be removable.

I recommend writing a test for each answer to the foregoing quetions.

#### Personal orgs, default orgs, or view restrictions.

One approach to help answer these questions is to create the concept of a "personal org". This adds some complexity because that org would be treated differently in many cases. For example, if a personal org is named after the owner, should changing the owner's name change the name of the personal org? If a user is created because they were invited to an org, does it make sense to create a personal org too? And if a user leaves their last org and doesn't have a personal org, perhaps it should create one. In a lot of applications, the concept of a personal org would not make sense. But in primarily consumer-facing ones, it might.

Another approach might be the concept of a single "default" org that a user gets added to if they don't have another one. This is simpler, but runs the risk of users seeing each others' data, depending on which models are linked to the `Org` model. For example, it should not be possible for users to see the list of members in the default org.

A third approach might simply be to prevent a user from accessing any org-required views until they create an org. Perhaps something they could do on signup if they didn't join via an invitation from an org.

#### Invitations

If you create a system where an OrgUser can invite another user to an org (perhaps via email), consider the following scenarios:

- The user does not exist in the system yet.
- The user exists in the system, but is not yet a member of the org.
- The user is already a member of the org.
- The user is invited that already has a pending invitation to the org.
- Canceling a pending invitation.
- Who can invite a new user? Only the owner or is there an OrgUserSetting for it?
- Can you "resend" the invitation? Is there a maximum of number of times you can do it or a cooldown period?
- Should the inviter have a verified email address before they can invite anyone?

Again, it would be a good idea to write tests for the answers to the above questions.

## Other Things to Know

### Messages Framework

If the `extra_tags` parameter to `messages.add_message` is passed, the `extra_tags` parameter becomes the title, and the text of the message is the description.
