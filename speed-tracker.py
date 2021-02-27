#!/usr/bin/env ptython3

# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
import time, datetime
import math
import cv2
import numpy as np
import argparse
import os, sys
import sqlite3
#-----------------------------------------
# shared configs and functions
#-----------------------------------------
from _configs import *
from _sqlite3_functions import *

logfile_base = os.path.dirname(os.path.abspath(LOG_FILE))
os.makedirs(logfile_base, exist_ok=True)
os.makedirs(CSV_DIR_PATH, exist_ok=True)
os.makedirs(PATH_TO_IMAGES, exist_ok=True)
logfile = open(LOG_FILE,'w', 1)
sys.stdout = logfile
sys.stdin = logfile
sys.stderr = logfile

if os.path.isfile("_configs_coords.py"):
    from _configs_coords import *
else:
    # doesn't exist
    print('[ERROR] couldn\'t open configs_coords.py, To create the region to monitor run: ptython calibator.py')
    sys.exit(1)

cvGreen = (0, 255, 0)
cvBlack = (0, 0, 0)
cvRed = (0, 0, 255)


# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-ulx", "--upper_left_x", required=False,
    help="upper left x coord")
ap.add_argument("-uly", "--upper_left_y", required=False,
    help="upper left y coord")
ap.add_argument("-lrx", "--lower_right_x", required=False,
    help="lower right x coord")
ap.add_argument("-lry", "--lower_right_y", required=False,
    help="lower right y coord")
ap.add_argument("-s", "--show_image", required=True, default="off",
    help="Show Video Player")
args = vars(ap.parse_args())

upper_left_x = int(args["upper_left_x"]) if args["upper_left_x"] else UPPER_LEFT_X
upper_left_y = int(args["upper_left_y"]) if args["upper_left_y"] else UPPER_LEFT_Y
lower_right_x = int(args["lower_right_x"]) if args["lower_right_x"] else LOWER_RIGHT_X
lower_right_y = int(args["lower_right_y"]) if args["lower_right_y"] else LOWER_RIGHT_Y
SHOW_IMAGE = args["show_image"] if 'show_image' in args else 'off'

def offset_capture_by_direction():
    px_right = lower_right_x + CROP_OffSET
    if px_right < RESOLUTION[0]:
        px_r_offset = px_right
        px_l_offset = upper_left_x + CROP_OffSET
    else:
        px_r_offset = RESOLUTION[0]
        r_offset_diff = px_right - RESOLUTION[0]
        px_l_offset = upper_left_x + r_offset_diff
    l2r_offsets = (px_l_offset,px_r_offset)


    px_left = upper_left_x - CROP_OffSET
    if px_left >= 1:
        px_l_offset = px_left
        px_r_offset = lower_right_x - CROP_OffSET
    else:
        px_l_offset = 1
        px_r_offset = lower_right_x - upper_left_x
    r2l_offsets = (px_l_offset,px_r_offset)

    return r2l_offsets, l2r_offsets

if 'CROP_OffSET' in globals():
    CAPTURE_OFFSETS = offset_capture_by_direction()

# calculate the the width of the image at the distance specified
#frame_width_ft = 2*(math.tan(math.radians(FOV*0.5))*DISTANCE)
l2r_frame_width_ft = 2*(math.tan(math.radians(FOV*FIELD_OF_VIEW))*L2R_DISTANCE)
r2l_frame_width_ft = 2*(math.tan(math.radians(FOV*FIELD_OF_VIEW))*R2L_DISTANCE)
l2r_ftperpixel = l2r_frame_width_ft / float(RESOLUTION[0])
r2l_ftperpixel = r2l_frame_width_ft / float(RESOLUTION[0])

#-----------------------------------------



#-----------------------------------------
#
#-----------------------------------------
"""
calculate speed from pixels and time
"""
def get_speed(pixels, ftperpixel, secs):
    if secs > 0.0:
        return ((pixels * ftperpixel)/ secs) * 0.681818    # Magic number to convert fps to mph
    else:
        return 0.0
 
