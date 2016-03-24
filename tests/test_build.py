#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.

from __future__ import absolute_import, division, print_function, unicode_literals
import re
import subprocess
import unittest
import uuid

import grocker.builders as grocker_builders


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

    def test_dep_img_steps(self):  # but not push
        image_name = 'grocker.test/{}'.format(uuid.uuid4())
        runtime = 'python2'
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
            )

            return_code, logs = docker_run(
                image_name,
                ['--', 'python', '-m', 'gtp', msg]
            )

            self.assertEqual(return_code, 0)
            matches = re.findall(msg, logs)
            self.assertEqual(len(matches), 2)
        finally:
            docker_rmi(image_name)
