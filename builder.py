#!/usr/bin/env python3
"""
    Docker builder for blue applications

    Aims at compiling / preparing releases in a docker to be available when
    creating a new target docker

    prerequisites: the user running the program should be able to run the docker
    command.

    On debian, there is a docker group, so adding your user and logout / relogin
    would work.
    sudo usermod -a -G docker benoit

"""

import argparse
import logging
import os
import subprocess
import sys
import textwrap


logger = logging.getLogger(sys.argv[0])
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


# constants
BLUE_HOME = '/home/blue'
HOST_RUNNER_ENV = 'config.env'

parser = argparse.ArgumentParser()
parser.add_argument(
    '--python-version',
    help='Python version to build and use for the instance',
    required=True,
)

parser.add_argument(
    '--output-dir',
    help='Output directory where compiled files will be stored',
    required=True,
)

parser.add_argument(
    '--si-name',
    help='The project name to build',
    required=True,
)

parser.add_argument(
    '--si-version',
    help='The Si version to build',
    required=True,
)

parser.add_argument(
    '--builder-version',
    help='Indicate the builder version',
    default='0.1',
)

args = parser.parse_args()

IMAGE_TO_BUILD = ('base', 'compiler')


class MiserableFailure(Exception):
    pass


def run_process(process, *process_options):
    """Run the 'sh' style process but checks if it runs correctly
        and log the stderr/stdout

        Args:
            process:  sh, the selected process to run
            process_options, args, option to give to the process

        Raises:
            MiserableFailure when exit_code != 0
    """
    args = [process]
    args.extend(process_options)
    cmd_line = "{} {}".format(
        str(process),
        ' '.join(process_options),
    )
    logger.info("-> running %s", cmd_line)
    try:
        p = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except Exception as exc:
        logger.exception("Can't run %s", cmd_line)
        raise MiserableFailure("Process %s failed", cmd_line) from exc

    else:
        logger.info(p.stdout.read().decode())



for image in IMAGE_TO_BUILD:
    try:
        output = run_process(
            'docker',
            'build', '--force-rm=true', '--rm=true',
            '-t', 'bluesolutions/bundle-{image}:{version}'.format(
                image=image,
                version=args.builder_version
                ),
            '{image}.docker/.'.format(image=image),
        )
    except Exception as exc:
        logger.exception("Can't build image %s", image)
        sys.exit(-1)

# run the compiler
output = run_process(
    'docker',
    'run', '--rm',
    '--volume', '{home}/.pip/:{blue_home}/.pip.host'.format(
        home=os.path.expanduser("~"),
        blue_home=BLUE_HOME,
    ),
    '--volume', '{output_dir}:{blue_home}/output'.format(
        output_dir=args.output_dir,
        blue_home=BLUE_HOME,
    ),
    'bluesolutions/bundle-compiler:{builder_version}'.format(
        builder_version=args.builder_version,
    ),
    '--python', args.python_version,
    '--output', '{blue_home}/output'.format(blue_home=BLUE_HOME),
    '{si}=={si_version}'.format(
        si=args.si_name,
        si_version=args.si_version,
    )
)

# create the configuration for our future image
runner_env_path = os.path.join('runner_template.docker', 'output', HOST_RUNNER_ENV)
with open(runner_env_path, 'w') as fh:
    fh.write(textwrap.dedent(
        """
        PACKAGE_NAME={package_name}=={package_version}
        PYTHON_VERSION={python_version}
        """.format(

        package_name=args.si_name,
        package_version=args.si_version,
        python_version=args.python_version)
    ))


# create the future docker image
output = run_process(
    'docker',
    'build', '--force-rm=true', '--rm=true',
    '-t', 'bluesolutions/{si_name}:{si_version}'.format(
        si_name=args.si_name,
        si_version=args.si_version,
    ),
    'runner_template.docker/.'
)


