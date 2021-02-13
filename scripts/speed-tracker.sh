#!/usr/bin/bash


# cat <<EOT > /etc/systemd/system/speed-tracker.service
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
# WorkingDirectory=/home/pi/repos/car-speed-tracker
# ExecStartPre=/home/pi/repos/car-speed-tracker/scripts/load.py.virtualenv.sh
# ExecStart=/home/pi/repos/car-speed-tracker/scripts/speed-tracker.sh
#
# [Install]
# WantedBy=multi-user.target
# EOT

# systemctl daemon-reload
# systemctl enable speed-tracker.service
# systemctl restart speed-tracker.service
# systemctl status speed-tracker.service

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
/usr/bin/python3 speed-tracker.py --show_image=False &
exit 0
