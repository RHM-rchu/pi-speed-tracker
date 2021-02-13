from http.server import BaseHTTPRequestHandler, HTTPServer
import datetime, time, os, sys
import re
# import http.server
import socketserver
from urllib.parse import urlparse
from urllib.parse import parse_qs
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

def print2log(message=''):
    global LOG_FILE_WEB
    print(message)
    f = open(LOG_FILE_WEB, 'a')
    f.write(message+"\n")
    f.close

#-----------------------------------------
# DB
#-----------------------------------------
def get_data_speed_matrix(date_begin, date_end):
    global DB_TABLE
    # ensure 24 slots for 24hrs
    lists_below_10 = [0 for x in range(1, 24)]
    lists_around_10 = [0 for x in range(1, 24)]
    lists_above_10 = [0 for x in range(1, 24)]
    lists_above_20 = [0 for x in range(1, 24)]
    lists_above_30 = [0 for x in range(1, 24)]
    # set speeds based on speed limit
    below_10 = int(SPEED_LIMIT - 10)
    above_10 = int(SPEED_LIMIT + 10)
    above_20 = int(SPEED_LIMIT + 20)
    above_30 = int(SPEED_LIMIT + 30)

    datebegin = date_begin.replace("-","")
    dateend = date_end.replace("-","")

    result = db_select_record(f'''SELECT mean_speed, hour from {DB_TABLE} WHERE date BETWEEN '{datebegin}' and '{dateend}';''')

    if result:
        for row in result:
            hr = int(row['hour'])
            sp = int(f"{float(row['mean_speed']):.0f}")
            if sp < below_10:
                lists_below_10[hr] += 1
            elif sp > above_30:
                lists_above_30[hr] += 1
            elif sp > above_20:
                lists_above_20[hr] += 1
            elif sp > above_10:
                lists_above_10[hr] += 1
            else:
                lists_around_10[hr] += 1

    return (lists_below_10, lists_around_10, lists_above_10, lists_above_20, lists_above_30)

def get_data_speed_list(
        date_begin, 
        date_end, 
        maxPerPage=1000, 
        page=1,
        direction=None,
        speed_range=None,
        speed_limit=SPEED_LIMIT,
        ):
    global DB_TABLE
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
        speed_ranges = {
            '<10': " and mean_speed < %d" % (speed_limit - 10),
            '+/-10': " and (mean_speed > %s and mean_speed < %s)" % ((speed_limit - 10), (speed_limit + 10)),
            '+10': " and mean_speed > %d" % (speed_limit + 10),
            '+20': " and mean_speed > %d" % (speed_limit + 20),
            '>30': " and mean_speed > %d" % (speed_limit + 30),
            }
        # if speed_ranges[speed_range]:
        if speed_range in speed_ranges:
            sql_speed_range = speed_ranges[speed_range]

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
    global DB_TABLE

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
    command = "systemctl is-active " + daemon + " > tmp"
    os.system(command)
    with open('tmp') as tmp:
        tmp = tmp.read()
        if "active" == re.sub(r'\W+', '', tmp):
            os.remove('tmp')
            return 1
    os.remove('tmp')
    return 0


def convert_list_to_int(thelist):
    numbers  = [ int(x) for x in thelist ]
    return numbers


def temp_change_primarykeys():
    global DB_TABLE
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
            # print(f"{sql}")
        elif '-' not in speed['idx']:
            s = float(speed['idx']) / 1000.0
            dt = datetime.datetime.fromtimestamp(s).strftime('%Y-%m-%d %H:%M:%S.%f')
            # print(dt)

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
    htmllist = Template(filename='html/_form.txt')
    html = htmllist.render(
        date_begin=date_begin,
        date_end=date_end,
        date_today=date_today,
        maxPerPage=maxPerPage,
        direction=direction,
        speed_limit=speed_limit,
        speed_range=speed_range,
        )
    return html

