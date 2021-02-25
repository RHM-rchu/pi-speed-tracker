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
        SELECT mean_speed, hour from {DB_TABLE} WHERE date BETWEEN '{datebegin}' and '{dateend}'
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

def get_data_speed_list(
        date_begin, 
        date_end, 
        maxPerPage=1000, 
        page=1,
        direction=None,
        speed_range=None,
        speed_limit=SPEED_LIMIT,
        ):
    # global DB_TABLE
    datebegin = date_begin.replace("-","")
    dateend = date_end.replace("-","")
    page = int(page)
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

    result = db_select_record(f'''SELECT count(date) as total 
        from {DB_TABLE}
        WHERE date BETWEEN '{datebegin}' and '{dateend}'  {sql_direction}  {sql_speed_range};''')
    total = int(result[0]['total'])
    total_page = int(total/maxPerPage)  + (total % maxPerPage > 0)


    result = db_select_record(f'''SELECT id, date, hour, minute, round(mean_speed, 2) as mean_speed, 
        direction, image_path, round(sd, 0) as sd, counter
        from {DB_TABLE} 
        WHERE date BETWEEN '{datebegin}' and '{dateend}' {sql_direction} {sql_speed_range}
        LIMIT {limit}''')
 
    return result, total_page, total

def get_data_server_status(date_today, web_statuspage_limit=10):
    date_today = date_today.replace("-","")
    result = db_select_record(f'''SELECT count(date) as total 
        from {DB_TABLE}
        WHERE date BETWEEN '{date_today}' and '{date_today}';''')
    total = int(result[0]['total'])

    result = db_select_record(f'''select * from {DB_TABLE} order by id DESC limit {web_statuspage_limit}''')
 
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


def convert_list_to_int(thelist):
    numbers  = [ int(x) for x in thelist ]
    return numbers


def temp_change_primarykeys():
    local_table = "speedTracker"
    # milliseconds_since_epoch = datetime.datetime.now().timestamp() * 1000
    # print(f"---->{milliseconds_since_epoch}")
    result = db_select_record(f'''SELECT idx from {local_table}''')
    for speed in result:
        if '-' in speed['idx']:
            idx = re.sub(r'^([0-9]{8})-([0-9]{6})([0-9]{1})\.(.*)', r'\1-\2.\3\4', speed['idx'])
            datetimeobject = datetime.datetime.strptime(idx, '%Y%m%d-%H%M%S.%f')
            datetime_fmt = datetimeobject.strftime('%Y%m%d-%H%M%S.%f')
            epoch = datetime.datetime.strptime(datetime_fmt, '%Y%m%d-%H%M%S.%f').timestamp() * 1000
            sql = f'''UPDATE {local_table} SET idx ='{epoch}' WHERE idx='{speed['idx']}';'''
            db_update_record(sql)
        elif '-' not in speed['idx']:
            s = float(speed['idx']) / 1000.0
            dt = datetime.datetime.fromtimestamp(s).strftime('%Y-%m-%d %H:%M:%S.%f')

def convert_millisec_2_time(epoch, fmt='%A %d %B %Y %I:%M:%S%p'):
    epoch = int(float(epoch))
    s = float(epoch) / 1000.0
    date_full = datetime.datetime.fromtimestamp(s).strftime(fmt)
    return epoch, date_full

#-----------------------------------------
# HTML
#-----------------------------------------
def render_html_form(
        date_today, 
        date_begin, 
        date_end, 
        maxPerPage=0, 
        direction=None,
        speed_limit=None,
        speed_range=None,
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
        )
    return html

def render_html_speed_graph(
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
    graph_hrly = Template(filename='html/_graph_hrly.html')

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
        ):

    speed_lists, total_pages, total_count = get_data_speed_list(
        date_begin=date_begin, 
        date_end=date_end, 
        maxPerPage=maxPerPage, 
        page=page, 
        direction=direction,
        speed_range=speed_range,
        speed_limit=SPEED_LIMIT,
        )

    if direction == None: direction = True
    hours24 = [0 for x in range(1, 24)]
    speed_dict = []
    epoch = 0
    # dedupe = {}
    # epoch = 0
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

def render_html_log(log=None):
    htmllist = Template(filename='html/log-view.html')
    html = htmllist.render(
        WEB_REQURE_AUTH=WEB_REQURE_AUTH,
        WEB_USERNAME=WEB_USERNAME,
        WEB_PASSWORD=WEB_PASSWORD,
        log=log,
        )
    return html

def render_html_status(date_today, cam=None, web_statuspage_limit=None):
    latest_records, total = get_data_server_status(date_today, web_statuspage_limit)

    i=0
    for speed in latest_records:
        epoch, date_full = convert_millisec_2_time(speed['id'])
        latest_records[i]['date_full'] = date_full
        latest_records[i]['epoch'] = epoch
        latest_records[i]['speed'] = round(float(speed['mean_speed']), 0)
        latest_records[i]['sd'] = round(float(speed['sd']), 0)
        i+=1

    #--- turn cam on/off
    if cam == "start":
        os.system("./scripts/service-manager.sh -a speed -x start")
        time.sleep(1)
    elif cam == "stop":
        os.system("./scripts/service-manager.sh -a speed -x stop" )
        time.sleep(1)
    if cam == "restart-web":
        os.system("./scripts/service-manager.sh -a web -x restart" )

    sp_tracker_running = is_daemon_active('speed')

    htmllist = Template(filename='html/_status.html')
    html = htmllist.render(sp_tracker_running=sp_tracker_running,
        latest_records=latest_records,
        total=total,
        web_statuspage_limit=web_statuspage_limit,
        )
    return html

def stream_log(self, log=None):
    # self.send_response(200)
    # self.send_header('Content-type','text/html')
    # self.end_headers()
    if log == 'web':
        cmd = f"tail -f /var/log/speed/py-web-server.log"
    elif log == 'top':
        cmd = "top -b -1 -n 1 -u pi"
    else:
        cmd = f"tail -f /var/log/speed/speed_tracker.log"

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
                    # print("[NOTICE] wfile Nothing to write")
                    None
            # self.wfile.write(bytes(realtime_output.strip() + "\n", "utf-8"))
    try:
        process.terminate()
    except:
        print("[NOTICE] process.terminate() was not needed")



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

    def do_GET(self):

        #------------ userauth
        if WEB_REQURE_AUTH == True:
            key = self.server.get_auth_key()

            ''' Present frontpage with user authentication. '''
            if self.headers.get('Authorization') == 'Basic ' + str(key):
                # self.send_response(200)
                # self.send_header('Content-type', 'application/json')
                # self.end_headers()

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
            metarefresh = True


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
                    )
            elif self.path.startswith('/status'):
                html_body = render_html_status(
                    date_today=date_today,
                    cam=cam,
                    web_statuspage_limit=WEB_STATUSPAGE_LIMIT,
                    )
            elif self.path.startswith('/log-view'):
                html_body = render_html_log(
                    log=log,
                    )
                metarefresh = False
            elif self.path.startswith('/log-stream'):
                stream_log(
                    self,
                    log=log,
                    )
                return True
            else:
                # speed list count by hr
                html_body = render_html_speed_graph(
                    date_today=date_today,
                    date_begin=date_begin,
                    date_end=date_end,
                    query_string=query_string,
                    )

            htmlwrapper = Template(filename='html/wrapper.html')
            html = htmlwrapper.render(
                metarefresh=metarefresh,
                body=html_body,
                page_refresh=WEB_AUTO_REFRESH
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