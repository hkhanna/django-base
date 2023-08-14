#!/usr/bin/env bash

# exit on error
set -o errexit

# install -d -m 700 /opt/render/project/gnupg && gpg --import base-fedora.asc

pip install -r requirements/production.txt