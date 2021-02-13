
from picamera.array import PiRGBArray
from picamera import PiCamera
import cv2
import time
from _configs import *

coords = []
drawing = False



def get_image(source):
    # open the camera, grab a frame, and release the camera
    cam = cv2.VideoCapture(source)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUTION[0])
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUTION[1])
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
    rawCapture = PiRGBArray(camera)
    time.sleep(0.3)
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
      image = frame.array
      rawCapture.truncate(0)
      print(image.shape)
      return image
      break
    return None


def click_and_crop(event, x, y, flag, image):
    """
    Callback function, called by OpenCV when the user interacts
    with the window using the mouse. This function will be called
    repeatedly as the user interacts.
    """
    # get access to a couple of global variables we'll need
    global coords, drawing, clone, h, w
    if event == cv2.EVENT_LBUTTONDOWN:
        # user has clicked the mouse's left button
        drawing = True
        # save those starting coordinates
        coords = [(x, y)]
    elif event == cv2.EVENT_MOUSEMOVE:
        # user is moving the mouse within the window
        if drawing is True:
            # if we're in drawing mode, we'll draw a green rectangle
            # from the starting x,y coords to our current coords
            clone = image.copy()
            cv2.rectangle(clone, coords[0], (x, y), (0, 255, 0), 2)
            cv2.imshow('CapturedImage', clone)
    elif event == cv2.EVENT_LBUTTONUP:
        # user has released the mouse button, leave drawing mode
        # and crop the photo
        drawing = False
        # save our ending coordinates
        coords.append((x, y))
        if len(coords) == 2:
            # calculate the four corners of our region of interest
            ty, by, tx, bx = coords[0][1], coords[1][1], coords[0][0], coords[1][0]
            crop_clone = clone[ty:by,tx:bx]
            h, w, _ = crop_clone.shape
            fontScale=.6
            beginText = "%sx,%sy - Begin" % (tx,ty)
            endText = "%sx,%sy - End" % (bx,by)
            txt_demensions = "%dh x %dw" % (h,w)
            txt_bsize, bbase = cv2.getTextSize(beginText, fontFace=cv2.FONT_HERSHEY_DUPLEX, fontScale=fontScale, thickness=2)
            # txt_esize, ebase = cv2.getTextSize(endText, fontFace=cv2.FONT_HERSHEY_DUPLEX, fontScale=fontScale, thickness=2) 
            scale=10
            for txt in [beginText, endText, txt_demensions]:
              cv2.putText(clone, txt, (4,txt_bsize[1]+scale), cv2.FONT_HERSHEY_DUPLEX, fontScale, (255, 255, 255), 3) 
              cv2.putText(clone, txt, (4,txt_bsize[1]+scale), cv2.FONT_HERSHEY_DUPLEX, fontScale, (255, 0, 0), 2) 
              print(txt)
              scale = scale+30
            cv2.imshow('CapturedImage', clone)
            # Save the image
            cv2.imwrite(f"{PATH_TO_IMAGES}/calibrator.jpg", clone)
            # crop the image using array slicing
            roi = image[ty:by, tx:bx]
            height, width = roi.shape[:2]
            if width > 0 and height > 0:
                # make sure roi has height/width to prevent imshow error
                # and show the cropped image in a new window
                # cv2.namedWindow("ROI", cv2.WINDOW_NORMAL)
                cv2.imshow("ROI", roi)

def click_and_cropx(event, x, y, flag, image):
    """
    Callback function, called by OpenCV when the user interacts
    with the window using the mouse. This function will be called
    repeatedly as the user interacts.
    """
    # get access to a couple of global variables we'll need
    global coords, drawing, s_x, s_y
    if event == cv2.EVENT_LBUTTONDOWN:
        # user has clicked the mouse's left button
        drawing = True
        # save those starting coordinates
        coords = [(x, y)]
        s_x, s_y = (x, y)
    elif event == cv2.EVENT_MOUSEMOVE:
        # user is moving the mouse within the window
        if drawing is True:
            # if we're in drawing mode, we'll draw a green rectangle
            # from the starting x,y coords to our current coords
            clone = image.copy()
            fontScale=.6
            beginText = "x: %s, y:%s" % (s_x,s_y)
            endText = "x: %s, y:%s" % (x,y)
            bsize, bbase = cv2.getTextSize(beginText, fontFace=cv2.FONT_HERSHEY_DUPLEX, fontScale=fontScale, thickness=2)
            esize, ebase = cv2.getTextSize(endText, fontFace=cv2.FONT_HERSHEY_DUPLEX, fontScale=fontScale, thickness=2)
            # cv2.putText(clone, beginText, (s_x+8,s_y+bsize[1]+4), cv2.FONT_HERSHEY_DUPLEX, fontScale, (255, 0, 0), 2) 
            # cv2.putText(clone, endText, (x,y), cv2.FONT_HERSHEY_DUPLEX, fontScale, (255, 0, 0), 2) 
            cv2.rectangle(clone, coords[0], (x+esize[0], y), (0, 255, 0), 2)
            cv2.imshow('CapturedImage', clone)
    elif event == cv2.EVENT_LBUTTONUP:
        # user has released the mouse button, leave drawing mode
        # and crop the photo
        drawing = False
        # save our ending coordinates
        coords.append((x, y))
        if len(coords) == 2:
            # calculate the four corners of our region of interest
            ty, by, tx, bx = coords[0][1], coords[1][1], coords[0][0], coords[1][0]
            # crop the image using array slicing
            roi = image[ty:by, tx:bx]
            height, width = roi.shape[:2]
            if width > 0 and height > 0:
                # make sure roi has height/width to prevent imshow error
                # and show the cropped image in a new window
                cv2.namedWindow("ROI", cv2.WINDOW_NORMAL)
                cv2.imshow("ROI", roi)


def main():
# image_source = "media/images/calibrate.jpg"
    image = get_image(0)
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



if __name__ == "__main__":
    main()