
from picamera.array import PiRGBArray
from picamera import PiCamera
import cv2
import time
from _configs import *

coords = []
drawing = False
last_x = 0
last_y = 0



def get_image(source):
    # open the camera, grab a frame, and release the camera
    cam = cv2.VideoCapture(source)
    print(RESOLUTION[0])
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUTION[0])
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUTION[1])
    # cv2.resizeWindow("framename", RESOLUTION[0], RESOLUTION[1])

    # cap.set(cv2.cv.CV_CAP_PROP_FPS, FPS)
    # Read picture. ret === True on success
    image_captured, image = cam.read()
    cam.release()
    if (image_captured):
        return image
    return None

def piimage():
    # open the camera, grab a frame, and release the camera
    camera = PiCamera()
    camera.resolution = RESOLUTION
    camera.framerate = FPS
    camera.vflip = False
    camera.hflip = False
    rawCapture = PiRGBArray(camera)
    time.sleep(0.8)
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
      image = frame.array
      rawCapture.truncate(0)
      print(image.shape)
      return image
      break
    return None

def insert_text_on_img(image, coords):
    # calculate the four corners of our region of interest
    ty, by, tx, bx = coords[0][1], coords[1][1], coords[0][0], coords[1][0]
    crop_clone = image[ty:by,tx:bx]
    h, w, _ = crop_clone.shape
    fontScale=.6
    beginText = "%sx,%sy - Begin" % (tx,ty)
    endText = "%sx,%sy - End" % (bx,by)
    txt_demensions = "%dh x %dw" % (h,w)
    txt_bsize, bbase = cv2.getTextSize(beginText, fontFace=cv2.FONT_HERSHEY_DUPLEX, fontScale=fontScale, thickness=2)
    # txt_esize, ebase = cv2.getTextSize(endText, fontFace=cv2.FONT_HERSHEY_DUPLEX, fontScale=fontScale, thickness=2) 
    scale=10
    for txt in [beginText, endText, txt_demensions]:
        cv2.putText(image, txt, (4,txt_bsize[1]+scale), cv2.FONT_HERSHEY_DUPLEX, fontScale, (255, 255, 255), 3) 
        cv2.putText(image, txt, (4,txt_bsize[1]+scale), cv2.FONT_HERSHEY_DUPLEX, fontScale, (255, 0, 0), 2) 
        if drawing == True:
            print(txt)
        scale = scale+30
    return image, ty, by, tx, bx

def click_and_crop(event, x, y, flag, image):
    """
    Callback function, called by OpenCV when the user interacts
    with the window using the mouse. This function will be called
    repeatedly as the user interacts.
    """
    # get access to a couple of global variables we'll need
    global coords, drawing, clone, h, w, last_x, last_y
    if event == cv2.EVENT_LBUTTONDOWN:
        # user has clicked the mouse's left button
        drawing = True
        # save those starting coordinates
        coords = [(x, y)]
    elif event == cv2.EVENT_MOUSEMOVE:
        # user is moving the mouse within the window
        if drawing is True:
            last_x = x
            last_y = y
    elif event == cv2.EVENT_LBUTTONUP:
        # user has released the mouse button, leave drawing mode
        # and crop the photo
        # save our ending coordinates
        coords.append((x, y))
        if len(coords) == 2:
            image, ty, by, tx, bx = insert_text_on_img(image, coords)
            cv2.imshow('CapturedImage', image)
            # Save the image
            cv2.imwrite(f"{PATH_TO_IMAGES}/calibrator.jpg", image)
            # crop the image using array slicing
            roi = image[ty:by, tx:bx]
            height, width = roi.shape[:2]
            if width > 0 and height > 0:
                # make sure roi has height/width to prevent imshow error
                # and show the cropped image in a new window
                # cv2.namedWindow("ROI", cv2.WINDOW_NORMAL)
                coords_to_file = f'UPPER_LEFT_X = {tx}\nUPPER_LEFT_Y = {ty}\nLOWER_RIGHT_X = {bx}\nLOWER_RIGHT_Y = {by}'
                print(coords_to_file)
                #--- write to file
                f = open('_configs_coords.py', 'r+')
                f.write(coords_to_file+"\n")
                f.close
                
                # cv2.imshow("ROI", roi)
        drawing = False



def main_still_img():
# image_source = "media/images/calibrate.jpg"
    # image = get_image(0)
    image = piimage()
    if image is not None:
        # show the captured image in a window
        # cv2.namedWindow('CapturedImage', cv2.WINDOW_NORMAL)
        cv2.imshow('CapturedImage', image)
        # specify the callback function to be called when the user
        # clicks/drags in the 'CapturedImage' window
        cv2.setMouseCallback('CapturedImage', click_and_crop, image)
        while True:
            # wait for Esc or q key and then exit
            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord("q"):
                # print('Image cropped at coordinates: %s - %dw x %dh' % (format(coords), w, h))
                cv2.destroyAllWindows()
                break

def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUTION[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUTION[1])
    # cap.set(cv2.cv.CV_CAP_PROP_FPS, FPS)
    # specify the callback function to be called when the user
    # clicks/drags in the 'CapturedImage' window
    while True:
        #Reading the first frame
        _, image = cap.read()

        if last_x > 0 and last_y > 0:
            if drawing == False:
                image, _, _, _, _ = insert_text_on_img(image, coords)
            cv2.rectangle(image, coords[0], (last_x, last_y), (0, 255, 0), 2)
        # show the captured image in a window
        # cv2.namedWindow('CapturedImage', cv2.WINDOW_NORMAL)
        cv2.imshow('CapturedImage', image)

        cv2.setMouseCallback('CapturedImage', click_and_crop, image)


        # wait for Esc or q key and then exit
        key = cv2.waitKey(1) & 0xFF
        if key == 27 or key == ord("q"):
            cv2.destroyAllWindows()
            break



if __name__ == "__main__":
    main()