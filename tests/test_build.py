#! /usr/bin/env python
# Copyright (c) Polyconseil SAS. All rights reserved.


import os
import re
import subprocess  # noqa: S404
import sys
import tempfile
import unittest
import uuid

import docker.errors
import yaml

import grocker.utils


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
        detach=True,
    )

    return_code = container.wait()
    logs = container.logs()
    container.remove()

    return return_code, logs


def docker_inspect(image):
    client = grocker.utils.docker_get_client()
    return client.images.get(image).attrs


class AbstractBuildTestCase:
    dependencies = {}
    runtime = None
    tp_name = 'grocker-test-project'
    tp_version = '3.0.1'

    def run_grocker(self, release, command, cwd, docker_prefix):
        image_name = f'grocker.test/{uuid.uuid4()}'
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
            subprocess.check_call(call_args, cwd=cwd)  # noqa: S603

            with open(result_file_path) as fp:
                results = yaml.safe_load(fp)

            self.assertNotIn('hash', results)
            self.assertIn('image', results)
            self.assertEqual(image_name, results['image'])

            result, logs = docker_run(
                image_name,
                command,
            )

            self.assertEqual(result['StatusCode'], 0, msg=(result, logs))
            return logs.decode('utf-8'), docker_inspect(image_name)
        finally:
            docker_rmi(image_name)

    def check(self, config, release, cmd, expected, docker_prefix=None):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with open(os.path.join(tmp_dir, '.grocker.yml'), 'w') as fp:
                yaml.safe_dump(config, fp)

            logs, inspect_data = self.run_grocker(
                release,
                command=[cmd] if not isinstance(cmd, list) else cmd,
                cwd=tmp_dir,
                docker_prefix=docker_prefix,
            )
        matches = re.findall(expected, logs)
        self.assertEqual(len(matches), 1, msg=logs)
        return logs, inspect_data

    def test_dependencies(self):
        config = {
            'runtime': self.runtime,
            'dependencies': self.dependencies,
        }
        msg = 'Grocker build this successfully !'
        expected = msg
        self.check(config, f'{self.tp_name}=={self.tp_version}', msg, expected)

    def test_from_path(self):
        test_project_path = os.path.abspath(os.path.join(__file__, '..', 'resources', 'grocker-test-project'))
        subprocess.check_call(  # noqa: S603
            [
                sys.executable,
                'setup.py',
                'bdist_wheel',
                '--universal',
            ],
            cwd=test_project_path,
        )
        wheel_filepath = os.path.join(
            test_project_path, 'dist', 'grocker_test_project-3.0.1-py2.py3-none-any.whl',
        )
        config = {
            'runtime': self.runtime,
            'dependencies': self.dependencies,
        }
        msg = 'Grocker build this successfully !'
        expected = msg
        self.check(config, wheel_filepath, msg, expected)

    def test_from_path_with_extra(self):
        test_project_path = os.path.abspath(os.path.join(__file__, '..', 'resources', 'grocker-test-project'))
        subprocess.check_call(  # noqa: S603
            [
                sys.executable,
                'setup.py',
                'bdist_wheel',
                '--universal',
            ],
            cwd=test_project_path,
        )
        # Specificy [pep8] extra requirement
        wheel_filepath = os.path.join(
            test_project_path, 'dist', 'grocker_test_project-3.0.1-py2.py3-none-any.whl[pep8]',
        )
        config = {
            'runtime': self.runtime,
            'dependencies': self.dependencies,
        }
        msg = 'Grocker build this successfully !'
        expected = msg
        self.check(config, wheel_filepath, msg, expected)

    def test_pip_constraints(self):
        with tempfile.NamedTemporaryFile() as fp:
            fp.write(b'qrcode==5.2')
            fp.flush()

            config = {
                'pip_constraint': fp.name,
                'entrypoint_name': '/bin/sh',
                'runtime': self.runtime,
                'dependencies': self.dependencies,
            }
            self.check(config, f'{self.tp_name}=={self.tp_version}', ['-c', 'pip freeze'], 'qrcode==5.2')

    def test_extras(self):
        config = {
            'entrypoint_name': '/bin/sh',
            'runtime': self.runtime,
            'dependencies': self.dependencies,
        }
        self.check(config, f'{self.tp_name}[pep8]=={self.tp_version}', ['-c', 'pip list'], 'pep8')

    def test_with_docker_prefix(self):
        config = {
            'runtime': self.runtime,
            'entrypoint_name': '/bin/sh',
        }
        self.check(config, 'pep8==1.7', ['-c', 'pep8 --version'], '1.7.0', docker_prefix='grocker')

    def test_envs(self):
        config = {
            'runtime': self.runtime,
            'envs': {
                'GROCKER_EXTRA_ENVVAR': 'Grocker!',
            },
            'entrypoint_name': '/bin/sh',
        }
        self.check(
            config,
            'pep8==1.7',
            ['-c', 'env'],
            'GROCKER_EXTRA_ENVVAR=Grocker!',
            docker_prefix='grocker',
        )

    def test_entrypoints(self):
        config = {
            'volumes': ['/data', '/config'],
            'ports': [8080, 9090],
            'entrypoint_name': 'my-custom-runner',
            'runtime': self.runtime,
            'dependencies': self.dependencies,
        }
        msg = 'Grocker build this successfully !'
        expected = 'custom: %s' % msg
        _, inspect_data = self.check(config, f'{self.tp_name}=={self.tp_version}', msg, expected)

        volumes = sorted(inspect_data['Config'].get('Volumes', []))
        ports = sorted(inspect_data['Config'].get('ExposedPorts', []))
        self.assertEqual(volumes, ['/config', '/data'])
        self.assertEqual(ports, ['8080/tcp', '9090/tcp'])


