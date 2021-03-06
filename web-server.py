# from http.server import BaseHTTPRequestHandler, HTTPServer
import http.server
import json
import base64
import datetime, time, os, sys
import re

import subprocess, socketserver

import socketserver
from urllib.parse import urlparse, parse_qs
from mako.template import Template

from _configs import *
from _sqlite3_functions import *


DOW = ("Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday")
DATE_FORMAT = '%Y-%m-%d'
CONFIG_FILE='_configs.py'
COORD_FILE='_coords.py'
THEUSER = os.getlogin()
CRONFILE = 'tmp_crontab.txt'
SQL_SELECT_APPLY_ALL = f" and sd<={INGNORE_SD_GT} and counter>{INGNORE_CNT_LT} "
# generate a config file if not exists
if os.path.isfile(CONFIG_FILE) == False:
    os.system(f'cp sample_configs.py {CONFIG_FILE}')


#~~~~~~~~~~~~~~~~ temp rename old coord file to new
if os.path.isfile('_configs_coords.py') == True:
    os.rename('_configs_coords.py', COORD_FILE)
#~~~~~~~~~~~~~~~~ 

if os.path.isfile("_coords.py"):
    from _coords import *
else:
    UPPER_LEFT_X = 0
    UPPER_LEFT_Y = 0
    LOWER_RIGHT_X = 0
    LOWER_RIGHT_Y = 0


logfile_base = os.path.dirname(os.path.abspath(LOG_FILE_WEB))
os.makedirs(logfile_base, exist_ok=True)
logfile = open(LOG_FILE_WEB,'w', 1)
sys.stdout = logfile
sys.stdin = logfile
sys.stderr = logfile

# hostName = "localhost"
hostName = ""
serverPort = 8080

#-----------------------------------------
# DB
#-----------------------------------------
def get_data_speed_matrix(date_begin, date_end):
    ttl_records = 0
    webSpeeDict = [None] * len(WEB_SPEED_DICT)

    for i, val in enumerate(WEB_SPEED_DICT):
        webSpeeDict[i] = val.copy()
        webSpeeDict[i]['lists'] = [0 for x in range(0, 24)]

    datebegin = date_begin.replace("-","")
    dateend = date_end.replace("-","")

    result = db_select_record(f'''
        SELECT mean_speed, hour from {DB_TABLE} WHERE date BETWEEN '{datebegin}' and '{dateend}' {SQL_SELECT_APPLY_ALL}
        ''')

    if result:
        for row in result:
            hr = int(row['hour'])
            sp = int(f"{float(row['mean_speed']):.0f}")

            for i, val in enumerate(webSpeeDict):
                if sp >= webSpeeDict[i]['speed_low'] and sp <= webSpeeDict[i]['speed_high']:
                    webSpeeDict[i]['lists'][(hr - 1)] += 1
                    webSpeeDict[i]['total'] = sum(webSpeeDict[i]['lists'])
                    ttl_records += 1

    return (webSpeeDict, ttl_records)

def get_data_day_of_week(date_begin, date_end):
    ttl_records = 0
    webSpeeDict = {}
    dow_stats = { i : {'count':0, 'categories':{}} for i in DOW }

    for i, val in enumerate(WEB_SPEED_DICT):
        webSpeeDict[val['name']] = {
            'name': val['name'],
            'rgb': val['rgb'],
            'count':0,
        }
        for dow in DOW:
            webSpeeDict[val['name']][dow] = {
                'speed': 0,
                'count': 0,
                'percentage': 0,
            }

    datebegin = date_begin.replace("-","")
    dateend = date_end.replace("-","")

    result = db_select_record(f'''
        SELECT mean_speed, date from {DB_TABLE} WHERE date BETWEEN '{datebegin}' and '{dateend}' {SQL_SELECT_APPLY_ALL}
        ''')

    if result:
        for row in result:
            dow = datetime.datetime.strptime(row['date'], '%Y%m%d').strftime('%A')
            sp = int(f"{float(row['mean_speed']):.0f}")

            dow_stats[dow]['count'] += 1
            for i, val in enumerate(WEB_SPEED_DICT):
                if sp >= val['speed_low'] and sp <= val['speed_high']:
                    webSpeeDict[val['name']][dow]['speed'] = int((webSpeeDict[val['name']][dow]['speed'] + sp)/2)
                    webSpeeDict[val['name']][dow]['count'] +=  1
                    webSpeeDict[val['name']]['count'] += 1
                    ttl_records += 1

                    if val['name'] not in dow_stats[dow]['categories']:
                        dow_stats[dow]['categories'][val['name']] = {
                            'count': 1,
                            'avespeed': sp,
                            'rgb': val['rgb'],
                        }
                    else:
                        dow_stats[dow]['categories'][val['name']]['count'] += 1
                        dow_stats[dow]['categories'][val['name']]['avespeed'] = int((dow_stats[dow]['categories'][val['name']]['avespeed'] + sp)/2)
             
    return (webSpeeDict, dow_stats, ttl_records)