def render_html_speed_graph(
        date_today,
        date_begin,
        date_end,
        query_string,
        ):
    
    sp_below_10, sp_around_10, sp_above_10, sp_above_20, sp_above_30 = get_data_speed_matrix(date_begin, date_end)
    sp_below_10 = [str(element) for element in sp_below_10]
    sp_around_10 = [str(element) for element in sp_around_10]
    sp_above_10 = [str(element) for element in sp_above_10]
    sp_above_20 = [str(element) for element in sp_above_20]
    sp_above_30 = [str(element) for element in sp_above_30]
    # total for each category
    ttl_sp_below_10 = sum(convert_list_to_int(sp_below_10))
    ttl_sp_around_10 = sum(convert_list_to_int(sp_around_10))
    ttl_sp_above_10 = sum(convert_list_to_int(sp_above_10))
    ttl_sp_above_20 = sum(convert_list_to_int(sp_above_20))
    ttl_sp_above_30 = sum(convert_list_to_int(sp_above_30))
    ttl_sp = sum([ ttl_sp_below_10, ttl_sp_around_10, ttl_sp_above_10, ttl_sp_above_20, ttl_sp_above_30 ])
    # percentage of total
    if ttl_sp > 1:
        speed_lists = {
            "Below 10":{"count":ttl_sp_below_10, "percent":"{0}%".format(round(ttl_sp_below_10/ttl_sp*100, 2))}, 
            "Within 10":{"count":ttl_sp_around_10, "percent":"{0}%".format(round(ttl_sp_around_10/ttl_sp*100, 2))}, 
            "Above 10":{"count":ttl_sp_above_10, "percent":"{0}%".format(round(ttl_sp_above_10/ttl_sp*100, 2))}, 
            "Above 20":{"count":ttl_sp_above_20, "percent":"{0}%".format(round(ttl_sp_above_20/ttl_sp*100, 2))}, 
            "Above 30":{"count":ttl_sp_above_30, "percent":"{0}%".format(round(ttl_sp_above_30/ttl_sp*100, 2))}
            }
    else:
          speed_lists = {
            "Below 10":{"count":0, "percent":0}, 
            "Within 10":{"count":0, "percent":0}, 
            "Above 10":{"count":0, "percent":0}, 
            "Above 20":{"count":0, "percent":0}, 
            "Above 30":{"count":0, "percent":0}
            }


    form=render_html_form(
        date_today=date_today, 
        date_begin=date_begin,
        date_end=date_end,
        speed_limit=SPEED_LIMIT,
        );
    graph_hrly = Template(filename='html/_graph_hrly.txt')
    html = graph_hrly.render(
        sp_below_10=sp_below_10, 
        sp_around_10=sp_around_10, 
        sp_above_10=sp_above_10, 
        sp_above_20=sp_above_20, 
        sp_above_30=sp_above_30, 
        percent_sp_list=speed_lists,
        total_sp=ttl_sp,
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
            'direction': 'l2r',
            })
        speed_dict.append({
            'mean_speed': 0,
            'date_full': date_full,
            'epoch': 0,
            'direction': 'r2l',
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
    htmllist = Template(filename='html/_list.txt')
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
        os.system("sudo systemctl start speed-tracker.service")
        time.sleep(1)
    elif cam == "stop":
        os.system("sudo systemctl stop speed-tracker.service" )
        time.sleep(1)
    if cam == "restart-web":
        os.system("sudo systemctl restart py-web-tracker.service" )
        time.sleep(4)

    sp_tracker_running = is_daemon_active('speed-tracker')

    htmllist = Template(filename='html/_status.txt')
    html = htmllist.render(sp_tracker_running=sp_tracker_running,
        latest_records=latest_records,
        total=total,
        web_statuspage_limit=web_statuspage_limit,
        )
    return html

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

class theWebServer(BaseHTTPRequestHandler):
    def do_GET(self):
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
            else:
                # speed list count by hr
                html_body = render_html_speed_graph(
                    date_today=date_today,
                    date_begin=date_begin,
                    date_end=date_end,
                    query_string=query_string,
                    )

            htmlwrapper = Template(filename='html/wrapper.txt')
            html = htmlwrapper.render(
                body=html_body,
                page_refresh=WEB_AUTO_REFRESH
                )

            self.wfile.write(bytes(html, "utf-8"))



if __name__ == "__main__":        
    webServer = HTTPServer(("", serverPort), theWebServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")