class DebianBuildTestCase(AbstractBuildTestCase, unittest.TestCase):
    runtime = 'buster/3.9'
    dependencies = {
        'build': ['libjpeg62-turbo-dev'],
        'run': ['libjpeg62-turbo'],
    }

    def test_repositories(self):
        config = {
            'runtime': self.runtime,
            'dependencies': self.dependencies,
            'entrypoint_name': 'python',
            'repositories': {
                'nginx': {
                    'uri': 'deb http://nginx.org/packages/debian/ jessie nginx',
                    'key': """
                        -----BEGIN PGP PUBLIC KEY BLOCK-----
                        Version: GnuPG v2.0.22 (GNU/Linux)

                        mQENBE5OMmIBCAD+FPYKGriGGf7NqwKfWC83cBV01gabgVWQmZbMcFzeW+hMsgxH
                        W6iimD0RsfZ9oEbfJCPG0CRSZ7ppq5pKamYs2+EJ8Q2ysOFHHwpGrA2C8zyNAs4I
                        QxnZZIbETgcSwFtDun0XiqPwPZgyuXVm9PAbLZRbfBzm8wR/3SWygqZBBLdQk5TE
                        fDR+Eny/M1RVR4xClECONF9UBB2ejFdI1LD45APbP2hsN/piFByU1t7yK2gpFyRt
                        97WzGHn9MV5/TL7AmRPM4pcr3JacmtCnxXeCZ8nLqedoSuHFuhwyDnlAbu8I16O5
                        XRrfzhrHRJFM1JnIiGmzZi6zBvH0ItfyX6ttABEBAAG0KW5naW54IHNpZ25pbmcg
                        a2V5IDxzaWduaW5nLWtleUBuZ2lueC5jb20+iQE+BBMBAgAoAhsDBgsJCAcDAgYV
                        CAIJCgsEFgIDAQIeAQIXgAUCV2K1+AUJGB4fQQAKCRCr9b2Ce9m/YloaB/9XGrol
                        kocm7l/tsVjaBQCteXKuwsm4XhCuAQ6YAwA1L1UheGOG/aa2xJvrXE8X32tgcTjr
                        KoYoXWcdxaFjlXGTt6jV85qRguUzvMOxxSEM2Dn115etN9piPl0Zz+4rkx8+2vJG
                        F+eMlruPXg/zd88NvyLq5gGHEsFRBMVufYmHtNfcp4okC1klWiRIRSdp4QY1wdrN
                        1O+/oCTl8Bzy6hcHjLIq3aoumcLxMjtBoclc/5OTioLDwSDfVx7rWyfRhcBzVbwD
                        oe/PD08AoAA6fxXvWjSxy+dGhEaXoTHjkCbz/l6NxrK3JFyauDgU4K4MytsZ1HDi
                        MgMW8hZXxszoICTTiQEcBBABAgAGBQJOTkelAAoJEKZP1bF62zmo79oH/1XDb29S
                        YtWp+MTJTPFEwlWRiyRuDXy3wBd/BpwBRIWfWzMs1gnCjNjk0EVBVGa2grvy9Jtx
                        JKMd6l/PWXVucSt+U/+GO8rBkw14SdhqxaS2l14v6gyMeUrSbY3XfToGfwHC4sa/
                        Thn8X4jFaQ2XN5dAIzJGU1s5JA0tjEzUwCnmrKmyMlXZaoQVrmORGjCuH0I0aAFk
                        RS0UtnB9HPpxhGVbs24xXZQnZDNbUQeulFxS4uP3OLDBAeCHl+v4t/uotIad8v6J
                        SO93vc1evIje6lguE81HHmJn9noxPItvOvSMb2yPsE8mH4cJHRTFNSEhPW6ghmlf
                        Wa9ZwiVX5igxcvaIRgQQEQIABgUCTk5b0gAKCRDs8OkLLBcgg1G+AKCnacLb/+W6
                        cflirUIExgZdUJqoogCeNPVwXiHEIVqithAM1pdY/gcaQZmIRgQQEQIABgUCTk5f
                        YQAKCRCpN2E5pSTFPnNWAJ9gUozyiS+9jf2rJvqmJSeWuCgVRwCcCUFhXRCpQO2Y
                        Va3l3WuB+rgKjsQ=
                        =EWWI
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
        self.check(config, f'{self.tp_name}=={self.tp_version}', ['-c', script], 'True')


class AlpineTestCase(AbstractBuildTestCase, unittest.TestCase):
    runtime = 'alpine/3'
    dependencies = {
        'build': ['libjpeg-turbo-dev', 'zlib-dev'],
        'run': ['libjpeg-turbo', 'zlib'],
    }