def get_data_speed_list(
        date_begin, 
        date_end, 
        maxPerPage=1000, 
        page=1,
        direction=None,
        speed_range=None,
        speed_limit=SPEED_LIMIT,
        sort=None,
        ):
    # global DB_TABLE
    datebegin = date_begin.replace("-","")
    dateend = date_end.replace("-","")
    page = int(page)
    order_by = ''
    maxPerPage = int(maxPerPage)
    speed_limit = int(speed_limit)

    if page > 1:
        # e = maxPerPage * page
        # b = maxPerPage * (page - 1)
        # limit = f"{b}, {e}"
        # e = maxPerPage * page
        b = maxPerPage * (page - 1)
        limit = f"{b}, {maxPerPage}"
    else:
        limit = maxPerPage 

    sql_speed_range = ''
    sql_direction = f" and direction='{direction}'" if direction else ""

    if speed_range:
        for i, val in enumerate(WEB_SPEED_DICT):
            if val['name'] == speed_range:
                sql_speed_range = f"and (mean_speed >= {val['speed_low']} and mean_speed <= {val['speed_high']})"
                # sql_speed_range = "and mean_speed BETWEEN %.2f and %.2f" % ( (float(val['speed_low']) - .5), (float(val['speed_high']) + .5) )

    if sort is not None:
        order_by = f" ORDER BY id {sort}"

    result = db_select_record(f'''SELECT count(date) as total 
        from {DB_TABLE}
        WHERE date BETWEEN '{datebegin}' and '{dateend}'  {sql_direction}  {sql_speed_range}  {SQL_SELECT_APPLY_ALL};''')
    print("-------> " + SQL_SELECT_APPLY_ALL)
    total = int(result[0]['total'])
    total_page = int(total/maxPerPage)  + (total % maxPerPage > 0)

    result = db_select_record(f'''SELECT id, date, hour, minute, round(mean_speed, 2) as mean_speed, 
        direction, image_path, round(sd, 0) as sd, counter
        from {DB_TABLE} 
        WHERE date BETWEEN '{datebegin}' and '{dateend}' {sql_direction} {sql_speed_range} {SQL_SELECT_APPLY_ALL}
        {order_by}
        LIMIT {limit}''')
 
    return result, total_page, total

def get_data_server_status(date_today, web_statuspage_limit=10):
    date_today = date_today.replace("-","")
    result = db_select_record(f'''SELECT count(date) as total 
        from {DB_TABLE}
        WHERE date BETWEEN '{date_today}' and '{date_today}' {SQL_SELECT_APPLY_ALL};''') 
    total = int(result[0]['total'])

    result = db_select_record(f'''select * from {DB_TABLE} WHERE  sd<={INGNORE_SD_GT} and counter>{INGNORE_CNT_LT} order by id DESC limit {web_statuspage_limit}''')
 
    return result, total


#-----------------------------------------
# General
#-----------------------------------------
def is_daemon_active(daemon):
    command = f"./scripts/service-manager.sh  -a {daemon} -x status > tmp"
    os.system(command)
    with open('tmp') as tmp:
        tmp = tmp.read()
        tmppid = int(re.sub(r'\W+', '', tmp))
    os.remove('tmp')
    return tmppid

def restart_services(cam):
    #--- turn cam on/off
    if cam == "debugger-speedcam":
        if CONSOLE_DEBUGGER >= 3: print("[INFO] restarting speed cam with debugger")
        os.system("./scripts/service-manager.sh -a speed -x stop")
        os.system("./scripts/service-manager.sh -a speed -x start-debug")
        time.sleep(1)
    if cam == "restart-speedcam":
        if CONSOLE_DEBUGGER >= 3: print("[INFO] restarting speed cam")
        os.system("./scripts/service-manager.sh -a speed -x restart")
        time.sleep(1)
    if cam == "start-speedcam":
        if CONSOLE_DEBUGGER >= 3: print("[INFO] starting speed cam")
        os.system("./scripts/service-manager.sh -a speed -x start")
        time.sleep(1)
    elif cam == "stop-speedcam":
        if CONSOLE_DEBUGGER >= 3: print("[INFO] stopping speed cam")
        os.system("./scripts/service-manager.sh -a speed -x stop" )
        time.sleep(1)
    if cam == "restart-web":
        if CONSOLE_DEBUGGER >= 3: print("[INFO] restarting web-server cam")
        os.system("./scripts/service-manager.sh -a web -x restart" )


def convert_list_to_int(thelist):
    numbers  = [ int(x) for x in thelist ]
    return numbers


def convert_millisec_2_time(epoch, fmt='%A %d %B %Y %I:%M:%S%p'):
    epoch = int(float(epoch))
    s = float(epoch) / 1000.0
    date_full = datetime.datetime.fromtimestamp(s).strftime(fmt)
    return epoch, date_full


