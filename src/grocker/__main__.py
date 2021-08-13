#! /usr/bin/env python
# Copyright (c) Polyconseil SAS. All rights reserved.

import logging

import click

from . import __version__
from . import builders
from . import cleanners
from . import helpers
from . import loggers
from . import utils

logger = logging.getLogger('grocker')


@click.group()
@click.version_option(__version__)
@click.option('-v', '--verbose', count=True)
def main(verbose):
    loggers.setup(verbose > 0)


@main.command()
@click.option('-a', '--all-versions/--only-old-versions', default=False)
@click.option('-f', '--including-final-images/--excluding-final-images', default=False)
def purge(all_versions, including_final_images):
    """Purge Grocker created Docker stuff."""
    docker_client = utils.docker_get_client()
    cleanners.docker_purge_container(docker_client, current_version=all_versions)
    cleanners.docker_purge_volumes(docker_client, current_version=all_versions)
    cleanners.docker_purge_images(docker_client, current_version=all_versions, runner=including_final_images)


@main.command()
@click.option(
    '-c', '--config', multiple=True, type=click.Path(exists=True), metavar='<filename>',
    help='Grocker config file',
)
@click.option('-r', '--runtime', metavar='<runtime>', help="runtime used to build and run this image")
@click.option(
    '--pip-conf', type=click.Path(exists=True), metavar='<filename>',
    help="pip configuration file used to download dependencies (by default use pip config getter)",
)
@click.option(
    '--pip-constraint', type=click.Path(exists=True), metavar='<filename>',
    help="pip constraint file used to download dependencies",
)
@click.option('-e', '--entrypoint', metavar='<entrypoint>', help="Docker entrypoint to use to run this image")
@click.option('--volume', multiple=True, metavar='<volume>', help="Container storage and configuration area")
@click.option('--port', multiple=True, metavar='<port>', help="Port on which a container will listen for connections")
@click.option('--env', multiple=True, metavar='<env=value>', help="Additional environment variable for final image")
@click.option(
    '--image-prefix', metavar='<uri>',
    help='docker registry or account on Docker official registry to use',
)
@click.option(
    '--image-base-name', metavar='<name>',
    help="base name for the image (eg '<image-prefix>/<image-base-name>:<image-version>')",
)
@click.option('-n', '--image-name', metavar='<name>', help="name used to tag the build image")
@click.option(
    '--result-file', type=click.Path(exists=False), metavar='<filename>',
    help="yaml file where results (image name, ...) are written",
)
@click.option(
    '--build-dependencies/--no-build-dependencies', default=True,
    help='build the dependencies',
)
@click.option(
    '--build-image/--no-build-image', default=True,
    help='build the docker image',
)
@click.option(
    '--push/--no-push', default=True,
    help='push the image',
)
@click.argument('release')
def build(release, build_dependencies, build_image, push, **kwargs):
    """Build docker image for RELEASE (version specifiers can be used).

    RELEASE can either be the name of a project, or the path to a wheel to use. In both cases, extra requirements can be
    applied:

        grocker build your_project[with_extra]==1.2.3

        grocker build /path/to/your_project-1.2.3.whl[with_extra]
    """
    requirement = utils.GrockerRequirement.parse(release)
    collect = {}  # will contain all collected information
    docker_client = utils.docker_get_client()
    collect['release'] = release

    config = utils.parse_config(
        kwargs['config'],
        runtime=kwargs['runtime'],
        entrypoint_name=kwargs['entrypoint'],
        pip_constraint=kwargs['pip_constraint'],
        docker_image_prefix=kwargs['image_prefix'],
        image_base_name=kwargs['image_base_name'],
        volumes=kwargs['volume'],
        ports=kwargs['port'],
        envs=dict(item.split('=', 1) for item in kwargs['env']),
    )
    image_name = kwargs['image_name'] or utils.default_image_name(config, requirement)
    collect['image'] = image_name

    # Raise if grocker do not known the runtime
    if config['runtime'] not in config['runtimes']:
        raise RuntimeError('Unknown runtime: %s', config['runtime'])

    if config['runtimes'][config['runtime']].get('deprecated'):
        logging.warning(
            "Runtime %s is deprecated, please update to more recent runtime",
            config['runtime'],
        )

    if build_dependencies:
        logger.info('Compiling dependencies...')
        builders.get_or_build_root_image(docker_client, config)
        compiler = builders.get_or_build_compiler_image(docker_client, config)
        collect['compiler_image'] = compiler.tags[0]

        with helpers.pip_conf(pip_conf_path=kwargs['pip_conf']) as pip_conf:
            builders.compile_wheels(
                docker_client=docker_client,
                config=config,
                requirement=requirement,
                pip_conf=pip_conf,
            )

    if build_image:
        logger.info('Building image...')
        root_image = builders.get_or_build_root_image(docker_client, config)
        collect['root_image'] = root_image.tags[0]
        builders.build_runner_image(
            docker_client=docker_client,
            config=config,
            name=image_name,
            requirement=requirement,
        )

    if push:
        if not builders.is_prefixed_image(image_name):
            logger.warning('Not pushing any image since the registry is unclear in %s', image_name)
        else:
            logger.info('Pushing image...')
            image = builders.docker_push_image(docker_client, image_name)
            collect['hash'] = (
                builders.get_manifest_digest(image_name)
                or [x.split('@')[1] for x in image.attrs['RepoDigests']][0]
            ) if config['manifest'] else None

    if kwargs['result_file']:
        helpers.dump_yaml(kwargs['result_file'], collect)


if __name__ == '__main__':
    main()
