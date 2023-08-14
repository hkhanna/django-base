# Usage

This repository is used as a template repository that I can clone for any new Django project. Those projects should keep this repo as a "base" remote so changes to this base repository can be easily merged into the children projects.

Generally, you'll want to avoid making too many changes to the `core` app to avoid merge conflicts when you merge in updates to this base repo. In other words, put as much as you can into different apps, although some changes to the `core` app may be unavoidable.

# Creating a new Django project from `fedora/base`

- Pick a suitable project name.
- Clone the repo into the new project name directory. E.g., `git clone git@github.com:hkhanna/fedora.git <project_name>`
- Rename the `origin` remote to `base`: `git remote rename origin base`
- In the project directory: `git checkout base/base && git checkout -b base && git branch -D main && git branch -M main`.
- Create a fresh Github repo for the project.
- Point the `origin` remote to a fresh Github repo.
- In the `fedora` repo, add the new application as it's own remote so you can cherry-pick commits if necessary.
- Remove or replace the LICENSE file.
- Update `.env.example` to the desired defaults for the new project.
- Create an AWS bucket for media ideally named `<project>-production` and the appropriate keys. This will hold things like attachments to EmailMessages.
- Grep for the string `base-fedora` and either replace that string with the project name or take the other described action.
- Either disable social auth by removing it from the installed apps or obtain the relevant secrets and add them to local `.env`.
- Do the "Local Installation" in the README.
- Add to `ALLOWED_HOSTS` in production settings whatever the domain is going to be.
- Update `SITE_CONFIG`.
- Update the **production** `SENTRY_DSN` setting if using Sentry. Leave as `None` to keep Sentry off.

# Enable AWS for backups if desired

1. Set up the GPG encryption:
   1. `gpg --gen-key`
   1. For the name, put the name of the project. For the email, put `<project>@<domain>.`
   1. Make a note of the key's id.
   1. Remove the expiration date with `gpg --edit-key <project>@<domain>` and then `expire` and then `save`. You may need to remove subkey expiration dates as well with `key 1` and then `expire` and then `save`. Check that expiration dates have been removed by running `gpg --list-keys`.
   1. `gpg --output <project>.asc --armor --export <project>@<domain>`.
   1. Commit the new `.asc` file to the repo.
1. Store the private key & passphrase safely offline. E.g., paper or 1Password.
   1. `gpg --output <project>.secret.asc --armor --export-secret-keys <project>@<domain>`
   1. Don't commit this file to the repo!
1. Uncomment django-dbbackup section in common.py and production.py settings.
1. Uncomment django-dbbackup and python-gnupg in requirements/common.txt.
1. Uncomment dbbackup in common.py INSTALLED_APPS.
1. Uncomment the gpg line in build-web.sh and build-worker.sh.
1. Uncomment the GNUPGHOME environment variable in render.yaml.
   - This is needed because Render's build and runtime containers are different and only things in `/opt/render/project` make are taken from build to runtime.
1. Using celery beat or cron, call core.tasks.database_backup and core.tasks.media_backup as appropriate.

Note that an AWS lifecycle rule ("Prune Backups") will expire backups after approximately six months and permanently delete them approximately six months later.

# Create the AWS IAM User to obtain the access keys

Because django-storages is required, an IAM user will be needed with the following inline policy. If you're not using the automated backups, you can remove the first statement, but it doesn't hurt to keep it there in case you enable dbbackups someday.

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

# Deploy to Render

1. Make any changes to `render.yaml`. Look at the comments in the file.
1. Make sure the "Log Stream" is setup in your Render account settings. Right now, all services have to share 1 log stream, which is not ideal. It seems like that will change eventually and we will be able to have 1 Log Stream per service or service group.
1. Create a new "Blueprint" in the Render interface, and connect the repo. This will prompt you to set environment variables that are set to sync: false.
1. Using the Render shell on the dashboard:
   - Make sure there aren't any obvious issues in production. `python manage.py check --deploy`
   - Create the first superuser on production: `python manage.py createsuperuser`
   - If you want to poke around, `python manage.py shell`.
1. Update the Site name and domain in the Django admin.
1. If you're using social auth, add the appropriate `Social Applications`.

## Render - Enable Celery if desired.

1. Uncomment the redis and celery worker sections of `render.yaml` including the redis env var setting.
1. In production settings, uncomment the `CELERY_BROKER_URL` setting.
1. In production settings, add `CELERY_TASK_ALWAYS_EAGER = False`.
1. Do a deploy.

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
- A one-time payment situation would probably only use the default Plan and override OrgSettings as the purchase is made.
- Each setting stores its value as an integer, but if the type is set to `bool` instead of `int`, it will report it as True or False.

### Built-in OrgUserSettings

- `can_invite_members`: the `OrgUser` can invite and cancel invitations to an `Org`.
- `can_remove_members`: the `OrgUser` can invite and cancel invitations to an `Org`.