def take_snapshot(snapshot=False):
    imgPath = f"{PATH_TO_IMAGES}/calibrator.jpg"

    if os.path.isfile(imgPath) == True and snapshot == False: 
        # return f"{PATH_TO_IMAGES}/calibrate.jpg", 0
        return imgPath, 0


    if CONSOLE_DEBUGGER >= 4: print("[NOTICE] generating snapshot from webcam")

    from picamera.array import PiRGBArray
    from picamera import PiCamera
    import cv2

    pid = is_daemon_active('speed')

    if pid > 0: 
        if CONSOLE_DEBUGGER >= 4: print("[NOTICE] Stopping speed tracker")
        restart_services('stop-speedcam')

    camera = PiCamera()
    camera.resolution = RESOLUTION
    camera.framerate = FPS
    camera.vflip = False
    camera.hflip = False
    rawCapture = PiRGBArray(camera, size=camera.resolution)
    # allow the camera to warmup
    time.sleep(0.8)
    # grab an image from the camera
    camera.capture(rawCapture, format="bgr", use_video_port=True)

    if CONSOLE_DEBUGGER >= 4: print("[NOTICE] Capture Image")
    image = rawCapture.array

    txt_date = datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p")
    cv2.putText(image, txt_date,
        (10, image.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 1)

    if CONSOLE_DEBUGGER >= 4: print("[NOTICE] Saving Image")
    cv2.imwrite(imgPath, image)
    camera.close()

    return imgPath, pid

def save_backup_first(backupFile=''):
    if backupFile:
        backupDir = '.bak'
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        os.makedirs(backupDir, exist_ok=True)
        print(f"[STATUS] backing up {backupFile} to {backupDir}/{backupFile}.{timestamp}")
        os.system(f'cp {backupFile} {backupDir}/{backupFile}.{timestamp}')

def save_coord_conf(
        tx=0,
        ty=0,
        bx=0,
        by=0,
    ):
    # timestamp = datetime.datetime.timestamp(datetime.datetime.now())

    if tx > bx:
        bx,tx = tx,bx   
    if ty > by:
        by,ty = ty,by  
    # I know this is not needed bc of the above, but you never know
    t_width = tx-bx if tx > bx else bx-tx
    t_height = ty-by if ty > by else by-ty

    if bx > 0 and by > 0:
        coords_to_data = (f"""
UPPER_LEFT_X = {tx}
UPPER_LEFT_Y = {ty}
LOWER_RIGHT_X = {bx}
LOWER_RIGHT_Y = {by}
TARGET_WIDTH = {t_width}
TARGET_HEIGHT = {t_height}
""")

        # print(f"coords_to_data")
    else:
        return None

    save_backup_first(COORD_FILE)

    #--- write to file
    if CONSOLE_DEBUGGER >= 3: print("[INFO] Updating Coordinates")
    f = open(COORD_FILE, 'w+')
    f.write(coords_to_data+"\n")
    f.close


def save_config(config=None):
    if config == None:
        return None

    #--- write to file
    save_backup_first(CONFIG_FILE)
    if CONSOLE_DEBUGGER >= 3: print("[INFO] Updating Configs")
    f = open(CONFIG_FILE, 'w+')
    f.write(config+"\n")
    f.close
    return True


def set_cronfile_for_read():
    # print(f"[STATUS] created {CRONFILE}")
    cur_cron = os.popen(f'crontab -l > {CRONFILE}');
    cur_cron.read();
    cur_cron.close();


def save_cron(
    onbootwebserver=None,
    scheduleron=None,
    sp_start_hr=None,
    sp_start_min=None,
    sp_stop_hr=None,
    sp_stop_min=None,
    ):
    newline = ""
    with open(CRONFILE,'r') as file:
        # print(f"[STATUS] opened {CRONFILE}")
        for line in file:
            if 'service-manager.sh' not in line:
                newline += line
    if onbootwebserver == 1:
        newline += '@reboot ${HOME}/repos/pi-speed-tracker/scripts/service-manager.sh -a web -x start >/dev/null 2>&1\n'
    if scheduleron == 1:
        newline += '%s %s * * * ${HOME}/repos/pi-speed-tracker/scripts/service-manager.sh -a speed -x start >/dev/null 2>&1\n' % (sp_start_min, sp_start_hr)
        newline += '%s %s * * * ${HOME}/repos/pi-speed-tracker/scripts/service-manager.sh -a speed -x stop >/dev/null 2>&1\n' % (sp_stop_min, sp_stop_hr)
    # #--- write to file
    if CONSOLE_DEBUGGER >= 3: print("[INFO] Updating crontab")
    f = open(CRONFILE, 'w+')
    f.write(newline)
    f.close
    cur_cron = os.popen(f"crontab {CRONFILE}")

    return True



#-----------------------------------------
# HTML
#-----------------------------------------
def render_html_restart_service(
        ):
    sp_tracker_running = is_daemon_active('speed')
    htmllist = Template(filename='html/_restart_service.html')
    return  htmllist.render(
        sp_tracker_running=sp_tracker_running
        )

def render_html_form(
        date_today, 
        date_begin, 
        date_end, 
        maxPerPage=0, 
        direction=None,
        speed_limit=None,
        speed_range=None,
        sort=None,
        ):
    htmllist = Template(filename='html/_form.html')
    html = htmllist.render(
        date_begin=date_begin,
        date_end=date_end,
        date_today=date_today,
        maxPerPage=maxPerPage,
        direction=direction,
        speed_limit=speed_limit,
        speed_range=speed_range,
        LEFT_TO_RIGHT=LEFT_TO_RIGHT,
        RIGHT_TO_LEFT=RIGHT_TO_LEFT,
        WEB_SPEED_DICT=WEB_SPEED_DICT,
        sort=sort,
        )
    return html

def render_html_overview(
        date_today,
        date_begin,
        date_end,
        query_string,
        ):
    
    matrix, ttl_records = get_data_speed_matrix(date_begin, date_end)


    #################################
    speed_lists = {}
    graph_hrly_datas = {}
    total = ""
    percent = 0
    for i, val in enumerate(matrix):
        if 'total' in val: total = val['total']
        else: total = 0

        if total > 0 and ttl_records > 0:
            percent = "{0}".format(round(total/ttl_records*100, 2))
        else: 
            percent = 0
            
        speed_lists[val['name']] = {
            "count": total, 
            "rgb":val['rgb'], 
            "percent": percent,
            }
        graph_hrly_datas[val['name']] = {
            "rgb":val['rgb'], 
            "data":[str(element) for element in val['lists']],
            }

    form=render_html_form(
        date_today=date_today, 
        date_begin=date_begin,
        date_end=date_end,
        speed_limit=SPEED_LIMIT,
        );
    graph_hrly = Template(filename='html/_overview.html')
    # print(speed_lists)

    html = graph_hrly.render(
        graph_hrly_datas=graph_hrly_datas,
        percent_sp_list=speed_lists,
        total_sp=ttl_records,
        date_today=date_today,
        date_begin=date_begin,
        date_end=date_end,
        speed_limit=SPEED_LIMIT,
        form=form, 
        query_string=query_string,
        )
    return html


def render_html_speed_list(date_today, 
        date_begin, 
        date_end,
        query_string, 
        maxPerPage=1000, 
        page=1, 
        direction=None,
        speed_range=None,
        sort='DESC',
        ):

    speed_lists, total_pages, total_count = get_data_speed_list(
        date_begin=date_begin, 
        date_end=date_end, 
        maxPerPage=maxPerPage, 
        page=page, 
        direction=direction,
        speed_range=speed_range,
        speed_limit=SPEED_LIMIT,
        sort=sort,
        )

    if direction == None: direction = True
    hours24 = [0 for x in range(1, 24)]
    speed_dict = []
    epoch = 0

    for speed in speed_lists:
        epoch, date_full = convert_millisec_2_time(speed['id'])
        speed['date_full'] = date_full

        speed_dict.append({
            'mean_speed': round(speed['mean_speed'], 0),
            'date_full': date_full,
            'epoch': epoch,
            'direction': speed['direction'],
            })

    if not speed_dict: 
        dateObj = datetime.date.today()
        date_full = dateObj.strftime('%Y-%m-%d %H:%M:%S')
        speed_dict.append({
            'mean_speed': 0,
            'date_full': date_full,
            'epoch': 0,
            'direction': LEFT_TO_RIGHT,
            })
        speed_dict.append({
            'mean_speed': 0,
            'date_full': date_full,
            'epoch': 0,
            'direction': RIGHT_TO_LEFT,
            })

    form=render_html_form(
        date_today=date_today, 
        date_begin=date_begin, 
        date_end=date_end, 
        maxPerPage=maxPerPage, 
        direction=direction,
        speed_limit=SPEED_LIMIT,
        speed_range=speed_range,
        sort=sort,
        );

    query_string = re.sub('&?page=[0-9]*', '', query_string)
    htmllist = Template(filename='html/_list.html')
    html = htmllist.render(
        speed_lists=speed_lists,
        speed_dict=speed_dict,
        speed_limit=SPEED_LIMIT,
        hours24=hours24,
        query_string=query_string,
        epoch=epoch,
        form=form,
        page=page,
        total_count=total_count,
        total_pages=int(total_pages),
        LEFT_TO_RIGHT=LEFT_TO_RIGHT,
        RIGHT_TO_LEFT=RIGHT_TO_LEFT,
        )
    return html

def render_html_day_of_week(
        date_today,
        date_begin,
        date_end,
        query_string,
        ):
    
    matrix, dow_stats, ttl_records = get_data_day_of_week(date_begin, date_end)

    for  val in matrix:
        for dow in DOW:

            if ttl_records == 0:
                matrix[val][dow]['percentage'] = 0
            else:
                matrix[val][dow]['percentage'] = round(matrix[val][dow]['count']/matrix[val]['count']*100, 2)

            if val in dow_stats[dow]['categories']:
                matrix[val][dow]['percentage_dow'] = round(dow_stats[dow]['categories'][val]['count']/dow_stats[dow]['count']*100, 1)
            else: 
                matrix[val][dow]['percentage_dow'] = 0

    # for  dow in DOW:
    #     for  val in WEB_SPEED_DICT:
    #         dow_stats[dow]['categories'][val['name']]['percentage'] = round(dow_stats[dow]['categories'][val['name']]['count']/dow_stats[dow]['count']*100, 1)


    form=render_html_form(
        date_today=date_today, 
        date_begin=date_begin,
        date_end=date_end,
        speed_limit=SPEED_LIMIT,
        );
    graph_dow = Template(filename='html/_day-of-week.html')

    html = graph_dow.render(
        DOW=DOW,
        day_of_week=matrix,
        dow_stats=dow_stats,
        total_sp=ttl_records,
        date_today=date_today,
        date_begin=date_begin,
        date_end=date_end,
        speed_limit=SPEED_LIMIT,
        form=form, 
        # query_string=query_string,
        )
    return html



def render_html_calibrate(
        querycomponents,
        ):
    upper_left_x = UPPER_LEFT_X
    upper_left_y = UPPER_LEFT_Y
    lower_right_x = LOWER_RIGHT_X
    lower_right_y = LOWER_RIGHT_Y
    messages = []
    snapshot = False # mode to take snapshot with cam

    tx = ty = bx = by = 0

    if 'begin_xy' in querycomponents:
        begin_xy = querycomponents["begin_xy"][0]  
        tx, ty = [int(s) for s in begin_xy.split(',')]
    if 'end_xy' in querycomponents:
        end_xy = querycomponents["end_xy"][0]
        bx, by = [int(s) for s in end_xy.split(',')]
    if 'snapshot' in querycomponents:
        snapshot = True


    if int(bx) > 0 and int(by) > 0:
        upper_left_x=tx
        upper_left_y=ty
        lower_right_x=bx
        lower_right_y=by
        save_coord_conf(tx, ty, bx, by)
        snapshot = False
        messages.append({
            'status': 'message',
            'message': f"Coordinates saved! [BEGIN] x:{tx} y:{ty} and [END] x:{bx} y:{by}",
            })
        messages.append({
            'status': 'warn',
            'message': f"Restart the WebServer to load in the new configs",
            })

    image_path, pid=take_snapshot(snapshot)

    if pid > 0: 
        if CONSOLE_DEBUGGER >= 4: print("[NOTICE] Starting speed tracker")
        restart_services('start-speedcam')

    restart_service = render_html_restart_service()
    calibrator = Template(filename='html/_calibrate.html')
    html = calibrator.render( 
        # query_string=query_string,
        upper_left_x=upper_left_x,
        upper_left_y=upper_left_y,
        lower_right_x=lower_right_x,
        lower_right_y=lower_right_y,
        width=lower_right_x-upper_left_x,
        height=lower_right_y-upper_left_y,
        # upper_left_x=UPPER_LEFT_X if 'UPPER_LEFT_X' in vars() else 0,
        image_path=image_path,
        messages=messages,
        restart_service=restart_service,
        )

    # if pid > 0: restart_services('start-speedcam')
    return html



def render_html_log(log=None):
    htmllist = Template(filename='html/log-view.html')
    html = htmllist.render(
        WEB_REQURE_AUTH=WEB_REQURE_AUTH,
        WEB_USERNAME=WEB_USERNAME,
        WEB_PASSWORD=WEB_PASSWORD,
        log=log,
        )
    return html

def render_html_status(date_today, web_statuspage_limit=None):
    latest_records, total = get_data_server_status(date_today, web_statuspage_limit)

    i=0
    for speed in latest_records:
        epoch, date_full = convert_millisec_2_time(speed['id'])
        latest_records[i]['date_full'] = date_full
        latest_records[i]['epoch'] = epoch
        latest_records[i]['speed'] = round(float(speed['mean_speed']), 0)
        latest_records[i]['sd'] = round(float(speed['sd']), 0)
        i+=1

    sp_tracker_running = is_daemon_active('speed')

    restart_service = render_html_restart_service()
    htmllist = Template(filename='html/_status.html')
    html = htmllist.render(sp_tracker_running=sp_tracker_running,
        latest_records=latest_records,
        total=total,
        web_statuspage_limit=web_statuspage_limit,
        restart_service=restart_service,
        )
    return html


def render_html_config_editor(querycomponents=None):
    configContent = None
    messages = []
    if 'configs' in querycomponents:
        configContent = querycomponents["configs"][0] 
        saveStatus = save_config(config=configContent)
        if saveStatus == True:
            messages.append({
            'status': 'message',
            'message': "Configs Saved!",
            })

    if configContent is None:
        with open(CONFIG_FILE,'r') as file:
            configContent = file.read()

    restart_service = render_html_restart_service()
    htmllist = Template(filename='html/_config_editor.html')
    html = htmllist.render(
        messages=messages,
        configContent=configContent,
        restart_service=restart_service,
        )
    return html


def render_html_cron_editor(querycomponents=None):
    configContent = None
    messages = []
    onbootwebserver = False
    scheduleron = False
    sp_start_hr=0
    sp_start_min=0
    sp_start_ampm = 'AM'
    sp_stop_hr=0
    sp_stop_min=0
    sp_stop_ampm = 'PM'

    # set_cronfile_for_read()


    if 'submit' in querycomponents:
        # print(f"[STATUS] processing submitted data")
        if 'onbootwebserver' in querycomponents:
            onbootwebserver = int(querycomponents["onbootwebserver"][0]) 
        if 'scheduleron' in querycomponents:
            scheduleron = int(querycomponents["scheduleron"][0]) 
            sp_start_hr = int(querycomponents["sp_start_hr"][0]) 
            sp_start_min = int(querycomponents["sp_start_min"][0])
            sp_start_ampm = querycomponents["sp_start_ampm"][0]
            sp_stop_hr = int(querycomponents["sp_stop_hr"][0]) 
            sp_stop_min = int(querycomponents["sp_stop_min"][0]) 
            sp_stop_ampm = querycomponents["sp_stop_ampm"][0] 
        if save_cron(
            onbootwebserver=onbootwebserver,
            scheduleron=scheduleron,
            sp_start_hr=sp_start_hr + 12 if sp_start_ampm == 'PM' else sp_start_hr,
            sp_start_min=sp_start_min,
            sp_stop_hr=sp_stop_hr + 12 if sp_stop_ampm == 'PM' else sp_stop_hr,
            sp_stop_min=sp_stop_min,
            ):
            messages.append({
                'status': 'message',
                'message': 'Schedule Updated',
                })
    else:
        set_cronfile_for_read()


    min_hours = []
    with open(CRONFILE,'r') as file:
        # crondata = file.read()
                # Read all lines in the file one by one
        for line in file:
            # For each line, check if line contains the string
            if 'service-manager.sh' in line:
                if '@reboot' in line:
                    onbootwebserver = True
                else:
                    scheduleron = True
                    min_hours.extend(re.findall('^([0-9]{1,2}) ([0-9]{1,2}) .*', line)[0])

        if min_hours:
            sp_start_hr = int(min_hours[1])
            sp_start_min = int(min_hours[0])
            sp_stop_hr = int(min_hours[3])
            sp_stop_min = int(min_hours[2])
            if int(sp_start_hr) > 12:
                sp_start_ampm='PM'
                sp_start_hr-=12
            if int(sp_stop_hr) > 12:
                sp_stop_ampm='PM'
                sp_stop_hr-=12

    htmllist = Template(filename='html/_cron_editor.html')
    html = htmllist.render(
        # configContent=configContent,
        messages=messages,
        onbootwebserver=onbootwebserver,
        scheduleron=scheduleron,
        sp_start_hr=sp_start_hr,
        sp_start_min=sp_start_min,
        sp_stop_hr=sp_stop_hr,
        sp_stop_min=sp_stop_min,
        sp_start_ampm=sp_start_ampm,
        sp_stop_ampm=sp_stop_ampm,
        )
    return html

def get_media_path(subpath=''):
    # cap_time = datetime.datetime.strptime(date, DATE_FORMAT)
    # media_path = PATH_TO_IMAGES + '/' + cap_time.strftime("%Y/%m/%d") + subpath
    media_path = PATH_TO_IMAGES + subpath
    media_base_path = os.path.dirname(media_path)
    os.makedirs(media_base_path, exist_ok=True)
    # ls -tp media/images/2021/03/05/debug | grep -v '/$' | tail -n +51 | xargs -d '\n' rm -f --
    # stream = os.popen(f"ls -1tr {media_path} | head -n -10")
    # output = stream.read()
    return media_path

def render_html_speed_debugger(querycomponents):
    media_path = get_media_path(subpath='/debug')

    #--- keep only 50 records
    keepOnly = 50
    os.popen(f"cd {media_path} && ls -tp $PWD | grep -v '/$' | tail -n +{keepOnly*2 + 1} | xargs rm -f" )
    jpg_files = [f for f in os.listdir(media_path) if f.endswith('.jpg')]
    jpg_files.sort(reverse=True)
    jpg_files=jpg_files[:keepOnly]

    #--- get two ids differentiate standard and debug mode
    pid = is_daemon_active('speed')
    stream = os.popen("ps aux | grep 'speed-tracker.py.*debug' | grep -v grep | awk '{print $2}'")
    pid_debug = stream.read()
    if pid_debug == "": pid_debug = 0


    htmllist = Template(filename='html/_speed_debugger.html')
    html = htmllist.render(
        # configContent=configContent,
        jpg_files=jpg_files,
        media_path=media_path,
        pid=pid,
        pid_debug=int(pid_debug),
        )
    return html

def render_html_debugger_get(querycomponents, self):

    if 'img_lookup' in querycomponents:
        img_lookup = querycomponents["img_lookup"][0]
        if img_lookup == 'enable-debugger':
            restart_services('debugger-speedcam')
            return "debugger on"
        elif img_lookup == 'stop-speedcam':
            restart_services('stop-speedcam')
            return "Speed Cam Stoped"
        elif img_lookup == 'restart-speedcam':
            restart_services('restart-speedcam')
            return "Speed Cam Restarted"

    media_path = get_media_path(subpath=f'/debug/{img_lookup}.jpg.log')
        
    with open(media_path) as f:
        debugged = f.read()
    self.wfile.write(bytes(debugged, "utf-8"))
    return True;


def stream_log(self, log=None):
    if log == 'web':
        cmd = f"tail -f {LOG_FILE_WEB}"
    elif log == 'top':
        cmd = "top -b -1 -n 1"
        # cmd = f"top -b -1 -n 1 -u {THEUSER}"
    else:
        cmd = f"tail -f {LOG_FILE}"

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
        encoding='utf-8',
        errors='replace'
    )
    self.wfile.write(bytes('', "utf-8"))

    while True:
        realtime_output = process.stdout.readline()

        if realtime_output == '' and process.poll() is not None:
            break

        if realtime_output:
                try:
                    self.wfile.write(bytes(realtime_output.strip() + "\n", "utf-8"))
                except:
                    # if CONSOLE_DEBUGGER >= 4: print("[NOTICE] wfile Nothing to write")
                    None
    try:
        process.terminate()
    except:
        if CONSOLE_DEBUGGER >= 4: print("[NOTICE] process.terminate() was not needed")






