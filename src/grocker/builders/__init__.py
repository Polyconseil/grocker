# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.

from __future__ import absolute_import, division, print_function, unicode_literals

from . import build
from .build import build_runner_image
from . import naming
from . import op
from .op import docker_push_image, is_prefixed_image
from .wheels import compile_wheels


__all__ = [
    'build_runner_image',
    'docker_push_image',
    'is_prefixed_image',
    'compile_wheels',
    'get_or_build_root_image',
    'get_or_build_compiler_image',
]


def get_or_build_root_image(docker_client, config):
    return op.docker_get_or_build_image(
        docker_client,
        naming.image_name(config, 'root'),
        lambda client: build.build_root_image(client, config)
    )


def get_or_build_compiler_image(docker_client, config):
    return op.docker_get_or_build_image(
        docker_client,
        naming.image_name(config, 'compiler'),
        lambda client: build.build_compiler_image(client, config)
    )
