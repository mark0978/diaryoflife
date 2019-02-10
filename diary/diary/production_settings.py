"""
Production settings for diary project, these are not used with platform.sh
"""

from settings import *

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
                'handlers': ['sys-logger', ],
                'level': logging.DEBUG,
                'propagate': True,
                },
            }
    })
