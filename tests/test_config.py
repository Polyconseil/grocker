# Copyright (c) Polyconseil SAS. All rights reserved.

import contextlib
import itertools
import os
import os.path
import tempfile
import textwrap
import unittest

import grocker.builders as grocker_builders
import grocker.utils as grocker_utils


@contextlib.contextmanager
def mkchtmpdir():
    with tempfile.TemporaryDirectory() as tmp_dir:
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            yield tmp_dir
        finally:
            os.chdir(old_cwd)


def write_file(directory, name, content):
    with open(os.path.join(directory, name), 'w') as fp:
        fp.write(textwrap.dedent(content))


class ConfigTestCase(unittest.TestCase):
    grocker_yml_content = """
        file: .grocker.yml
        not_used_key: .grocker.yml
        runtime: .grocker.yml
    """[1:-1]

    first_config_content = """
        file: first.yml
        dependencies: first.yml
    """[1:-1]

    second_config_content = """
        file: second.yml
        runtime: second.yml
    """[1:-1]

    def test_parse_config(self):
        with mkchtmpdir() as tmp_dir:
            write_file(tmp_dir, '.grocker.yml', self.grocker_yml_content)
            write_file(tmp_dir, 'first.yml', self.first_config_content)
            write_file(tmp_dir, 'second.yml', self.second_config_content)

            config = grocker_utils.parse_config(['first.yml', 'second.yml'])
            self.assertNotIn('not_used_key', config)  # .grocker.yml is not read
            self.assertIn('entrypoint_name', config)  # grocker internal config is read
            self.assertEqual(config.get('dependencies'), 'first.yml')  # from first.yml
            self.assertEqual(config.get('runtime'), 'second.yml')  # from second.yml
            self.assertEqual(config.get('file'), 'second.yml')  # from second.yml

    def test_not_existing_config(self):
        try:
            raised_error = FileNotFoundError
        except NameError:
            raised_error = IOError

        with mkchtmpdir() as tmp_dir:
            write_file(tmp_dir, '.grocker.yml', self.grocker_yml_content)
            self.assertRaises(raised_error, grocker_utils.parse_config, ['not_existing_config_file.yml'])

    def test_empty_config(self):
        with mkchtmpdir() as tmp_dir:
            write_file(tmp_dir, 'empty.yml', '')
            config = grocker_utils.parse_config(['empty.yml'])
            self.assertIn('entrypoint_name', config)  # grocker internal config is read

    def test_not_grocker_yml(self):
        with mkchtmpdir():
            config = grocker_utils.parse_config([])
            self.assertIn('entrypoint_name', config)  # grocker internal config is read

    def test_grocker_yml(self):
        with mkchtmpdir() as tmp_dir:
            write_file(tmp_dir, '.grocker.yml', self.grocker_yml_content)
            config = grocker_utils.parse_config([])
            self.assertIn('not_used_key', config)  # .grocker.yml is read
            self.assertIn('entrypoint_name', config)  # grocker internal config is read


class GrockerRequirementTestCase(unittest.TestCase):

    def test_existing_filepath(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = 'grocker_test_project-1.2.3-py2.py3-none-any.whl'
            filepath = os.path.join(tmpdir, filename)
            with open(filepath, 'w'):
                pass
            grocker_req = grocker_utils.GrockerRequirement.parse(filepath)
            self.assertEqual('1.2.3', grocker_req.version)
            self.assertEqual('grocker-test-project', grocker_req.project_name)
            self.assertEqual([], grocker_req.extras)
            self.assertEqual(filepath, grocker_req.filepath)

    def test_existing_filepath_with_extras(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = 'grocker_test_project-1.2.3-py2.py3-none-any.whl'
            filepath = os.path.join(tmpdir, filename)
            with open(filepath, 'w'):
                pass
            grocker_req = grocker_utils.GrockerRequirement.parse(filepath + '[extra2,extra1]')
            self.assertEqual('1.2.3', grocker_req.version)
            self.assertEqual('grocker-test-project', grocker_req.project_name)
            self.assertEqual(['extra1', 'extra2'], grocker_req.extras)
            self.assertEqual(filepath, grocker_req.filepath)

    def test_valid_req(self):
        grocker_req = grocker_utils.GrockerRequirement.parse('grocker-test-project[extra2, extra1]==2.0')
        self.assertEqual('2.0', grocker_req.version)
        self.assertEqual('grocker-test-project', grocker_req.project_name)
        self.assertEqual(['extra1', 'extra2'], grocker_req.extras)
        self.assertIsNone(grocker_req.filepath)

    def test_invalid_reqs(self):
        for invalid_req in (
            './grocker_test_project-1.2.3-py2.py3-none-any.whl',  # Unexistent file
            'grocker-test-project == 2.0 @ file://toto',
        ):
            with self.assertRaises(ValueError):
                grocker_utils.GrockerRequirement.parse(invalid_req)


class DefaultImageNameTestCase(unittest.TestCase):

    def test_default_image_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = 'grocker_test_project-1.2.3-py2.py3-none-any.whl'
            filepath = os.path.join(tmpdir, filename)
            with open(filepath, 'w'):
                pass
            releases = (
                'grocker-test-project==2.0.0',
                'grocker-test-project[pep8]==2.0.0',
                'grocker-test-project[pep8, other_extra]==2.0.0+git1234',
                filepath,
            )
            image_names = (None, 'demo-app')
            docker_prefixes = (None, 'registry.local')
            product = itertools.product(releases, image_names, docker_prefixes)
            expected_names = [
                # classic
                'grocker-test-project:2.0.0',
                'registry.local/grocker-test-project:2.0.0',
                'demo-app:2.0.0',
                'registry.local/demo-app:2.0.0',
                # with extra
                'grocker-test-project-pep8:2.0.0',
                'registry.local/grocker-test-project-pep8:2.0.0',
                'demo-app:2.0.0',
                'registry.local/demo-app:2.0.0',
                # with several extras and + sign
                'grocker-test-project-other_extra-pep8:2.0.0-git1234',
                'registry.local/grocker-test-project-other_extra-pep8:2.0.0-git1234',
                'demo-app:2.0.0-git1234',
                'registry.local/demo-app:2.0.0-git1234',
                # from path
                'grocker-test-project:1.2.3',
                'registry.local/grocker-test-project:1.2.3',
                'demo-app:1.2.3',
                'registry.local/demo-app:1.2.3',
            ]

            for (release, image_base_name, docker_image_prefix), expected in zip(product, expected_names):
                config = {
                    'image_base_name': image_base_name,
                    'docker_image_prefix': docker_image_prefix,
                }
                grocker_req = grocker_utils.GrockerRequirement.parse(release)
                got = grocker_utils.default_image_name(config, grocker_req)
                self.assertEqual(got, expected)


class PipConfigTestCase(unittest.TestCase):

    def test_get_pip_env(self):
        with tempfile.NamedTemporaryFile(prefix="grocker") as f:
            f.write(textwrap.dedent("""\
                [global]
                timeout=99
                index-url=http://example.com/simple
            """).encode())
            f.flush()
            env = grocker_builders.wheels.get_pip_env(f.name)
        self.assertEqual(
            env,
            {
                'PIP_TIMEOUT': '99',
                'PIP_INDEX_URL': 'http://example.com/simple',
            },
        )
