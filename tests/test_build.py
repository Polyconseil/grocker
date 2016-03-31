#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.

from __future__ import absolute_import, division, print_function, unicode_literals
import os
import re
import subprocess
import sys
import textwrap
import unittest
import uuid

import grocker.builders as grocker_builders
import grocker.six as grocker_six


def docker_rmi(image):
    client = grocker_builders.docker_get_client()
    client.remove_image(image)


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


class BuildTestCase(unittest.TestCase):
    RELEASE = 'grocker-test-project==1.0.0'

    def run_grocker(self, cwd=None):
        image_name = 'grocker.test/{}'.format(uuid.uuid4())
        runtime = 'python{}'.format(sys.version_info[0])
        msg = 'Grocker build this successfully !'
        try:
            subprocess.check_call(
                [
                    'python', '-m', 'grocker',
                    '--image-name', image_name,
                    '--runtime', runtime,
                    'dep', 'img',
                    self.RELEASE
                ],
                cwd=cwd,
            )

            return_code, logs = docker_run(
                image_name,
                ['--', 'python', '-m', 'gtp', msg]
            )

            self.assertEqual(return_code, 0, msg=logs)
            matches = re.findall(msg, logs.decode('utf-8'))
            self.assertEqual(len(matches), 2)
        finally:
            docker_rmi(image_name)

    def test_dep_img_steps(self):  # but not push
        self.run_grocker()

    def test_minimal_dependencies(self):
        config = """
        dependencies:
            - libzbar0: libzbar-dev
            - libjpeg62-turbo: libjpeg62-turbo-dev
            - libffi6: libffi-dev
            - libtiff5: libtiff5-dev
        """

        with grocker_six.TemporaryDirectory() as tmp_dir:
            with open(os.path.join(tmp_dir, '.grocker.yml'), 'w') as fp:
                fp.write(textwrap.dedent(config[1:]))

            self.run_grocker(cwd=tmp_dir)
