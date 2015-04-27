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
from __future__ import absolute_import, division, print_function, unicode_literals
import argparse
import logging
import logging.config
import os
import re
import shutil
import socket
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


def templatize(filename, destination_path, context):
    filename = os.path.join(TEMPLATE_PATH, filename)
    with open(os.path.expanduser(destination_path), 'w') as fw:
        with open(filename) as fh:
            fw.write(string.Template(fh.read()).substitute(context))


def get_host_ip():
    output = subprocess.check_output(['ip', 'route', 'show', '0.0.0.0/0'])
    matched = re.search(r'via\s([0-9.]+)\s', output)
    return matched.groups()[0]


def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)
    else:
        logging.getLogger(__name__).info("%s already exists !", path)


def execute(*args):
    """Run a command"""
    logging.getLogger(__name__).info("-> running %s", ' '.join(args))
    try:
        subprocess.check_call(args)
    except subprocess.CalledProcessError:
        pass


def get_context():  # TODO: replace by ad-hoc context in function ?
    return {
        'django_config_path': DJANGO_SETTINGS_PATH,
        'python_version': os.environ['PYTHON_VERSION'],
        'project_name': os.environ['PROJECT_NAME'],
        'project_name_upper': os.environ['PROJECT_NAME'].upper(),
        'venv': VENV,
    }


def setup_environment():
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
                logging.getLogger(__name__).info("> line '%s' is not an environment variable" % line)

    os.environ.update({
        'PATH': '{0}{1}{2}'.format(os.path.join(VENV, 'bin'), os.pathsep, os.environ['PATH']),
        'DJANGO_SETTINGS_MODULE': '{0}.settings'.format(os.environ['PROJECT_NAME']),
        '{0}_CONFIG'.format(os.environ['PROJECT_NAME'].upper()): os.path.join(DJANGO_SETTINGS_PATH, '*.ini'),
    })


def setup_app():
    """Take care of django SI configuration:
        * moves configuration from /config/SI/*ini to $HOME/django_settings/
    """
    for path in (DJANGO_SETTINGS_PATH, LOG_DIR, RUN_DIR):
        create_directory(path)

    templatize('settings.ini', os.path.join(DJANGO_SETTINGS_PATH, '50_base_settings.ini'), get_context())

    si_mounted_config_dir = os.path.join(CONFIG_MOUNT_POINT, 'app')
    if not os.path.exists(si_mounted_config_dir):
        logging.getLogger(__name__).warning("No 'app' directory found")
        return

    for filename in os.listdir(si_mounted_config_dir):
        shutil.copy(
            src=os.path.join(si_mounted_config_dir, filename),
            dst=os.path.join(DJANGO_SETTINGS_PATH, filename),
        )


def setup_mail_relay():
    fqdn = socket.getfqdn()
    get_mail_cmd = [  # FIXME
        'python', '-c',
        'from django.conf import settings; print settings.LOGGING["handlers"]["maildev"]["toaddrs"][0]'
    ]

    context = {
        'smtp_server': get_host_ip(),
        'fqdn': fqdn,
        'domain': '.'.join(fqdn.split('.')[1:]),
        'mailto': subprocess.check_output(get_mail_cmd),
    }

    templatize('ssmtp.conf', os.path.join('~', 'etc', 'ssmtp.conf'), context)


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


def run_shell(*args):
    """Runs a script that HAS to begin with a shebang"""
    args = list(args)
    script_path = os.path.join(SCRIPT_DIR, args[0])
    if os.path.exists(script_path):
        args[0] = script_path

    logging.getLogger(__name__).info("running %s", " ".join(args))
    process = subprocess.Popen(args, cwd=SCRIPT_DIR)
    process.wait()


def start_service(command, *args):
    """Run the corresponding service with uwsgi & nginx"""
    context = get_context()
    context['service'] = args[0]
    templatize('uwsgi.ini', os.path.join('~', 'etc', 'uwsgi.ini'), context)
    templatize('nginx.conf', os.path.join('~', 'etc', 'nginx.conf'), context)

    supervisord_config = os.path.expanduser(os.path.join('~', 'etc', 'supervisord.conf'))
    templatize('supervisord.conf', supervisord_config, context)

    execute('supervisord', '-c', supervisord_config)


def run_cron(self, *args):
    templatize('cron.env', os.path.join('~', 'etc', 'cron.env'), get_context())
    execute('sudo', 'cron', '-f')


def dispatch(args):
    service_mapping = {
        'cron': run_cron,
        'start': start_service,
    }

    args = args or ['/bin/bash']
    fn = service_mapping.get(args[0], run_shell)
    fn(*args)


def main():
    parser = argparse.ArgumentParser(prog='entrypoint', description='Docker entry point')
    parser.add_argument('--disable-colors', help='disable colors')
    parser.add_argument('args', nargs='*', help='the command and its arguments')
    args = parser.parse_args()

    setup_logging(not args.disable_colors)
    setup_environment()
    setup_mail_relay()
    setup_app()

    dispatch(args.args)

if __name__ == '__main__':
    main()
