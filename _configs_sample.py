#-----------------------------------------
# CONFIGS
#-----------------------------------------
# define some constants
L2R_DISTANCE = 120                      #<---- enter your distance to road in ft - bottom left corner from calibrator.py, step (8) of readme
R2L_DISTANCE = 120                      #<---- enter your distance to road in ft - bottom right corner from calibrator.py, step (8) of readme
SAVE_CSV = True                         #<---- record the results in .csv format in carspeed_(date).csv
MIN_SPEED_SAVE = 1                      #<---- enter the minimum speed for publishing to MQTT broker and saving to CSV
MAX_SPEED_SAVE = 90                     #<---- enter the maximum speed for publishing to MQTT broker and saving to CSV
SPEED_LIMIT = 40                        #<---- MPH speed limit
FIELD_OF_VIEW = 0.665

THRESHOLD = 25                          #<---- adjust for accuracy, higher the number the more picky
MIN_AREA = 175                          #<---- heightxwidth pixel count, ignore if below this count
BLURSIZE = (15,15)                      #<---- ignore unless you know what you are doing, this is fine
RESOLUTION = (1280,720)                 #<---- Camera resolution, this is fine
FOV = 62.2                              #<---- Pi Camera v2 is wider
FPS = 30
SHOW_BOUNDS = True
SHOW_IMAGE = True
CONSOLE_DEBUGGER = 3                   #<---- 3: info, 2: save & info, 1: notice & save & info

# the following enumerated values are used to make the program more readable, safe to ignore
WAITING = 0
TRACKING = 1
SAVING = 2
UNKNOWN = 0
LEFT_TO_RIGHT = 'Southbound'
RIGHT_TO_LEFT = 'Northbound'
TOO_CLOSE = 0.4
MIN_SAVE_BUFFER = 2

# web page configs
WEB_AUTO_REFRESH = 900                  #<---- auto update the webpages in sec
WEB_STATUSPAGE_LIMIT = 100              #<---- limits results per page on status page
WEB_USERNAME = "speed"
WEB_PASSWORD = "racer"

WEB_SPEED_DICT = [                      #<---- Speed names and ranges to plot on the graph 
    {
    "name": 'Snail under 29',
    "rgb": '75, 192, 192',
    "speed_low": 0,
    "speed_high": 29,
    },
    {
    "name": 'Safe Drivers',
    "rgb": '54, 162, 235',
    "speed_low": 30,
    "speed_high": 40,
    },
    {
    "name": '45-50',
    "rgb": '255, 206, 86',
    "speed_low": 41,
    "speed_high": 50,
    },
    {
    "name": '50-54',
    "rgb": '255, 99, 132',
    "speed_low": 51,
    "speed_high": 60,
    },
    {
    "name": 'speed daemon',
    "rgb": '153, 102, 255',
    "speed_low": 61,
    "speed_high": 155,
    },
]

# Path and directories, safe to ignore, unless you really have to change
PATH_TO_IMAGES = "media/images"
CSV_DIR_PATH = "data"
DB_DIR_PATH = "db"
DB_NAME = "speed-tracker.sqlite3"
DB_TABLE="speeds"
DB_PATH = DB_DIR_PATH + '/' +  DB_NAME
LOG_FILE='/var/log/speed/speed_tracker.log'
LOG_FILE_WEB='/var/log/speed/py-web-server.log'
