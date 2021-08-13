# Copyright (c) Polyconseil SAS. All rights reserved.

from .. import __version__
from .. import utils


def image_name(config, role):
    image_name_template = 'grocker-{runtime}-{role}:{version}-{hash}'
    if role == 'wheel-server':
        image_name_template = 'grocker-{role}:{version}'

    if config['docker_image_prefix']:
        image_name_template = '{prefix}/' + image_name_template

    return image_name_template.format(
        prefix=config['docker_image_prefix'],
        runtime=config['runtime'].replace('/', '-'),
        role=role,
        version=__version__,
        hash=utils.config_identifier(config),
    )


def wheel_volume_name(config):
    return 'grocker-wheel-cache-{version}-{runtime}-{hash}'.format(
        version=__version__,
        runtime=config['runtime'].replace('/', '-'),
        hash=utils.config_identifier(config),
    )
