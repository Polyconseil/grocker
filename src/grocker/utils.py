# Copyright (c) Polyconseil SAS. All rights reserved.

import hashlib
import os.path

import docker
import packaging.utils
from packaging import requirements

from . import helpers

GROUP_SEPARATOR = b'\x1D'
RECORD_SEPARATOR = b'\x1E'
UNIT_SEPARATOR = b'\x1F'


def config_identifier(config):
    """
    Hash config to get an unique identifier.

    Args:
        config (dict): Grocker config

    Returns:
        str: Config identifier (SHA 256)

    """
    def unit_list(list_item):
        return UNIT_SEPARATOR.join(sorted(x.encode('utf-8') for x in list_item))

    dependencies = unit_list(get_dependencies(config, with_build_dependencies=True))
    repositories = RECORD_SEPARATOR.join(
        unit_list([name] + [cfg[x] for x in sorted(cfg)])
        for name, cfg in config['repositories'].items()
    )
    data = GROUP_SEPARATOR.join([
        dependencies,
        repositories,
    ])
    digest = hashlib.sha256(data)
    return digest.hexdigest()


def default_image_name(config, req):
    docker_image_prefix = config['docker_image_prefix']
    if config['image_base_name']:
        img_name = config['image_base_name']
    elif req.extras:
        img_name = "{project}-{extra_requirements}".format(
            project=req.project_name,
            extra_requirements='-'.join(req.extras),
        )
    else:
        img_name = req.project_name
    img_name += ":{project_version}".format(
        # Python versions might contain "+"
        # but a docker tag name must be valid ASCII and may contain lowercase and uppercase
        # letters, digits, underscores, periods and dashes
        project_version=req.version.replace('+', '-'),
    )
    return '/'.join((docker_image_prefix, img_name)) if docker_image_prefix else img_name


def docker_get_client(min_version=None):
    client = docker.from_env()
    if min_version and client.version()['ApiVersion'].split('.') <= min_version.split('.'):
        raise RuntimeError(
            'Docker API version should be at least {expected} ({current})'.format(
                current=client.version()['ApiVersion'],
                expected=min_version,
            ),
        )
    return client


def get_dependencies(config, with_build_dependencies=False):
    runtime = config['runtime']
    runtime_dependencies = config['runtimes'][runtime]['dependencies']

    dependencies = (
        runtime_dependencies.get('run', [])
        + config['dependencies'].get('run', [])
    )

    if with_build_dependencies:
        dependencies += (
            runtime_dependencies.get('build', [])
            + config['dependencies'].get('build', [])
        )

    return dependencies


def parse_config(config_paths, **kwargs):
    """
    Generate config regarding precedence order.

    Precedence order is defined as :

    1. Command line arguments
    2. project ``.grocker.yml`` file (or the one specified on the command line)
    3. the grocker ``resources/grocker.yaml`` file
    """
    config = helpers.load_yaml_resource('grocker.resources', 'grocker.yaml')

    if not config_paths and os.path.exists('.grocker.yml'):
        config_paths = ['.grocker.yml']

    for config_path in config_paths:
        project_config = helpers.load_yaml(config_path)
        config = helpers.deep_update(config, project_config or {})

    return helpers.deep_update(config, {k: v for k, v in kwargs.items() if v})


class GrockerRequirement:

    def __init__(self, project_name, operator, version, extras, filepath):
        self.project_name = packaging.utils.canonicalize_name(project_name)
        self.operator = operator
        self.version = version
        self.extras = extras
        self.filepath = filepath

    @classmethod
    def parse(cls, release):
        if os.path.sep in release:
            return cls.parse_from_filepath(release)
        else:
            return cls.parse_from_req(release)

    @classmethod
    def parse_from_req(cls, release):
        requirement = requirements.Requirement(release)
        if len(requirement.specifier) != 1:
            raise ValueError("A single exact specifier is mandatory: %s" % requirement)
        if requirement.url or requirement.marker:
            raise ValueError("Invalid requirement: %s: marker and url are ignored" % requirement)
        spec = list(requirement.specifier)[0]
        if spec.operator not in ('==', '==='):
            raise ValueError("Only exact specifier are accepted: %s" % requirement)
        version = spec.version
        return cls(
            project_name=requirement.name,
            operator=spec.operator,
            version=version,
            extras=sorted(requirement.extras),
            filepath=None,
        )

    @classmethod
    def parse_from_filepath(cls, release):
        if release.endswith(']'):
            filepath, _, extras = release[:-1].rpartition('[')
            extras = sorted(extra.strip() for extra in extras.split(','))
        else:
            filepath = release
            extras = []
        if not os.path.exists(filepath):
            raise ValueError("Invalid filepath %s" % release)
        if not filepath.endswith('.whl'):
            raise ValueError("Invalid filepath %s: only .whl are accepted" % release)
        wheel_file_parts = os.path.basename(filepath).split('-')
        return cls(
            project_name=wheel_file_parts[0],
            operator='==',
            version=wheel_file_parts[1],
            extras=extras,
            filepath=os.path.abspath(filepath),
        )

    @property
    def pip_extras(self):
        if not self.extras:
            return ''
        return "[{}]".format(",".join(sorted(self.extras)))

    @property
    def to_install(self):
        return "".join([self.project_name, self.pip_extras, self.operator, self.version])
