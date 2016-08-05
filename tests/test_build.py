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
import yaml

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


def docker_inspect(image):
    client = grocker_builders.docker_get_client()
    return client.inspect_image(image)


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

    def run_grocker(self, release, command, cwd):
        image_name = 'grocker.test/{}'.format(uuid.uuid4())
        result_file_path = os.path.join(
            cwd,
            'created-by-grocker',
            'grocker.results.yml',
        )
        try:
            subprocess.check_call(
                [
                    'python', '-m', 'grocker',
                    '--docker-image-prefix', 'grocker',
                    '--image-name', image_name,
                    '--result-file', result_file_path,
                    'dep', 'img',
                    release,
                ] + (
                    ['--runtime', self.runtime] if self.runtime else []
                ),
                cwd=cwd,
            )

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

    def check(self, config, cmd, expected):
        with grocker_six.TemporaryDirectory() as tmp_dir:
            with open(os.path.join(tmp_dir, '.grocker.yml'), 'w') as fp:
                fp.write(textwrap.dedent(config[1:]))

            logs, inspect_data = self.run_grocker(
                self.release,
                command=[cmd] if not isinstance(cmd, list) else cmd,
                cwd=tmp_dir
            )
        matches = re.findall(expected, logs)
        self.assertEqual(len(matches), 1, msg=logs)
        return logs, inspect_data

    def test_dependencies(self):
        config = """
            dependencies: %s
        """ % indent(self.dependencies, '    ')
        msg = 'Grocker build this successfully !'
        expected = msg
        self.check(config, msg, expected)

    def test_entrypoints(self):
        config = """
            volumes: ['/data', '/config']
            ports: [8080, 9090]
            entrypoint_name: my-custom-runner
            dependencies: %s
        """ % indent(self.dependencies, '    ')
        msg = 'Grocker build this successfully !'
        expected = 'custom: %s' % msg
        _, inspect_data = self.check(config, msg, expected)

        volumes = sorted(inspect_data['Config'].get('Volumes', []))
        ports = sorted(inspect_data['Config'].get('ExposedPorts', []))
        self.assertEqual(volumes, ['/config', '/data'])
        self.assertEqual(ports, ['8080/tcp', '9090/tcp'])

    def test_repositories(self):
        config = """
            dependencies: %s
            entrypoint_name: python
            repositories:
                nginx:
                    uri: deb http://nginx.org/packages/debian/ jessie nginx
                    key: |
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
        """ % indent(self.dependencies, '    ')
        script = ";".join([
            "from __future__ import print_function",
            "import subprocess",
            "output = subprocess.check_output(['apt-cache', 'policy'])",
            "print('nginx' in output.decode())",
        ])
        self.check(config, ['-c', script], 'True')


class BuildCustomRuntimeTestCase(BuildTestCase):
    runtime = 'python2.7'
