#!/usr/bin/env bash
# Purpose
# =======

# This cron wrapper will perform the following tasks:
# - Run the given management command
# - Send its output (stdout + stderr) to a given logfile, depending on the command line
# - Log (to syslog) the result of the cron in a dedicated facility
# - If the command failed (non-zero exit, stderr output), send all (stdout+stderr) output to stdout / stderr in order to generate an email.

eval $(cat /home/blue/etc/cron.env | sed 's/^/export /')


# Settings
# ========

function get_django_setting () {
    ${VENV}/bin/python -c "from django.conf import settings; print settings.$1"
}

PROJECT=$(get_django_setting PROJECT_NAME)
PROJECT_NAME=$(echo ${PROJECT} | tr [a-z] [A-Z])
MANAGE_PY="${VENV}/bin/django-admin.py"  # Path to the django-admin.py command
LOG_FOLDER=/var/log/cronwrapper  # Where temporary log files should be created.
PID_FOLDER=/var/run/cronwrapper  # Where PID files are kept

# Usage
# =====

usage() {
  # Print the usage string and exit.
  # Extra arg: retcode: the exit code to use (defaults to 0).
  local retcode;
  retcode=${1:-0};

  echo "Usage: $0 --all|--help [--environment <environment>] [--fleet <fleet>] [--kill-previous] COMMAND [ARG1 ARG2 ...]

Run the COMMAND manage.py command within a wrapper which will capture stdout/stderr.

The Django settings module is taken from the environment variable '\$DJANGO_SETTINGS_MODULE', as usual for DJango apps.


Options:

  --help                        Show this help message
  --environment <environment>   Excecute command only for specified environment
  --fleet <fleet>               Execute command only for specified fleet
  --kill-previous               Kill the previous instance

Example:

  The command:
    $0 dumpdata auth
  Would run the following line:
    ${MANAGE_PY} dumpdata auth
";
  exit ${retcode};
}

# Options
# =======

# Capture all command arguments into the FULL_ARGS variable.
FULL_ARGS=$*;

# Check for at least two arguments (apart from --help / -h)
if [[ $# -lt 2 && $1 != "--help" && $1 != "-h" ]]; then
  echo -e "Expecting at least one command name.\n"
  usage 1;
fi

# SWITCH will be one of --all, --help. Shift it.
SWITCH=$1;
case $SWITCH in
  --master)
    # DEPRECATED: does nothing.
    shift 1;
    ;;
  --all)
    # Nothing to do (see test after the esac).
    shift 1;
    ;;

  --help)
    usage;;

  -h)
    usage;;

  *)
    ;;
esac;

# Check environment
if [[ "$1" == "--environment" ]]; then
    FOR_ENVIRONMENT=$2
    shift 2;
    if [[ $(get_django_setting ENVIRONMENT) != ${FOR_ENVIRONMENT} ]]; then
        logger -p cron.info "Cron ${FULL_ARGS} disabled: environment is not ${FOR_ENVIRONMENT}."
        exit 0;
    fi
fi

# Check fleet
if [[ "$1" == "--fleet" ]]; then
  FOR_FLEET=$2;
  shift 2;
  if [[ $(get_django_setting FLEET_ID) != ${FOR_FLEET} ]]; then
    # Log to the 'cron' facility, level 'info'.
    logger -p cron.info "Cron ${FULL_ARGS} disabled: fleet ${FOR_FLEET} is not the current fleet."
    exit 0;
  fi
fi

# Kill previous
KILL_PREVIOUS=0;
if [[ "$1" == "--kill-previous" ]]; then
  KILL_PREVIOUS=1;
  shift 1;
fi


# Command line building
# =====================

# Store the command name and the args list in two separate vars.
COMMAND=$1
# Remove the command name from $*
shift 1;
ARGS=$*


LOG_NAME=${LOG_NAME:-${COMMAND}}


# PID check
# =========

PIDFILE="${PID_FOLDER}/${LOG_NAME}.pid"

if [[ -f "${PIDFILE}" ]]; then
  OLD_PID=$(cat "${PIDFILE}");

  if kill -0 "${OLD_PID}" ; then  # Still running

    if [[ "${KILL_PREVIOUS}" = "1" ]]; then
      echo "Previous instance still running as ${OLD_PID}, killing it." >&2;
      kill -9 ${OLD_PID};
      sleep 1;
    else
      echo "Previous instance still running as ${OLD_PID}, aborting." >&2
      exit 1;
    fi
  fi

  rm -f "${PIDFILE}";
fi

echo -n $$ > "${PIDFILE}"


# Logging setup
# =============

DATE=`date +'%F_%H%M%S'`

# Logs will be written to two temporary files in order to be able know whether
# stderr was used.
LOGFILE_STDOUT="${LOG_FOLDER}/${LOG_NAME}-${DATE}.stdout"
LOGFILE_STDERR="${LOG_FOLDER}/${LOG_NAME}-${DATE}.stderr"

syslog_line() {
  # Log one line to syslog.
  # Args: level, line.
  local line level;
  facility=$(get_django_setting "LOGGING['handlers']['syslog']['facility']");
  level=$1;
  line=$2;
  logger -p ${facility}.${level} -t ${PROJECT}.cron.${LOG_NAME} -- ${line};
}

syslog_file() {
  # Log the lines of one file to syslog.
  # Args: level, file name.
  # The file will be logged as a single line, unless empty.
  local filename level content;
  level=$1;
  filename=$2;

  if [[ -s ${filename} ]]; then
    content=`cat ${filename}`;
    syslog_line ${level} "${content}";
  fi
}

# Command execution
# =================

# Prepare the command
CMD="${MANAGE_PY} ${COMMAND} ${ARGS}"

# Run it
${CMD} > ${LOGFILE_STDOUT} 2> ${LOGFILE_STDERR}
RETCODE=$?

# Remove our PIDFILE.
rm -f ${PIDFILE}


# Log handling
# ============

if [[ ${RETCODE} == 0 && -s ${LOGFILE_STDERR} ]]; then
  # STDERR was not empty
  RETCODE=-1;
fi

if [[ ${RETCODE} == 0 ]]; then  # Success
  # Log success and output to syslog
  syslog_line info "Cron $0 ${FULL_ARGS}: OK";
  syslog_file info ${LOGFILE_STDOUT};

  # Cleanup
  rm -f ${LOGFILE_STDOUT} ${LOGFILE_STDERR};

else  # Some failure (retcode != 0 or stderr)
  # Log failure to syslog
  syslog_line err "Cron $0 ${FULL_ARGS}: NOK (code ${RETCODE}).";

  syslog_file info ${LOGFILE_STDOUT};
  syslog_file err ${LOGFILE_STDERR};

  # Output to stdout/stderr to generate email
  echo "Project : ${PROJECT}" >&2;
  echo "Cron $0 ${FULL_ARGS} failed with status ${RETCODE}." >&2;
  cat ${LOGFILE_STDOUT};
  cat ${LOGFILE_STDERR} >&2;

  # Propagate return code
  exit ${RETCODE};
fi