def secs_diff(endTime, begTime):
    diff = (endTime - begTime).total_seconds()
    return diff

def record_speed(csvfileout, res):
    # global csvfileout
    f = open(csvfileout, 'a')
    f.write(res+"\n")
    f.close

# mapping function equivalent to C map function from Arduino
def my_map(x, in_min, in_max, out_min, out_max):
    return int((x-in_min) * (out_max-out_min) / (in_max-in_min) + out_min)

def measure_light(hsvImg):
    #Determine luminance level of monitored area 
    #returns the median from the histogram which contains 0 - 255 levels
    hist = cv2.calcHist([hsvImg], [2], None, [256],[0,255])
    windowsize = (hsvImg.size)/3   #There are 3 pixels per HSV value 
    count = 0
    sum = 0
    for value in hist:
        sum = sum + value
        count +=1    
        if (sum > windowsize/2):   #test for median
            break
    return count   

def calibration_image(image):
    hotzone = image[upper_left_y:lower_right_y,upper_left_x:lower_right_x]
    imageheight, imagewidth, channel = hotzone.shape
    cntr_x = 10
    cntr_y = int(imageheight * 0.2) 
    lists = [
        (imageheight,imagewidth,"Height Width"),
        (upper_left_x,upper_left_y, " x,y UPPER_LEFT"),
        (lower_right_x,lower_right_y," x,y LOWER_RIGHT")
    ]
    for lines in lists:
        cntr_y += 40
        text = "%.0f,%.0f %s" %  lines
        cv2.putText(image, text, (cntr_x , cntr_y), cv2.FONT_HERSHEY_SIMPLEX, .70, cvBlack, 4)
        cv2.putText(image, text, (cntr_x , cntr_y), cv2.FONT_HERSHEY_SIMPLEX, .70, cvGreen, 2)
    # Draw threshold box with point
    image = cv2.rectangle(image, (upper_left_x, upper_left_y)
        , (lower_right_x,lower_right_y), cvRed, 2)
    image = cv2.circle(image, (upper_left_x, upper_left_y), 8, cvGreen, -3)
    image = cv2.circle(image, (lower_right_x,lower_right_y), 8, cvGreen, -3)

    calibration_image_path = ("%s/calibrate.jpg" % PATH_TO_IMAGES)
    if CONSOLE_DEBUGGER >= 3: print("[INFO] Creating calibration img: %s" % calibration_image_path)
    cv2.imwrite( calibration_image_path, image )
    return image
"""
Reciprocal function curve to give a smaller number for bright light and a bigger number for low light
"""
def get_save_buffer(light):
    save_buffer = int((100/(light - 0.5)) + MIN_SAVE_BUFFER)    
    if CONSOLE_DEBUGGER >= 3: print("[NOTICE] Save Buffer:  %s" %  save_buffer)
    return save_buffer

def get_min_area(light):
    if (light > 10):
        light = 10;
    area =int((1000 * math.sqrt(light - 1)) + 100)
    if CONSOLE_DEBUGGER >= 3: print("[INFO] Main Area:  %s" %  area)
    return area

def get_threshold(light):
   #Threshold for dark needs to be high so only pick up lights on vehicle
    if (light <= 1):
        threshold = 130
    elif(light <= 2):
        threshold = 100
    elif(light <= 3):
        threshold = 60
    else:
        threshold = THRESHOLD
    if CONSOLE_DEBUGGER >= 3: print("[INFO] Threahold: %s" %  threshold)
    return threshold

