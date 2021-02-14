#-----------------------------------------
# CONFIGS
#-----------------------------------------
# define some constants
L2R_DISTANCE = 120                      #<---- enter your distance-to-road value for cars going left to right here
R2L_DISTANCE = 120                      #<---- enter your distance-to-road value for cars going left to right here
SAVE_CSV = True                         #<---- record the results in .csv format in carspeed_(date).csv
MIN_SPEED_SAVE = 1                      #<---- enter the minimum speed for publishing to MQTT broker and saving to CSV
MAX_SPEED_SAVE = 90                     #<---- enter the maximum speed for publishing to MQTT broker and saving to CSV
SPEED_LIMIT = 40
FIELD_OF_VIEW = 0.665

# UPPER_LEFT_X = 365
# UPPER_LEFT_Y = 460
# LOWER_RIGHT_X = 865
# LOWER_RIGHT_Y = 600

THRESHOLD = 25
MIN_AREA = 175
BLURSIZE = (15,15)
RESOLUTION = (1280,720)
FOV = 62.2                              #<---- Pi Camera v2 is wider
FPS = 30
SHOW_BOUNDS = True
SHOW_IMAGE = True
CONSOLE_DEBUGGER = 3                   #<---- 3: info, 2: save & info, 1: notice & save & info

# the following enumerated values are used to make the program more readable
WAITING = 0
TRACKING = 1
SAVING = 2
UNKNOWN = 0
LEFT_TO_RIGHT = 'l2r'
RIGHT_TO_LEFT = 'r2l'
TOO_CLOSE = 0.4
MIN_SAVE_BUFFER = 2

WEB_AUTO_REFRESH=900
WEB_STATUSPAGE_LIMIT=100

PATH_TO_IMAGES = "media/images"
CSV_DIR_PATH = "data"
DB_DIR_PATH = "db"
DB_NAME = "speed-tracker.sqlite3"
DB_TABLE="speeds"
DB_PATH = DB_DIR_PATH + '/' +  DB_NAME
LOG_FILE='/var/log/speed/speed_tracker.log' #<---- ensure you have write permission to the parent directory
LOG_FILE_WEB='/var/log/speed/py-web-server.log'

