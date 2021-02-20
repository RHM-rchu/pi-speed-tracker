#!/usr/bin/bash
the_home=$HOME
export WORKON_HOME=${the_home}/.virtualenvs
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
source /usr/local/bin/virtualenvwrapper.sh
workon py3cv4
