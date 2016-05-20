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
    def test_parse_config(self):
        grocker_yml_content = """
            file: .grocker.yml
            not_used_key: .grocker.yml
            runtime: should-not-be-used
        """[1:-1]

        first_config_content = """
            file: first.yml
            dependencies: should-be-used
        """[1:-1]

        second_config_content = """
            file: second.yml
            runtime: should-be-used
        """[1:-1]

        with mkchtmpdir() as tmp_dir:
            write_file(tmp_dir, '.grocker.yml', grocker_yml_content)
            write_file(tmp_dir, 'first.yml', first_config_content)
            write_file(tmp_dir, 'second.yml', second_config_content)

            config = parse_config(['first.yml', 'second.yml'])
            self.assertNotIn('not_used_key', config)  # .grocker.yml is not read
            self.assertIn('entrypoint_name', config)  # grocker internal config is read
            self.assertEqual(config.get('dependencies'), 'should-be-used')  # from first.yml
            self.assertEqual(config.get('runtime'), 'should-be-used')  # from second.yml
            self.assertEqual(config.get('file'), 'second.yml')  # from second.yml
