import requests
import base64
import numpy as np
from cv2 import *
import json
import RPi.GPIO as GPIO
import time
import sys
import signal


img_path = "im2.jpg"
url = "http://35.163.191.108:3000/api/request"

cont = True

def find_marker(image):
    # convert the image to grayscale, blur it, and detect edges
    gray = cvtColor(image, COLOR_BGR2GRAY)
    gray = GaussianBlur(gray, (5, 5), 0)
    edged = Canny(gray, 35, 125)
 
    # find the contours in the edged image and keep the largest one;
    # we'll assume that this is our piece of paper in the image
    (cnts, _) = findContours(edged.copy(), RETR_LIST, CHAIN_APPROX_SIMPLE)
    c = max(cnts, key = contourArea)
 
    # compute the bounding box of the of the paper region and return it
    return minAreaRect(c)[1]
 
def large_enough(image, threshold):
    area = find_marker(image) 
    area = area[0] * area[1]
    return area > threshold

def main():
    print("Initing GPIO and Webcam")
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(13, GPIO.OUT)
    serv1 = GPIO.PWM(13, 50)
    GPIO.setup(11, GPIO.OUT)
    serv2 = GPIO.PWM(11, 50)
    GPIO.setup(15, GPIO.OUT)
    serv3 = GPIO.PWM(15, 50)

    cam = VideoCapture(0)
    if not cam.isOpened():
        print("Unable to open camera")
        clean_exit()

    # Start the Servos
    serv1.start(12.5)
    serv2.start(12.5)
    serv3.start(12.5)

    print(cont)
    while cont:
        print("Starting img capture")
        if cam.isOpened():
            s, img = cam.read()
        else:
            print("Camera Lost")
            clean_exit()
            sys.exit(1)

        s, jimg = imencode(".jpeg", img)

        isObj = large_enough(img, 100000)

        if isObj:
            b64img = base64.b64encode(jimg)

            print("Sending POST")
            r = requests.post(url, json={"image" : b64img})

            jsresp = r.json()["status"]
            print(jsresp)

            # Compost
            if jsresp == 1:
                serv1.ChangeDutyCycle(2.5)
                time.sleep(8)
                serv1.ChangeDutyCycle(12.5)
            # Recycle
            elif jsresp == 2:
                serv2.ChangeDutyCycle(2.5)
                time.sleep(8)
                serv2.ChangeDutyCycle(12.5)
            # Trash
            elif jsresp == 3:
                serv3.ChangeDutyCycle(2.5)
                time.sleep(8)
                serv3.ChangeDutyCycle(12.5)
            # ALL
            else:
                serv1.ChangeDutyCycle(2.5)
                serv2.ChangeDutyCycle(2.5)
                serv3.ChangeDutyCycle(2.5)
                time.sleep(8)
                serv1.ChangeDutyCycle(12.5)
                serv2.ChangeDutyCycle(12.5)
                serv3.ChangeDutyCycle(12.5)

            time.sleep(5)

    print("Stopping Servos")
    serv1.stop()
    serv2.stop()
    serv3.stop()
    cam.release()

def clean_exit():
    print("Cleaning up")
    GPIO.cleanup()

def signal_handler(signal, frame):
#        cont = False
        clean_exit()
        sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()

    """try:
        main()
        clean_exit()
    except Exception as e:
	print(e)
        clean_exit()
        sys.exit(1)
    """
