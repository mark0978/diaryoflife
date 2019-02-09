import os

# Provide dummy values for the platform environment during test
os.environ['DJANGO_DB_USER'] = 'platform'
os.environ['DJANGO_DB_PASSWORD'] = 'platform'

from .test_settings import *


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
