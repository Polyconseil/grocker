# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.

from __future__ import absolute_import, division, print_function, unicode_literals

import base64
import logging
import zlib

from .. import six
from .. import utils
from . import naming
from . import op

logger = logging.getLogger(__name__)


def get_pip_env(pip_conf):
    def get(cfg, section, option, default=None):
        try:
            return cfg.get(section, option)
        except (six.configparser.NoSectionError, six.configparser.NoOptionError):
            return default

    if not pip_conf:
        return {}

    logger.info('-> Pip use configuration from %s.', pip_conf)
    config = six.configparser.ConfigParser()
    config.read(pip_conf)

    env = {
        'PIP_INDEX_URL': get(config, 'global', 'index-url'),
        'PIP_EXTRA_INDEX_URL': get(config, 'global', 'extra-index-url'),
    }
    env = {k: v for k, v in env.items() if v}
    logger.debug('pip using env: %s', env)
    return env


def compile_wheels(docker_client, config, release, pip_conf):
    wheels_destination_volume = op.get_or_create_data_volume(
        docker_client,
        naming.wheel_volume_name(config),
        role='wheel',
        labels={
            'grocker.runtime': config['runtime'],
            'grocker.config.hash': utils.config_identifier(config),
        },
    )
    volumes = {
        wheels_destination_volume.name: {
            'bind': '/home/grocker/packages',
            'mode': 'rw',
        },
    }
    command = ['--python', config['runtime'], release]
    environment = get_pip_env(pip_conf)

    if config['pip_constraint']:
        with open(config['pip_constraint'], 'rb') as fp:
            constraints = fp.read()
        environment['PIP_CONSTRAINT_CONTENT'] = base64.b64encode(zlib.compress(constraints)).decode()

    return op.docker_run_container(
        docker_client,
        naming.image_name(config, 'compiler'),
        command,
        volumes=volumes,
        environment=environment,
    )
