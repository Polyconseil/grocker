#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.

from __future__ import absolute_import, division, print_function, unicode_literals
import os
import re
import subprocess
import tempfile
import unittest
import uuid

import docker.errors
import yaml

import grocker.utils
import grocker.six


def docker_rmi(image):
    client = grocker.utils.docker_get_client()
    try:
        client.images.remove(image)
    except docker.errors.APIError:
        pass  # do not fail when image does not exist


def docker_run(image, command):
    client = grocker.utils.docker_get_client()

    container = client.containers.run(
        image=image,
        command=command,
        detach=True
    )

    return_code = container.wait()
    logs = container.logs()
    container.remove()

    return return_code, logs


def docker_inspect(image):
    client = grocker.utils.docker_get_client()
    return client.images.get(image).attrs


class AbstractBuildTestCase(unittest.TestCase):
    dependencies = yaml.safe_load("""
        - libzbar0: libzbar-dev
        - libjpeg62-turbo: libjpeg62-turbo-dev
        - libffi6: libffi-dev
        - libtiff5: libtiff5-dev
    """)
    runtime = None

    def run_grocker(self, release, command, cwd, docker_prefix):
        image_name = 'grocker.test/{}'.format(uuid.uuid4())
        result_file_path = os.path.join(
            cwd,
            'created-by-grocker',
            'grocker.results.yml',
        )
        try:
            call_args = [
                'python', '-m', 'grocker', 'build',
                '--image-name', image_name,
                '--result-file', result_file_path,
                '--no-push',
                release,
            ]
            if docker_prefix:
                call_args += ['--image-prefix', docker_prefix]
            if self.runtime:
                call_args += ['--runtime', self.runtime]
            subprocess.check_call(call_args, cwd=cwd)

            with open(result_file_path) as fp:
                results = yaml.load(fp)

            self.assertNotIn('hash', results)
            self.assertIn('image', results)
            self.assertEqual(image_name, results['image'])

            return_code, logs = docker_run(
                image_name,
                command,
            )

            self.assertEqual(return_code, 0, msg=logs)
            return logs.decode('utf-8'), docker_inspect(image_name)
        finally:
            docker_rmi(image_name)

    def check(self, config, release, cmd, expected, docker_prefix=None):
        with grocker.six.TemporaryDirectory() as tmp_dir:
            with open(os.path.join(tmp_dir, '.grocker.yml'), 'w') as fp:
                yaml.dump(config, fp)

            logs, inspect_data = self.run_grocker(
                release,
                command=[cmd] if not isinstance(cmd, list) else cmd,
                cwd=tmp_dir,
                docker_prefix=docker_prefix,
            )
        matches = re.findall(expected, logs)
        self.assertEqual(len(matches), 1, msg=logs)
        return logs, inspect_data


