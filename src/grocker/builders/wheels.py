# Copyright (c) Polyconseil SAS. All rights reserved.

import base64
import configparser
import logging
import os.path
import pathlib
import zlib

from .. import utils
from . import naming
from . import op

logger = logging.getLogger(__name__)


def get_pip_env(pip_conf):
    def get(cfg, section, option, default=None):
        try:
            return cfg.get(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default

    if not pip_conf:
        return {}

    logger.info('-> Pip use configuration from %s.', pip_conf)
    config = configparser.ConfigParser()
    config.read(pip_conf)

    env = {
        'PIP_INDEX_URL': get(config, 'global', 'index-url'),
        'PIP_EXTRA_INDEX_URL': get(config, 'global', 'extra-index-url'),
        'PIP_TIMEOUT': get(config, 'global', 'timeout'),
        'PIP_TRUSTED_HOST': get(config, 'global', 'trusted-host'),
    }
    env = {k: v for k, v in env.items() if v}
    logger.debug('pip using env: %s', env)
    return env


def compile_wheels(docker_client, config, requirement, pip_conf):
    wheels_destination_volume = op.get_or_create_data_volume(
        docker_client,
        naming.wheel_volume_name(config),
        role='wheel',
        labels={
            'grocker.runtime': config['runtimes'][config['runtime']]['runtime'],
            'grocker.config.hash': utils.config_identifier(config),
        },
    )
    volumes = {
        wheels_destination_volume.name: {
            'bind': '/home/grocker/packages',
            'mode': 'rw',
        },
    }

    # may contain passwords/token for pypi auth
    netrc = pathlib.Path('~/.netrc').expanduser()
    if netrc.exists():
        volumes[netrc] = {
            'bind': '/home/grocker/.netrc',
            'mode': 'ro',
        }

    if requirement.filepath:
        filename = os.path.basename(requirement.filepath)
        wheel_path = f'/tmp/src/{filename}'  # noqa: S108
        volumes[requirement.filepath] = {'bind': wheel_path, 'mode': 'ro'}
        to_install = wheel_path + requirement.pip_extras
    else:
        to_install = requirement.to_install

    command = ['--python', config['runtimes'][config['runtime']]['runtime'], to_install]
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