def store_image(cap_time, image, mean_speed, direction):
    if 'CAPTURE_OFFSETS' in globals():
        if direction == LEFT_TO_RIGHT:
            cap_begin_w = CAPTURE_OFFSETS[1][0]
            cap_end_w = CAPTURE_OFFSETS[1][1]
        elif direction == RIGHT_TO_LEFT:
            cap_begin_w = CAPTURE_OFFSETS[0][0]
            cap_end_w = CAPTURE_OFFSETS[0][1]
    else:
        cap_begin_w = upper_left_x
        cap_end_w = lower_right_x

    s_image = image[upper_left_y:lower_right_y,cap_begin_w:cap_end_w]

    w, h, _ = s_image.shape
    cntr_x = w
    cntr_y = int(h * 0.05)
    spd_fnt_sz = 1
    txt_date = cap_time.strftime("%A %d %B %Y %I:%M:%S%p")
    txt_speed = "%.0f mph" % mean_speed
    media_path = PATH_TO_IMAGES + '/' + cap_time.strftime("%Y/%m/%d")
    imageFilename = cap_time.strftime("%Y%m%d_%H%M%S") + ".jpg"
    imageFilename_full = media_path + "/" + "car_at_" + cap_time.strftime("%Y%m%d_%H%M%S") + ".jpg"
    os.makedirs(media_path, exist_ok=True)

    if CONSOLE_DEBUGGER >= 2: print("[SAVING] Image:  %s" % imageFilename_full)

    cv2.putText(s_image, txt_date,
        (10, s_image.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 1)
    # size, base = cv2.getTextSize(txt_speed, cv2.FONT_HERSHEY_SIMPLEX, spd_fnt_sz, 2)
    # then center it horizontally on the image
    cv2.putText(s_image, txt_speed,
        (cntr_x , cntr_y), cv2.FONT_HERSHEY_SIMPLEX, spd_fnt_sz, (0, 0, 0), 3)
    cv2.putText(s_image, txt_speed,
        (cntr_x , cntr_y), cv2.FONT_HERSHEY_SIMPLEX, spd_fnt_sz, (0, 255, 0), 2)
    # Save the image
    cv2.imwrite(imageFilename_full, s_image)
    return imageFilename_full

def store_traffic_data(cap_time, mean_speed, direction, counter, standard_deviation, imageFilename_full=''):
    if CONSOLE_DEBUGGER >= 2: print("[SAVING] Record: %.0fmph with standard_deviation of %.2f with %s data points" % 
        (mean_speed, standard_deviation, counter))
    csvString =  "%s, %s, %s, %s, %s, %s" % \
        (cap_time.strftime("%Y-%m-%d %H:%M:%S"), mean_speed, direction, counter, standard_deviation, imageFilename_full)
    record_speed(csvfileout, csvString)

    # micsec=int(cap_time.strftime("%f"))/100000
    ##############
    datetime_fmt = cap_time.strftime('%Y%m%d-%H%M%S.%f')
    epoch = datetime.datetime.strptime(datetime_fmt, '%Y%m%d-%H%M%S.%f').timestamp() * 1000
    #############
    the_id = ("%s" % epoch)
    date = ("%s" % (cap_time.strftime("%Y%m%d")))
    hour = ("%s" % cap_time.strftime("%H"))
    minute = ("%s" % cap_time.strftime("%M"))
    speed_data = (the_id,
                 date, 
                 hour, 
                 minute,
                 mean_speed,
                 'mph', 
                 direction, 
                 counter,
                 standard_deviation,
                 imageFilename_full,
                 'car_type',
                 'car_color',
                 'cam_location')

    db_save_record(speed_data)

def img_float32(img):
  return img.copy() if img.dtype != 'uint8' else (img/255.).astype('float32')

def over(fgimg, bgimg):
  fgimg, bgimg = img_float32(fgimg),img_float32(bgimg)
  (fb,fg,fr,fa),(bb,bg,br,ba) = cv2.split(fgimg),cv2.split(bgimg)
  color_fg, color_bg = cv2.merge((fb,fg,fr)), cv2.merge((bb,bg,br))
  alpha_fg, alpha_bg = np.expand_dims(fa, axis=-1), np.expand_dims(ba, axis=-1)
  
  color_fg[fa==0]=[0,0,0]
  color_bg[ba==0]=[0,0,0]
  
  a = fa + ba * (1-fa)
  a[a==0]=np.NaN
  color_over = (color_fg * alpha_fg + color_bg * alpha_bg * (1-alpha_fg)) / np.expand_dims(a, axis=-1)
  color_over = np.clip(color_over,0,1)
  color_over[a==0] = [0,0,0]
  
  result_float32 = np.append(color_over, np.expand_dims(a, axis=-1), axis = -1)
  return (result_float32*255).astype('uint8')

def overlay_transparent(bgimg, fgimg, xmin = 0, ymin = 0,trans_percent = 1):
    if bgimg.shape[2] == 3:
        bgimg = cv2.cvtColor(bgimg, cv2.COLOR_BGR2BGRA)
    if 2 not in fgimg.shape:
        fgimg = cv2.cvtColor(fgimg, cv2.COLOR_GRAY2BGRA)
    elif fgimg.shape[2] == 3:
        fgimg = cv2.cvtColor(fgimg, cv2.COLOR_BGR2BGRA)
    #we assume all the input image has 4 channels
    assert(bgimg.shape[-1] == 4 and fgimg.shape[-1] == 4)
    fgimg = fgimg.copy()
    roi = bgimg[ymin:ymin+fgimg.shape[0], xmin:xmin+fgimg.shape[1]].copy()
    b,g,r,a = cv2.split(fgimg)
    fgimg = cv2.merge((b,g,r,(a*trans_percent).astype(fgimg.dtype)))
    roi_over = over(fgimg,roi)
    result = bgimg.copy()
    result[ymin:ymin+fgimg.shape[0], xmin:xmin+fgimg.shape[1]] = roi_over
    return result

# def print2log(message=''):
#     global LOG_FILE
#     print(message)
#     f = open(LOG_FILE, 'a')
#     f.write(message+"\n")
#     f.close



if SAVE_CSV:
    csvfileout = CSV_DIR_PATH + "/carspeed_{}.csv".format(datetime.datetime.now().strftime("%Y%m%d_%H%M"))
    record_speed(csvfileout, 'DateTime,Speed,Direction, Counter,SD, Image')
else:
    csvfileout = ''
#-----------------------------------------
# Main
#-----------------------------------------
def main():        
    #Initialisation
    state = WAITING
    direction = UNKNOWN
    initial_x = 0
    last_x = 0
    cap_time = datetime.datetime.now()   
    #pixel width at left and right of window to detect end of tracking
    savebuffer = MIN_SAVE_BUFFER  
    base_image = None
    abs_chg = 0
    mph = 0
    secs = 0.0
    ix,iy = -1,-1
    fx,fy = -1,-1
    drawing = False
    setup_complete = False
    tracking = False
    text_on_image = 'No cars'
    broker_address = 'emonpi'
    save_image = False
    t1 = 0.0  #timer
    t2 = 0.0  #timer
    lightlevel = 0
    adjusted_threshold = THRESHOLD
    adjusted_min_area = MIN_AREA
    first_pass = True
         
    monitored_width = lower_right_x - upper_left_x
    monitored_height = lower_right_y - upper_left_y

    if CONSOLE_DEBUGGER >= 2: print(f"[LOADING] Tracking area:")
    if CONSOLE_DEBUGGER >= 2: print(f"[LOADING]   upper_left_x {upper_left_x}")
    if CONSOLE_DEBUGGER >= 2: print(f"[LOADING]   upper_left_y {upper_left_y}")
    if CONSOLE_DEBUGGER >= 2: print(f"[LOADING]   lower_right_x {lower_right_x}")
    if CONSOLE_DEBUGGER >= 2: print(f"[LOADING]   lower_right_y {lower_right_y}")
    if CONSOLE_DEBUGGER >= 2: print(f"[LOADING]   monitored_width {monitored_width}")
    if CONSOLE_DEBUGGER >= 2: print(f"[LOADING]   monitored_height {monitored_height}")
    if CONSOLE_DEBUGGER >= 2: print(f"[LOADING]   monitored_area {monitored_width * monitored_height}")
    if CONSOLE_DEBUGGER >= 2: print("[LOADING]   %s Image width in feet %.0f at %0f from camera" % (LEFT_TO_RIGHT, l2r_frame_width_ft, L2R_DISTANCE))
    if CONSOLE_DEBUGGER >= 2: print("[LOADING]   %s Image width in feet %3.0f at %3.0f}from camera" % (RIGHT_TO_LEFT, r2l_frame_width_ft, R2L_DISTANCE))

    # initialise the camera. 
    # Adjust vflip and hflip to reflect your camera's orientation
    camera = PiCamera()
    camera.resolution = RESOLUTION
    camera.framerate = FPS
    camera.vflip = False
    camera.hflip = False

    rawCapture = PiRGBArray(camera, size=camera.resolution)
    # allow the camera to warm up
    time.sleep(1)

    # capture frames from the camera (using capture_continuous.
    #   This keeps the picamera in capture mode - it doesn't need
    #   to prep for each frame's capture.
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        # grab the raw NumPy array representing the image 
        image = frame.array

    # load_video="../test/media/vid/Sequence1.mp4"
    # cap = cv2.VideoCapture(load_video)
    # while(cap.isOpened()):
    #     _, image = cap.read()

        # crop area defined by [y1:y2,x1:x2]
        gray = image[upper_left_y:lower_right_y,upper_left_x:lower_right_x]
        # capture colour for later when measuring light levels
        hsv = cv2.cvtColor(gray, cv2.COLOR_BGR2HSV)
        # convert the frame to grayscale, and blur it
        gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, BLURSIZE, 0)
     
        # if the base image has not been defined, initialize it
        if base_image is None:
            base_image = gray.copy().astype("float")
            rawCapture.truncate(0)
            if SHOW_IMAGE == 'on': cv2.imshow("Speed Camera", image)
      

        if lightlevel == 0:   #First pass through only
            #Set threshold and min area and save_buffer based on light readings
            lightlevel = my_map(measure_light(hsv),0,256,1,10)

            if CONSOLE_DEBUGGER >= 3: print("[INFO] Light Level: %s" %  lightlevel)

            adjusted_min_area = get_min_area(lightlevel)
            adjusted_threshold = get_threshold(lightlevel)
            adjusted_save_buffer = get_save_buffer(lightlevel)
            last_lightlevel = lightlevel

        # compute the absolute difference between the current image and
        # base image and then turn eveything lighter gray than THRESHOLD into
        # white
        frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(base_image))
        thresh = cv2.threshold(frameDelta, adjusted_threshold, 255, cv2.THRESH_BINARY)[1]
        
        # dilate the thresholded image to fill in any holes, then find contours
        # on thresholded image
        thresh = cv2.dilate(thresh, None, iterations=2)
        (cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)

        # look for motion 
        motion_found = False
        biggest_area = 0
        # examine the contours, looking for the largest one
        for c in cnts:
            (x1, y1, w1, h1) = cv2.boundingRect(c)
            # get an approximate area of the contour
            found_area = w1*h1 
            # find the largest bounding rectangle
            if (found_area > adjusted_min_area) and (found_area > biggest_area):  
                biggest_area = found_area
                motion_found = True
                x = x1
                y = y1
                h = h1
                w = w1
                #record the timestamp at the point in code where motion found
                timestamp = datetime.datetime.now()

        if motion_found:
            if state == WAITING:
                # intialize tracking
                state = TRACKING
                initial_x = x
                last_x = x
                #if initial capture straddles start line then the
                # front of vehicle is at position w when clock started
                initial_w = w
                initial_time = timestamp
                last_mph = 0
            
                #Initialise array for storing speeds
                speeds = np.array([])
                sd=0  #Initialise standard deviation
                
                text_on_image = 'Tracking'
                counter = 0   # use to test later if saving with too few data points    
                car_gap = secs_diff(initial_time, cap_time) 

                if CONSOLE_DEBUGGER >= 4: print(f"[NOTICE] ~~~ Started: {timestamp} ~~~")
                if CONSOLE_DEBUGGER >= 1: print("[TRACKING] x-chg    Secs   MPH  x-pos width  BA    Direction  Count time")

                if (car_gap<TOO_CLOSE):   
                    state = WAITING
                    if CONSOLE_DEBUGGER >= 4: print("[NOTICE] Too Close")
            else: # compute the lapsed time
                secs = secs_diff(timestamp,initial_time)
                if secs >= 3: # Object taking too long to move across
                    state = WAITING
                    direction = UNKNOWN
                    text_on_image = 'No Car Detected'
                    motion_found = False
                    biggest_area = 0
                    rawCapture.truncate(0)
                    base_image = None
                    if CONSOLE_DEBUGGER >= 4: print("[NOTICE] ~~~ Resetting ~~~")
                    continue             

                if state == TRACKING:       
                    if x >= last_x:
                        direction = LEFT_TO_RIGHT
                        abs_chg = (x + w) - (initial_x + initial_w)
                        mph = get_speed(abs_chg,l2r_ftperpixel,secs)
                    else:
                        direction = RIGHT_TO_LEFT
                        abs_chg = initial_x - x     
                        mph = get_speed(abs_chg,r2l_ftperpixel,secs)           

                    counter+=1   #Increment counter

                    speeds = np.append(speeds, mph)   #Append speed to array

                    if mph < 0:
                        if CONSOLE_DEBUGGER >= 3: print("[INFO] Negative speed - stopping tracking"+ "{0:7.2f}".format(secs))
                        if direction == LEFT_TO_RIGHT:
                            direction = RIGHT_TO_LEFT  #Reset correct direction
                            x=1  #Force save
                        else:
                            direction = LEFT_TO_RIGHT  #Reset correct direction
                            x=monitored_width + MIN_SAVE_BUFFER  #Force save
                    else:
                        if CONSOLE_DEBUGGER >= 1: print("[TRACKING] %4d  %7.2f  %3.0f  %4d  %5d %6d  %3s  %2d   %s" %
                            (abs_chg, secs, mph, x, w, biggest_area, direction, counter, timestamp.strftime("%H:%M:%S-%f")))
                    
                    real_y = upper_left_y + y
                    real_x = upper_left_x + x
                  

                    # is front of object outside the monitired boundary? Then write date, time and speed on image
                    # and save it 
                    if ((x <= adjusted_save_buffer) and (direction == RIGHT_TO_LEFT)) \
                            or ((x+w >= monitored_width - adjusted_save_buffer) \
                            and (direction == LEFT_TO_RIGHT)):
                        
                        #you need at least 2 data points to calculate a mean and we're deleting one on line below
                        if (counter > 2): 
                            mean_speed = np.mean(speeds[:-1])   #Mean of all items except the last one
                            sd = np.std(speeds[:-1])  #SD of all items except the last one
                        elif (counter > 1):
                            mean_speed = speeds[-1] # use the last element in the array
                            sd = 99 # Set it to a very high value to highlight it's not to be trusted.
                        else:
                            mean_speed = 0 #ignore it 
                            sd = 0

                        if CONSOLE_DEBUGGER >= 1: print("[DATA] mean_speed: %.0f sd: %.0f" % (mean_speed, sd))

                        #Captime used for mqtt, csv, image filename. 
                        cap_time = datetime.datetime.now()                    

                        # save the data if required and above min speed for data
                        if SAVE_CSV and mean_speed > MIN_SPEED_SAVE and mean_speed < MAX_SPEED_SAVE:
                            if lightlevel > 1: imageFilename_full = store_image(cap_time, image, mean_speed, direction)
                            store_traffic_data(cap_time, mean_speed, direction, counter, sd, imageFilename_full)
                        
                        counter = 0
                        state = SAVING #debug                    
                    # if the object hasn't reached the end of the monitored area, just remember the speed 
                    # and its last position
                    last_mph = mph
                    last_x = x
        else:
            # No motion detected
            if state == TRACKING:
                #Last frame has skipped the buffer zone    
                if (counter > 2): 
                    mean_speed = np.mean(speeds[:-1])   # Mean of all items except the last one
                    sd = np.std(speeds[:-1])  # remove last entry
                    if CONSOLE_DEBUGGER >= 1: print("[DATA] Missed but saving")
                elif (counter > 1):
                    mean_speed = speeds[-1] # use the last element in the array
                    sd = 99 # not trustworthy 
                    if CONSOLE_DEBUGGER >= 1: print("[DATA] Missed but saving")
                else:
                    mean_speed = 0 
                    sd = 0

                if CONSOLE_DEBUGGER >= 1: print("[DATA] mean_speed: %.0f sd: %.0f" % (mean_speed, sd))

                cap_time = datetime.datetime.now()
                
                # save the data if required and above min speed for data
                if SAVE_CSV and mean_speed > MIN_SPEED_SAVE and mean_speed < MAX_SPEED_SAVE:
                    # if lightlevel > 1: 
                    imageFilename_full = store_image(cap_time, image, mean_speed, direction)
                    store_traffic_data( cap_time, mean_speed, direction, counter, sd, imageFilename_full)

            if state != WAITING:
                state = WAITING
                direction = UNKNOWN
                text_on_image = 'Waiting for another car'
                counter = 0
                if CONSOLE_DEBUGGER >= 3: print("[INFO] %s" % text_on_image)
                
        # only update image and wait for a keypress when waiting for a car
        # This is required since waitkey slows processing.
        if (state == WAITING):    
     
            # draw the text and timestamp on the frame
            cv2.putText(image, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                (10, image.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 1)
            cv2.putText(image, "Road Status: {}".format(text_on_image), (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX,0.35, (0, 0, 255), 1)
         
            # show the frame and check for a keypress
            if SHOW_IMAGE == 'on':
                # prompt_on_image(prompt, image)
                image = overlay_transparent(image, thresh, upper_left_x, upper_left_y, 95)
                if SHOW_BOUNDS:
                    #define the monitored area right and left boundary
                    cv2.line(image,(upper_left_x,upper_left_y),(upper_left_x,lower_right_y),(0, 255, 0))
                    cv2.line(image,(lower_right_x,upper_left_y),(lower_right_x,lower_right_y),(0, 255, 0))
                cv2.imshow("Speed Camera", image)
                
            # Adjust the base_image as lighting changes through the day
            if state == WAITING:
                last_x = 0
                cv2.accumulateWeighted(gray, base_image, 0.25)
                t2 = time.process_time()
                if (t2 - t1) > 60:   # We need to measure light level every so often
                    t1 = time.process_time()
                    lightlevel = my_map(measure_light(hsv),0,256,1,10)

                    if CONSOLE_DEBUGGER >= 3: print("[INFO] Light Level = " + str(lightlevel))

                    adjusted_min_area = get_min_area(lightlevel)
                    adjusted_threshold = get_threshold(lightlevel)
                    adjusted_save_buffer = get_save_buffer(lightlevel)
                    if lightlevel != last_lightlevel:
                        base_image = None
                    last_lightlevel = lightlevel
            state=WAITING

            # if the `q` key is pressed, break from the loop and terminate processing
            # if running headless give a preview image with hotzone to calibrate blind
            if first_pass == True:
                calibration_image(image)
                first_pass = False
            elif cv2.waitKey(1) & 0xFF == ord('q'):
                calibration_image(image)
                print("[EXIT] Quit at %s" % datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"))
                break

             
        # clear the stream in preparation for the next frame
        rawCapture.truncate(0)
    # cleanup the camera and close any open windows
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # if not("RUNNING_PYCHARM" in os.environ):
    #     print("123", os.environ)
    # else:
    #     print("abc", os.environ)

    main()