class BuildTestCase(AbstractBuildTestCase):

    def test_dependencies(self):
        config = {
            'dependencies': self.dependencies,
        }
        msg = 'Grocker build this successfully !'
        expected = msg
        self.check(config, 'grocker-test-project==2.0', msg, expected)

    def test_pip_constraints(self):
        with tempfile.NamedTemporaryFile() as fp:
            fp.write(b'qrcode==5.2')
            fp.flush()

            config = {
                'pip_constraint': fp.name,
                'entrypoint_name': '/bin/bash',
                'dependencies': self.dependencies,
            }
            self.check(config, 'grocker-test-project==2.0', ['-c', 'pip freeze'], 'qrcode==5.2')

    def test_extras(self):
        config = {
            'entrypoint_name': '/bin/bash',
            'dependencies': self.dependencies,
        }
        self.check(config, 'grocker-test-project[pep8]==2.0', ['-c', 'pip list'], 'pep8')

    def test_with_docker_prefix(self):
        config = {
            'entrypoint_name': '/bin/bash'
        }
        self.check(config, 'pep8==1.7', ['-c', 'pep8 --version'], '1.7.0', docker_prefix='grocker')

    def test_entrypoints(self):
        config = {
            'volumes': ['/data', '/config'],
            'ports': [8080, 9090],
            'entrypoint_name': 'my-custom-runner',
            'dependencies': self.dependencies,
        }
        msg = 'Grocker build this successfully !'
        expected = 'custom: %s' % msg
        _, inspect_data = self.check(config, 'grocker-test-project==2.0', msg, expected)

        volumes = sorted(inspect_data['Config'].get('Volumes', []))
        ports = sorted(inspect_data['Config'].get('ExposedPorts', []))
        self.assertEqual(volumes, ['/config', '/data'])
        self.assertEqual(ports, ['8080/tcp', '9090/tcp'])

    def test_repositories(self):
        config = {
            'dependencies': self.dependencies,
            'entrypoint_name': 'python',
            'repositories': {
                'nginx': {
                    'uri': 'deb http://nginx.org/packages/debian/ jessie nginx',
                    'key': """
                        -----BEGIN PGP PUBLIC KEY BLOCK-----
                        Version: GnuPG v1.4.11 (FreeBSD)

                        mQENBE5OMmIBCAD+FPYKGriGGf7NqwKfWC83cBV01gabgVWQmZbMcFzeW+hMsgxH
                        W6iimD0RsfZ9oEbfJCPG0CRSZ7ppq5pKamYs2+EJ8Q2ysOFHHwpGrA2C8zyNAs4I
                        QxnZZIbETgcSwFtDun0XiqPwPZgyuXVm9PAbLZRbfBzm8wR/3SWygqZBBLdQk5TE
                        fDR+Eny/M1RVR4xClECONF9UBB2ejFdI1LD45APbP2hsN/piFByU1t7yK2gpFyRt
                        97WzGHn9MV5/TL7AmRPM4pcr3JacmtCnxXeCZ8nLqedoSuHFuhwyDnlAbu8I16O5
                        XRrfzhrHRJFM1JnIiGmzZi6zBvH0ItfyX6ttABEBAAG0KW5naW54IHNpZ25pbmcg
                        a2V5IDxzaWduaW5nLWtleUBuZ2lueC5jb20+iQE+BBMBAgAoBQJOTjJiAhsDBQkJ
                        ZgGABgsJCAcDAgYVCAIJCgsEFgIDAQIeAQIXgAAKCRCr9b2Ce9m/YpvjB/98uV4t
                        94d0oEh5XlqEZzVMrcTgPQ3BZt05N5xVuYaglv7OQtdlErMXmRWaFZEqDaMHdniC
                        sF63jWMd29vC4xpzIfmsLK3ce9oYo4t9o4WWqBUdf0Ff1LMz1dfLG2HDtKPfYg3C
                        8NESud09zuP5NohaE8Qzj/4p6rWDiRpuZ++4fnL3Dt3N6jXILwr/TM/Ma7jvaXGP
                        DO3kzm4dNKp5b5bn2nT2QWLPnEKxvOg5Zoej8l9+KFsUnXoWoYCkMQ2QTpZQFNwF
                        xwJGoAz8K3PwVPUrIL6b1lsiNovDgcgP0eDgzvwLynWKBPkRRjtgmWLoeaS9FAZV
                        ccXJMmANXJFuCf26iQEcBBABAgAGBQJOTkelAAoJEKZP1bF62zmo79oH/1XDb29S
                        YtWp+MTJTPFEwlWRiyRuDXy3wBd/BpwBRIWfWzMs1gnCjNjk0EVBVGa2grvy9Jtx
                        JKMd6l/PWXVucSt+U/+GO8rBkw14SdhqxaS2l14v6gyMeUrSbY3XfToGfwHC4sa/
                        Thn8X4jFaQ2XN5dAIzJGU1s5JA0tjEzUwCnmrKmyMlXZaoQVrmORGjCuH0I0aAFk
                        RS0UtnB9HPpxhGVbs24xXZQnZDNbUQeulFxS4uP3OLDBAeCHl+v4t/uotIad8v6J
                        SO93vc1evIje6lguE81HHmJn9noxPItvOvSMb2yPsE8mH4cJHRTFNSEhPW6ghmlf
                        Wa9ZwiVX5igxcvaIRgQQEQIABgUCTk5b0gAKCRDs8OkLLBcgg1G+AKCnacLb/+W6
                        cflirUIExgZdUJqoogCeNPVwXiHEIVqithAM1pdY/gcaQZmIRgQQEQIABgUCTk5f
                        YQAKCRCpN2E5pSTFPnNWAJ9gUozyiS+9jf2rJvqmJSeWuCgVRwCcCUFhXRCpQO2Y
                        Va3l3WuB+rgKjsQ=
                        =A015
                        -----END PGP PUBLIC KEY BLOCK-----
                    """,
                },
            },
        }
        script = ";".join([
            "from __future__ import print_function",
            "import subprocess",
            "output = subprocess.check_output(['apt-cache', 'policy'])",
            "print('nginx' in output.decode())",
        ])
        self.check(config, 'grocker-test-project==2.0', ['-c', script], 'True')


class BuildCustomRuntimeTestCase(BuildTestCase):
    runtime = 'python2.7'


class AlpineTestCase(AbstractBuildTestCase):
    runtime = 'python2.7'
    dependencies = []

    def test_with_alpine(self):
        config = {
            'system': {
                'image': 'alpine',
                'base': [],
                'build': [],
                'runtime': {
                    'python2.7': [
                        'python2',
                        'py2-pip',
                        'py-virtualenv',
                    ],
                },
            },
            'entrypoint_name': '/bin/sh'
        }
        self.check(config, 'pep8==1.7', ['-c', 'pep8 --version'], '1.7.0', docker_prefix='grocker')
