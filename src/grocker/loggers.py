# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.

from __future__ import absolute_import, division, print_function, unicode_literals
import logging
import logging.config


class ColoredStreamHandler(logging.StreamHandler):
    _colors = {
        logging.DEBUG: '36',
        logging.INFO: '1;36',
        logging.WARNING: '1;33',
        logging.ERROR: '1;31',
        logging.CRITICAL: '1;41;37',
    }

    def format(self, record):
        msg = super(ColoredStreamHandler, self).format(record)
        color = self._colors.get(record.levelno, None)

        if not color or not self.stream.isatty():
            return msg

        return '\x1b[{color}m{msg}\x1b[0m'.format(color=color, msg=msg)


def setup(verbose=False):
    level = 'DEBUG' if verbose else 'INFO'

    logging.config.dictConfig({
        'version': 1,
        'formatters': {
            'simple': {'format': '%(name)s: %(message)s'},
        },
        'handlers': {
            'console': {'class': '{}.ColoredStreamHandler'.format(__name__), 'formatter': 'simple'},
        },
        'loggers': {
            'grocker': {'handlers': ['console'], 'level': level},
        },
    })


if __name__ == '__main__':
    setup(verbose=True)
    test_logger = logging.getLogger(__package__)
    test_logger.debug('Some debug output.')
    test_logger.info('Some info output.')
    test_logger.warning('Some warning output.')
    test_logger.error('Some error output.')
    test_logger.critical('Some critical output.')
