#!/usr/bin/bash


# cat <<EOT > /etc/systemd/system/py-web-tracker.service
# [Unit]
# Description=Car Speed Tracker
# DefaultDependencies=no
# After=multi-user.target
# RequiresMountsFor=/var/log
# IgnoreOnIsolate=yes
#
# [Service]
# Type=oneshot
# User=pi
# Group=pi
# RemainAfterExit=yes
# WorkingDirectory=/home/pi/repos/speed-camera
# ExecStartPre=/home/pi/repos/car-speed-tracker/load.py.virtualenv.sh
# ExecStart=/home/pi/repos/car-speed-tracker/web-server.sh
#
# [Install]
# WantedBy=multi-user.target
# EOT

# systemctl daemon-reload
# systemctl enable py-web-tracker.service
# systemctl restart py-web-tracker.service
# systemctl statis py-web-tracker.service

# systemctl --failed
# virtualenv and virtualenvwrapper
SCRIPTPATH=$(dirname $( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P ))
export WORKON_HOME=$HOME/.virtualenvs
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
source /usr/local/bin/virtualenvwrapper.sh
source /opt/intel/openvino/bin/setupvars.sh
source $HOME/.virtualenvs/cv/bin/activate
workon cv
cd "$SCRIPTPATH"
/usr/bin/python3 web-server.py &
exit 0
