import sys

import logging.config

DEFAULT_LOGGING = {
    'version': 1,
    'formatters': {
        'standard': {
            'format': '%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
            'datefmt': '%Y-%m-%d:%H:%M:%S' },
    },
    'handlers': {
        'console':  {'class': 'logging.StreamHandler',
                     'formatter': "standard",
                     'level': 'DEBUG',
                     'stream': sys.stdout},
        'file':     {'class': 'logging.FileHandler',
                     'formatter': "standard",
                     'level': 'DEBUG',
                     'filename': 'live_detector.log','mode': 'w'}
    },
    'loggers': {
        __name__:   {'level': 'INFO',
                     'handlers': ['console', 'file'],
                     'propagate': False },
    }
}

logging.config.dictConfig(DEFAULT_LOGGING)
log = logging.getLogger(__name__)

class SingletonMeta(type):
    def __call__(cls, *args, **kwargs):
        if not hasattr(cls, '_obj'):
            cls._obj = cls.__new__(cls)
            cls._obj.__init__(*args, **kwargs)
        return cls._obj