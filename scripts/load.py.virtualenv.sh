#!/usr/bin/bash
export WORKON_HOME=/home/pi/.virtualenvs
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
source /usr/local/bin/virtualenvwrapper.sh
source /opt/intel/openvino/bin/setupvars.sh
source /home/pi/.virtualenvs/cv/bin/activate
workon cv