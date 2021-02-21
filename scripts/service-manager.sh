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
APP_SPEED="speed-tracker.py"
APP_WEB="web-server.py"
SCRIPTPATH=$(dirname $( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P ))
DIR="${BASH_SOURCE%/*}"

if [[ ! -d "$DIR" ]]; then DIR="$PWD"; fi
. ${DIR}/load.py.virtualenv.sh

cd "${SCRIPTPATH}"

#---------------------------- functions
help() {
    local msg=$1
    printf "${msg}"
cat <<EOT

===============================
Usagefor  $0 
===============================
  --app= or -a) speed or web, if no other flags passed default is to resturn the status

  --status= or -s) Returns status of apps
    $0 --status

  --execute= or -x) stop|start|restart app, When passed with --app show status, if no --app applies to all apps
    $0 --app=web -x start           <--- start web
    $0 -x start -a web              <--- start web
    $0 -x stop                      <--- stop all
    $0 -execute stop -app speed     <--- stop speed-tracker.py only
    $0 -x restart -a web            <--- restart web only
    $0 -a web -x status             <--- return just PID for web, for status checks from other scripts

  --help= or -h) This menus
    $0 -h

EOT
}
app_start() {
    local APP=$1
    # no app specified do both
    # only if pid greater than 0 ignore
    if [[ -z "$APP" ]]; then 
        [ "${pid_speed:-0}" -gt "0" ] || python $APP_SPEED --show_image=False &
        [ "${pid_web:-0}" -gt "0" ] || python $APP_WEB &
    else
        if [[ "${APP}" == "${APP_SPEED}" ]]; then
            [ "${pid_speed:-0}" -gt "0" ] || python $APP --show_image=False &
        elif [[ "${APP}" == "${APP_WEB}" ]]; then
            [ "${pid_web:-0}" -gt "0" ] || python $APP &
        fi
    fi
}
app_stop() {
    local APP=$1
    echo "app_stop---->${APP}"
    # no app specified do both
    # only if pid id is greater than 0
    if [[ -z "$APP" ]]; then 
        [ "${pid_speed:-0}" -gt "0" ] && sudo kill $pid_speed
        [ "${pid_web:-0}" -gt "0" ] && sudo kill $pid_web
    else
        if [[ "${APP}" = "${APP_SPEED}" ]]; then
            [ "${pid_speed:-0}" -gt "0" ] && sudo kill $pid_speed
        elif [[ "${APP}" = "${APP_WEB}" ]]; then
            [ "${pid_web:-0}" -gt "0" ] && sudo kill $pid_web
        fi
    fi
    app_status
}
app_restart() {
    local APP=$1
    app_stop $APP
    echo "Pausing for 2 sec to let system catch up"
    sleep 1
    app_start $APP
}
app_status() {
    local APP=$1
    local tmppid
    if [[ -z "$APP" ]]; then
        pid_speed=$(pgrep -f "${FILEVARMAP["speed"]}")
        pid_web=$(pgrep -f "${FILEVARMAP["web"]}")
    elif [[ ! -z APP ]]; then
        tmppid=$(pgrep -f "${FILEVARMAP[$APP]}");
        echo ${tmppid:-0};
        exit 0;
    fi
}


#---------------------------- arguments
while [ $# -gt 0 ]; do
  case "$1" in
    --app*|-a*)
      if [[ "$1" != *=* ]]; then shift; fi # Value is next arg if no `=`
      APP="${1#*=}"
      ;;
    --status*|-s*)
      if [[ "$1" != *=* ]]; then shift; fi # Value is next arg if no `=`
      STATUS=1
      ;;
    --execute*|-x*)
      if [[ "$1" != *=* ]]; then shift; fi # Value is next arg if no `=`
      ACTION="${1#*=}"
      ;;
    --help|-h)
      help "[Usage] Here's how to use this script\n"
      exit 0
      ;;
    *)
      >&2 help "[Error] Invalid argument\n"
      exit 1
      ;;
  esac
  shift
done

declare -A FILEVARMAP
FILEVARMAP=( 
    ["speed"]="${APP_SPEED}" ["speed-tracker"]="${APP_SPEED}" ["${APP_SPEED}"]="${APP_SPEED}"  
    ["web"]="${APP_WEB}" ["web-server"]="${APP_WEB}" ["${APP_WEB}"]="${APP_WEB}" 
    )
app_status

#---------------------------- execute
if [[ "$ACTION" = "start" ]]; then
    app_start "${FILEVARMAP[$APP]}"
elif [[ "$ACTION" = "stop"  ]]; then
    app_stop "${FILEVARMAP[$APP]}"
elif [[ "$ACTION" = "restart"  ]]; then
    app_restart "${FILEVARMAP[$APP]}"
    sleep 2
elif [[ "$ACTION" = "status"  ]]; then
    app_status "${FILEVARMAP[$APP]}"
fi

#---------------------------- status
app_status
cat <<EOT

===============================
${APP_SPEED} is running with pid:   [${pid_speed:-OFF}]
${APP_WEB} is running with pid:     [${pid_web:-OFF}]
===============================


EOT

exit 0
