#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This is our entry point script which is ran into our container
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
import shutil
import string
import subprocess

BLUE_HOME = '/home/blue'
CONFIG_MOUNT_POINT = '/config'
DJANGO_SETTINGS_PATH = os.path.join(BLUE_HOME, 'django_config')
ENV_CONFIG = os.path.join(BLUE_HOME, 'etc', 'config.env')
LOG_DIR = os.path.join(BLUE_HOME, 'logs')
RUN_DIR = os.path.join(BLUE_HOME, 'run')
SCRIPT_DIR = '/scripts'
TEMPLATE_PATH = os.path.join(BLUE_HOME, 'templates')
VENV = os.path.join(BLUE_HOME, 'app')
VENV_BIN = os.path.join(VENV, 'bin')


def templatize(filename, dest, context):
    filename = os.path.join(TEMPLATE_PATH, filename)
    with open(dest, 'w') as fw:
        with open(filename) as fh:
            fw.write(string.Template(fh.read()).substitute(context))


class EntryPoint(object):
    """EntryPoint script main class"""

    def __init__(self, args):
        self.logger = logging.getLogger(__name__)
        self.user_home = os.path.expanduser('~')
        self.command = args[0]
        self.args = args[1:]

        # our context, passed to our configuration template
        self.context = {}
        self.load_environment()

    def gen_context(self, **kwargs):
        self.context['django_config_path'] = DJANGO_SETTINGS_PATH
        self.context['python_version'] = os.environ['PYTHON_VERSION']
        self.context['project_name'] = os.environ['PROJECT_NAME']
        self.context['project_name_upper'] = self.context['project_name'].upper()
        self.context['venv'] = VENV
        self.context.update(kwargs)

        return self.context

    def load_environment(self):
        """A provisioning script is installed in /tmp"""
        regex = re.compile("^([a-zA-Z_1-9]*)=(.*)$")
        with open(ENV_CONFIG) as fh:
            for line in fh.readlines():
                if line.strip() == '':
                    continue
                r = regex.search(line)
                if r:
                    key, value = r.groups()
                    os.environ[key] = value
                else:
                    self.logger.info("> line '%s' is not an environment variable" % line)

    def run_command(self, *args):
        """Run a command"""
        self.logger.info("-> running %s", ' '.join(args))
        try:
            subprocess.check_call(args)
        except subprocess.CalledProcessError:
            pass

    def run(self):
        self.gen_context()
        self._setup_si()

        service_mapping = {
            'cron': self.run_cron,
            'django-admin': self.django_admin,
            'script': self.run_script,
            'shell': self.run_shell,
            'si-service': self.run_si,
        }

        fn = service_mapping.get(self.command, self.run_command)
        fn(self.command, *self.args)

    def _setup_environ(self, **kwargs):
        """In some case, we have to setup the environ"""
        environ = os.environ.copy()
        environ.update(kwargs)
        return environ

    def _setup_dir(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
        else:
            self.logger.info("%s already exists !", path)

    def _setup_si(self):
        """Take care of django SI configuration:
            * moves configuration from /config/SI/*ini to $HOME/django_settings/
        """
        for path in (DJANGO_SETTINGS_PATH, LOG_DIR, RUN_DIR, os.path.join(LOG_DIR, 'nginx')):
            self._setup_dir(path)

        templatize('settings.ini', os.path.join(DJANGO_SETTINGS_PATH, '50_base_settings.ini'), self.context)

        si_mounted_config_dir = os.path.join(CONFIG_MOUNT_POINT, 'si_config')
        if not os.path.exists(si_mounted_config_dir):
            self.logger.warning("No 'si_config' directory found")
            return

        for filename in os.listdir(si_mounted_config_dir):
            shutil.copy(
                src=os.path.join(si_mounted_config_dir, filename),
                dst=os.path.join(DJANGO_SETTINGS_PATH, filename),
            )

    def _run_custom_command(self, cmd_line):
        """Run a script or the django-admin command"""
        project_settings = os.path.join(DJANGO_SETTINGS_PATH, '*.ini')
        environ = {
            'PATH': "%s%s%s" % (os.environ['PATH'], os.pathsep, VENV_BIN),
            'DJANGO_SETTINGS_MODULE': '{project_name}.settings'.format(**self.context),
            '{project_name_upper}_CONFIG'.format(**self.context): project_settings,
        }
        self.logger.info("running %s", " ".join(cmd_line))
        environ = self._setup_environ(**environ)
        process = subprocess.Popen(cmd_line, env=environ, cwd=SCRIPT_DIR)
        process.wait()

    def django_admin(self, command, *args):
        """Run django-admin.py from the virtualenv"""
        binary = os.path.join(VENV_BIN, 'django-admin.py')
        cmd_line = [binary]
        cmd_line.extend(args)
        self._run_custom_command(cmd_line)

    def run_script(self, command, *args):
        """Runs a script that HAS to begin with a shbang """
        script_name = args[0]
        script_path = os.path.join(SCRIPT_DIR, script_name)
        cmd_line = [script_path]
        cmd_line.extend(args[1:])
        self._run_custom_command(cmd_line)

    def run_shell(self, command, *args):
        """simply start a shell"""
        self.run_command('bash')

    def run_si(self, command, *args):
        """Run the corresponding service with uwsgi & nginx"""
        service = args[0]
        self.context['service'] = service
        templatize('uwsgi.ini', os.path.join(self.user_home, 'etc', 'uwsgi.ini'), self.context)
        templatize('nginx.conf', os.path.join(self.user_home, 'etc', 'nginx.conf'), self.context)

        supervisord_config = os.path.join(self.user_home, 'etc', 'supervisord.conf')
        templatize('supervisord.conf', supervisord_config, self.context)

        self.run_command('supervisord', '-c', supervisord_config)

    def run_cron(self, *args):
        templatize('cron.env', os.path.join(self.user_home, 'etc', 'cron.env'), self.context)
        self.run_command('sudo', 'cron', '-f')


def setup_logging(enable_colors):
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


def main():
    parser = argparse.ArgumentParser(prog='entrypoint', description='Docker entry point')
    parser.add_argument('--disable-colors', help='disable colors')
    parser.add_argument('args', nargs='+', help='the command and its arguments')
    args = parser.parse_args()

    setup_logging(not args.disable_colors)
    entry_point = EntryPoint(args=args.args)
    entry_point.run()

if __name__ == '__main__':
    main()
