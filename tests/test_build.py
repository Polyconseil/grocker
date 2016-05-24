#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.

from __future__ import absolute_import, division, print_function, unicode_literals
import os
import re
import subprocess
import textwrap
import unittest
import uuid

import docker.errors

import grocker.builders as grocker_builders
import grocker.six as grocker_six


def docker_rmi(image):
    client = grocker_builders.docker_get_client()
    try:
        client.remove_image(image)
    except docker.errors.APIError:
        pass  # do not fail when image does not exist


def docker_run(image, command):
    client = grocker_builders.docker_get_client()

    container = client.create_container(
        image=image,
        command=command,
        host_config=client.create_host_config(),
    )

    container_id = container.get('Id')
    client.start(container_id)
    return_code = client.wait(container_id)
    logs = client.logs(container_id)

    client.remove_container(container_id)

    return return_code, logs


# Python 3 backport: textwrap.indent
def indent(text, prefix, predicate=None):
    """Adds 'prefix' to the beginning of selected lines in 'text'.

    If 'predicate' is provided, 'prefix' will only be added to the lines
    where 'predicate(line)' is True. If 'predicate' is not provided,
    it will default to adding 'prefix' to all non-empty lines that do not
    consist solely of whitespace characters.
    """
    if predicate is None:
        def predicate(line):
            return line.strip()

    def prefixed_lines():
        for line in text.splitlines(True):
            yield (prefix + line if predicate(line) else line)
    return ''.join(prefixed_lines())


class BuildTestCase(unittest.TestCase):
    release = 'grocker-test-project==1.0.3'
    dependencies = """
        - libzbar0: libzbar-dev
        - libjpeg62-turbo: libjpeg62-turbo-dev
        - libffi6: libffi-dev
        - libtiff5: libtiff5-dev
    """
    runtime = None

    def run_grocker(self, release, command, cwd=None):
        image_name = 'grocker.test/{}'.format(uuid.uuid4())
        try:
            subprocess.check_call(
                [
                    'python', '-m', 'grocker',
                    '--image-name', image_name,
                    '--docker-image-prefix', 'docker.polydev.blue',
                    'dep', 'img',
                    release,
                ] + (
                    ['--runtime', self.runtime] if self.runtime else []
                ),
                cwd=cwd,
            )

            return_code, logs = docker_run(
                image_name,
                command,
            )

            self.assertEqual(return_code, 0, msg=logs)
            return logs.decode('utf-8')
        finally:
            docker_rmi(image_name)

    def check(self, config, msg, expected):
        with grocker_six.TemporaryDirectory() as tmp_dir:
            with open(os.path.join(tmp_dir, '.grocker.yml'), 'w') as fp:
                fp.write(textwrap.dedent(config[1:]))

            logs = self.run_grocker(
                self.release,
                command=[msg],
                cwd=tmp_dir
            )
        matches = re.findall(expected, logs)
        self.assertEqual(len(matches), 1, msg=logs)

    def test_dependencies(self):
        config = """
            dependencies: %s
        """ % indent(self.dependencies, '    ')
        msg = 'Grocker build this successfully !'
        expected = msg
        self.check(config, msg, expected)

    def test_entrypoint_name(self):
        config = """
            entrypoint_name: my-custom-runner
            dependencies: %s
        """ % indent(self.dependencies, '    ')
        msg = 'Grocker build this successfully !'
        expected = 'custom: %s' % msg
        self.check(config, msg, expected)


class BuildCustomRuntimeTestCase(BuildTestCase):
    runtime = 'python2.7'
