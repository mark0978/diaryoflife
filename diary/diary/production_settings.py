"""
Production settings for diary project, these are not used with platform.sh
"""
#import sys

from .settings import *

import logging
from logging import config as logging_config


logging_config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '%(levelname)s %(module)s P%(process)d T%(thread)d %(message)s'
                },
            },
        'handlers': {
            # 'stdout': {
                # 'class': 'logging.StreamHandler',
                # 'stream': sys.stdout,
                # 'formatter': 'verbose',
                # },
            'sys-logger': {
                'class': 'logging.handlers.SysLogHandler',
                'address': '/dev/log',
                'facility': "local6",
                'formatter': 'verbose',
                },
            },
        'loggers': {
            '': {
                #'handlers': ['stdout', ],
                'handlers': ['sys-logger', ],
                'level': logging.DEBUG,
                'propagate': True,
                },
            }
    })


#EMAIL_BACKEND = 'email_log.backends.EmailBackend'
#EMAIL_LOG_BACKEND = 'postmarker.django.EmailBackend'
EMAIL_BACKEND = 'postmarker.django.EmailBackend'

POSTMARK = {
    "TOKEN": os.environ["DJANGO_POSTMARK_TOKEN"],
    "TEST_MODE": False,
    "VERBOSITY": 0,
}

EMAIL_SUBJECT_PREFIX = ""
DEFAULT_FROM_EMAIL = "(Diary Of Life) <noreply@diaryof.life>"
SERVER_EMAIL = "noreply@diaryof.life"