def date_ensure_gap(datebegin=None, dateend=None, dayz=6):
    dayz_ahead = datetime.timedelta(dayz)
    b_date = datetime.datetime.strptime(datebegin, DATE_FORMAT)
    e_date = datetime.datetime.strptime(dateend, DATE_FORMAT)
    dayz_ago = datetime.datetime.now().strftime(DATE_FORMAT)
    t_date = datetime.datetime.strptime(dayz_ago, DATE_FORMAT)

    b_date_dayz = b_date + dayz_ahead

    if b_date_dayz > t_date:
        b_date = datetime.datetime.today() - dayz_ahead
        datebegin = b_date.strftime(DATE_FORMAT)

    delta = e_date - b_date

    if delta.days < dayz:
        start = b_date
        end = start + dayz_ahead
        dateend = end.strftime(DATE_FORMAT)
    return datebegin, dateend



def date_begin_less_end(datebegin=None, dateend=None):
    if datebegin > dateend:
        return dateend, datebegin
    else:
        return datebegin, dateend

#-----------------------------------------
# web header and handles
#-----------------------------------------
def send_img(self, filename_rel, mimetype):
    #Open the static file requested and send it
    f = open(filename_rel) 
    self.send_response(200)
    self.send_header('Content-type',mimetype)
    self.end_headers()
    self.wfile.write(f.read())
    f.close()

