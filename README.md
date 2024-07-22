# Sync CSV Scoresheet to BCOE&M

You will need to set up a google app and create a set of oauth credentials.

Follow the guide [here](https://github.com/singingwolfboy/flask-dance-google#step-2-get-oauth-credentials-from-google).

Note: an unverified app in "Testing" phase is fine for small group of authorized admins as it allows up to 100 users.

## Local development

```
pyenv install
pip install -r requirements-dev.txt
cp .env.example .env
# set vars in .env
flask run --debug
```

Go to http://localhost:5000

## `update.sh`

You can use this script to deploy/update the app from the github repo.

## `passenger_wsgi.py`

This has nothing to do with the solution at all, but Westgate's shared hosting provider requires this file. It seems to serve as the application entry point.
