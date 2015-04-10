#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This is our entrypoint script which is ran into our container
    on startup.

    It's meant to:

        * prepare the configuration of the container
        * run the correct SERVICE (for django projects)
        * run a command and its parameters
        * start cron jobs
"""

import argparse
import logging
import logging.config
import os
import re
import string
import subprocess

DEFAULT_USER = 'blue'
BLUE_HOME = '/home/blue'
CONFIG_MOUNT_POINT = '/config'
ENV_CONFIG = os.path.join('/tmp', 'config.env')
TEMPLATE_PATH = os.path.join(BLUE_HOME, 'templates')


def templatize(filename, dest, context):
    filename = os.path.join(TEMPLATE_PATH, filename)
    with open(dest, 'w') as fw:
        with open(filename) as fh:
            fw.write(string.Template(fh.read()).substitute(context))


class EntryPoint(object):
    """EntryPoint script main class"""

    def __init__(self, service, enable_colors):
        # our program logger
        self.logger = None
        self.user_home = os.path.expanduser('~')
        self.service = service[0]
        self.args = service[1:]

        # our context, passed to our configuration template
        self.context = {}

        self.setup_logging(enable_colors)
        self.load_environment()
        self.si_name = self.context['project_name']

    def gen_context(self, **kwargs):
        self.context['python_version'] = os.environ['PYTHON_VERSION']
        self.context['project_name'] = os.environ['PACKAGE_NAME'].split('==')[0]
        self.context['project_name_upper'] = self.context['project_name'].upper()
        self.context.update(kwargs)

        return self.context

    def load_environment(self):
        """A provisioning script is installd in /tmp"""
        regex = re.compile("^([a-zA-Z_1-9]*)=(.*)$")
        with open(ENV_CONFIG) as fh:
            for line in fh.readlines():
                r = regex.search(line)
                if r:
                    key, value = r.groups()
                    os.environ[key] = value
                else:
                    print("line '%s' is not an envion" % line)

    def setup_logging(self, enable_colors):
        colors = {'begin': '\033[1;33m', 'end': '\033[0m'}
        if not enable_colors:
            colors = {'begin': '', 'end': ''}

        logging.config.dictConfig({
            'version': 1,
            'formatters': {
                'simple': {
                    'format': '{begin}%(message)s{end}'.format(**colors)
                },
            },
            'handlers': {
                'console': {'class': 'logging.StreamHandler', 'formatter': 'simple'},
            },
            'loggers': {
                __name__: {'handlers': ['console'], 'level': 'INFO'},
            },
        })

        self.logger = logging.getLogger(__name__)

    def run_command(self, *args):
        """Run a command"""
        self.logger.info("-> running %s", ' '.join(args))
        try:
            subprocess.check_call(args)
        except subprocess.CalledProcessError:
            pass

    def run(self):
        self.gen_context(service=self.service)
        service_mapping = {
            'shell': self.run_shell,
            'ops': self.run_si,
        }

        fn = service_mapping.get(self.service, self.run_command)
        fn(self.service, *self.args)

    def run_shell(self, service, *args):
        """simply start a shell"""
        self.run_command('bash')

    def run_si(self, si_service, *args):
        # configure uwsgi
        templatize(
            'uwsgi.ini',
            os.path.join(self.user_home, 'uwsgi.ini'),
            self.context,
        )

        # configure nginx
        os.makedirs(os.path.join(self.user_home, 'nginx'))
        templatize(
            'nginx.conf',
            os.path.join(self.user_home, 'nginx.conf'),
            self.context,
        )
        # configure the django project
        # put configuration to /etc/<siname>/

        si_name_config_path = os.path.join(self.user_home, self.si_name)

        os.makedirs(si_name_config_path)
        templatize(
            'settings.ini',
            os.path.join(si_name_config_path, 'settings.ini'),
            self.context,
        )

        # configure supervisord
        supervisord_config = os.path.join(self.user_home, 'supervisord.conf')
        templatize(
            'supervisord.conf',
            supervisord_config,
            self.context,
        )

        # run supervisord
        self.run_command('supervisord', '-c', supervisord_config)


def main():
    parser = argparse.ArgumentParser(prog='entrypoint', description='Docker entry point')
    parser.add_argument('service', nargs='+', help='the service to run')
    parser.add_argument('--disable-colors', help='disable colors')

    args = parser.parse_args()
    entry_point = EntryPoint(
        service=args.service,
        enable_colors=not args.disable_colors,
    )
    entry_point.run()

if __name__ == '__main__':
    main()
