# Developing the project

To run this on your machine you will need a database configured or you will need to swap the
enabled default DB in the settings file.

You will also need these environment variables in your development environment.  
I typically set all these up in .bashrc and use the same creds for all my dev projects.

```
DJANGO_DB_USER=<Your username here>
DJANGO_DB_PASSWORD=<Your password here>
DJANGO_DEBUG=1
````


# Testing the project

This command is handy when you are testing the project, coverage stats will be found in
htmlcov/index.html

```
$ DJANGO_SETTINGS_MODULE=diary.test_settings coverage run manage.py test && coverage html --include=\*stories\*,\*author\*,\*accounts\*
```