def content_type(filename_rel):
    ext2conttype = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif"
        }
    return ext2conttype[filename_rel[filename_rel.rfind(".")+1:].lower()]

class theWebServer(http.server.BaseHTTPRequestHandler):
    def do_AUTHHEAD(self):
        self.send_response(401)
        self.send_header(
            'WWW-Authenticate', 'Basic realm="Auth Realm"')
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_POST(self):
        #------------ userauth
        if WEB_REQURE_AUTH == True:
            key = self.server.get_auth_key()

            ''' Present frontpage with user authentication. '''
            if self.headers.get('Authorization') == 'Basic ' + str(key):
                getvars = self._parse_GET()

                response = {
                    'path': self.path,
                    'get_vars': str(getvars)
                }

            else:
                self.do_AUTHHEAD()

                response = {
                    'success': False,
                    'error': 'Invalid credentials'
                }

                self.wfile.write(bytes(json.dumps(response), 'utf-8'))
                return None

        # self.send_response(301)
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        length = int(self.headers['Content-Length'])
        fields = parse_qs(self.rfile.read(length).decode('utf-8'))
        html_body = None
        metarefresh = False
        
        if self.path.startswith('/config_editor'):
            html_body = render_html_config_editor(
                querycomponents=fields,
                )
        elif self.path.startswith('/cron_editor'):
            html_body = render_html_cron_editor(
                querycomponents=fields,
                )

        htmlwrapper = Template(filename='html/wrapper.html')
        html = htmlwrapper.render(
            metarefresh=metarefresh,
            body=html_body,
            )

        self.wfile.write(bytes(html, "utf-8"))

    def do_GET(self):

        #------------ userauth
        if WEB_REQURE_AUTH == True:
            key = self.server.get_auth_key()

            ''' Present frontpage with user authentication. '''
            if self.headers.get('Authorization') == 'Basic ' + str(key):
                getvars = self._parse_GET()

                response = {
                    'path': self.path,
                    'get_vars': str(getvars)
                }

            else:
                self.do_AUTHHEAD()

                response = {
                    'success': False,
                    'error': 'Invalid credentials'
                }

                self.wfile.write(bytes(json.dumps(response), 'utf-8'))
                return None


        # root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'html')
        filename =  self.path
        filename_rel = filename.strip('/')
        send_asset = False

        self.send_response(200)
        if filename[-4:] == '.html':
            self.send_header('Content-type', 'text/html')
            send_asset = True
        elif filename[-4:] == '.css':
            self.send_header('Content-type', 'text/css')
            send_asset = True
        elif filename[-5:] == '.json':
            self.send_header('Content-type', 'application/javascript')
            send_asset = True
        elif filename[-3:] == '.js':
            self.send_header('Content-type', 'application/javascript')
            send_asset = True
        elif filename[-4:] == '.ico':
            self.send_header('Content-type', 'image/x-icon')
        elif self.path.endswith(".jpg") or self.path.endswith(".gif") or self.path.endswith(".png"):
            contenttype = content_type(filename_rel)
            self.send_header('Content-type', contenttype)
            send_asset = True
        else:
            self.send_header('Content-type', 'text/html')
            send_asset = False

        self.end_headers()

        # ignore request to favicon
        if self.path.endswith('favicon.ico'):
            return
        elif send_asset or self.path.startswith('/html/assets/'):
            with open(filename_rel, 'rb') as fh:
                html = fh.read()
                self.wfile.write(html)
                return
        else:
            date_today = datetime.datetime.now().strftime("%Y-%m-%d")
            date_begin = date_today
            date_end = date_begin
            maxPerPage=1000
            page = 1
            direction = None
            speed_range = None
            cam = None
            log = None
            sort = 'DESC'
            metarefresh = False
            page_refresh=WEB_AUTO_REFRESH


            query_string = urlparse(self.path).query
            query_components = parse_qs(query_string)
            if 'date_begin' in query_components:
                date_begin = query_components["date_begin"][0]
            if 'date_end' in query_components:
                date_end = query_components["date_end"][0]
            if 'maxPerPage' in query_components:
                maxPerPage = query_components["maxPerPage"][0]
            if 'page' in query_components:
                page = query_components["page"][0]  
            if 'direction' in query_components:
                direction = query_components["direction"][0] 
            if 'speed_range' in query_components:
                speed_range = query_components["speed_range"][0] 
            if 'cam' in query_components:
                cam = query_components["cam"][0]  
            if 'log' in query_components:
                log = query_components["log"][0]  
            if 'sort' in query_components:
                sort = query_components["sort"][0]  

            # ensure begin date is less than end
            date_begin, date_end = date_begin_less_end(date_begin, date_end)

            html_body = ""
            if self.path.startswith('/list'):
                html_body = render_html_speed_list(
                    date_today=date_today,
                    date_begin=date_begin,
                    date_end=date_end,
                    query_string=query_string,
                    maxPerPage=maxPerPage,
                    page=page,
                    direction=direction,
                    speed_range=speed_range,
                    sort=sort,
                    )
                metarefresh = True
            elif self.path.startswith('/restart_service'):
                restart_services(cam)
                html = cam
            elif self.path.startswith('/status'):
                html_body = render_html_status(
                    date_today=date_today,
                    web_statuspage_limit=WEB_STATUSPAGE_LIMIT,
                    )
            elif self.path.startswith('/log-view'):
                html_body = render_html_log(
                    log=log,
                    )
                metarefresh = True
            elif self.path.startswith('/log-stream'):
                stream_log(
                    self,
                    log=log,
                    )
                return True
            elif self.path.startswith('/day-of-week'):

                if 'date_begin' not in query_components:
                    d = datetime.datetime.today() - datetime.timedelta(days=6)
                    date_begin = d.strftime(DATE_FORMAT)
                date_begin, date_end = date_ensure_gap(date_begin, date_end)

                html_body = render_html_day_of_week(
                    date_today=date_today,
                    date_begin=date_begin,
                    date_end=date_end,
                    query_string=query_string,
                    )
            elif self.path.startswith('/calibrate'):
                html_body = render_html_calibrate(
                    querycomponents=query_components,
                    )
            elif self.path.startswith('/config_editor'):
                html_body = render_html_config_editor(
                    querycomponents=query_components,
                    )
            elif self.path.startswith('/cron_editor'):
                html_body = render_html_cron_editor(
                    querycomponents=query_components,
                    )
            elif self.path.startswith('/speed_debugger'):
                html_body = render_html_speed_debugger(
                    querycomponents=query_components,
                    )
                metarefresh = True
                # page_refresh = 60
            elif self.path.startswith('/debugger_get'):
                html_body = render_html_debugger_get(
                    querycomponents=query_components,
                    self=self,
                    )
                return True
            else:
                # speed list count by hr
                html_body = render_html_overview(
                    date_today=date_today,
                    date_begin=date_begin,
                    date_end=date_end,
                    query_string=query_string,
                    )
                metarefresh = True

            htmlwrapper = Template(filename='html/wrapper.html')
            html = htmlwrapper.render(
                metarefresh=metarefresh,
                body=html_body,
                page_refresh=page_refresh,
                )

            self.wfile.write(bytes(html, "utf-8"))

    def _parse_GET(self):
        getvars = parse_qs(urlparse(self.path).query)

        return getvars


class CustomHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    key = ''

    def __init__(self, address, handlerClass=theWebServer):
        super().__init__(address, handlerClass)

    def set_auth(self, username, password):
        self.key = base64.b64encode(
            bytes('%s:%s' % (username, password), 'utf-8')).decode('ascii')

    def get_auth_key(self):
        return self.key


if __name__ == "__main__":        
    webServer = CustomHTTPServer(('', serverPort))
    if WEB_REQURE_AUTH == True: webServer.set_auth(WEB_USERNAME, WEB_PASSWORD)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")