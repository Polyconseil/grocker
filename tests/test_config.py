# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.

from __future__ import absolute_import, division, print_function, unicode_literals
import contextlib
import io
import os
import os.path
import textwrap
import unittest

from grocker.__main__ import parse_config
import grocker.six as grocker_six


@contextlib.contextmanager
def mkchtmpdir():
    with grocker_six.TemporaryDirectory() as tmp_dir:
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            yield tmp_dir
        finally:
            os.chdir(old_cwd)


def write_file(directory, name, content):
    with io.open(os.path.join(directory, name), 'w') as fp:
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

            config = parse_config(['first.yml', 'second.yml'])
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
            self.assertRaises(raised_error, parse_config, ['not_existing_config_file.yml'])

    def test_not_grocker_yml(self):
        with mkchtmpdir():
            config = parse_config([])
            self.assertIn('entrypoint_name', config)  # grocker internal config is read

    def test_grocker_yml(self):
        with mkchtmpdir() as tmp_dir:
            write_file(tmp_dir, '.grocker.yml', self.grocker_yml_content)
            config = parse_config([])
            self.assertIn('not_used_key', config)  # .grocker.yml is read
            self.assertIn('entrypoint_name', config)  # grocker internal config is read