# Copyright (c) Polyconseil SAS. All rights reserved.


from . import build
from . import naming
from . import op
from .build import build_runner_image
from .op import docker_push_image
from .op import get_manifest_digest
from .op import is_prefixed_image
from .wheels import compile_wheels

__all__ = [
    'build_runner_image',
    'docker_push_image',
    'is_prefixed_image',
    'compile_wheels',
    'get_manifest_digest',
    'get_or_build_root_image',
    'get_or_build_compiler_image',
]


def get_or_build_root_image(docker_client, config):
    return op.docker_get_or_build_image(
        docker_client,
        naming.image_name(config, 'root'),
        lambda client: build.build_root_image(client, config),
    )


def get_or_build_compiler_image(docker_client, config):
    return op.docker_get_or_build_image(
        docker_client,
        naming.image_name(config, 'compiler'),
        lambda client: build.build_compiler_image(client, config),
    )
