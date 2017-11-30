#!/bin/python3

import sys
import math
import statistics
import numpy as np
import cv2

from hole import Hole
from hough import Hough

state, p1x, p1y, p2x, p2y, distance = 0,0,0,0,0,0
circles = []
selected = False
s1x, s1y, s2x, s2y = 0, 0, 0, 0
img = []
def calculateDispersion(circles, pixelDist, realDist):
    n = len(circles)

    if n > 0:
        meanX = statistics.mean(c.x for c in circles)
        meanY = statistics.mean(c.y for c in circles)
        meanDist = 0
        for i in circles:
            meanDist += math.sqrt(math.pow(float(i.x) - meanX, 2) + math.pow(float(i.y) - meanY, 2))
        meanDist /= n
        meanRealDist = meanDist * realDist / pixelDist
        #print("Conversion: %f pixels to %f in" % (pixelDist, realDist))
        print("Mean distance: %f in" % meanRealDist)

def originalCallback(event, x, y, flags, param):
    global selecting, img, mask
    global s1x, s1y, s2x, s2y
    if event == cv2.EVENT_LBUTTONDOWN:
        print("Mouse down (%d, %d)" %(x, y))
        s1x = x
        s1y = y
    elif event == cv2.EVENT_LBUTTONUP:
        print("Mouse up (%d, %d)" %(x, y))
        s2x = x
        s2y = y
        # create the mask
        mask = np.zeros(img.shape, dtype="uint8")
        cv2.rectangle(mask, (s1x, s1y), (s2x, s2y), (255, 255, 255), -1)
        selected = True

def pprocCallback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDBLCLK:
        print("Mouse: (%d, %d)" %(x, y))
        global state, p1x, p1y, p2x, p2y
        global circles
        if state == 0:
            p1x = x
            p1y = y
            state = 1
        elif state == 1:
            p2x = x
            p2y = y
            state = 0
            distance = math.sqrt(math.pow(p1x - p2x, 2) + math.pow(p1y - p2y, 2))
            realDistance = float(input("Input real distance (in):: "))
            calculateDispersion(circles, distance, realDistance)

def sharpen(image):
   kernel = np.array([
                      [1,4,6,4,1],
                      [4,16,24,16,4],
                      [6, 24, -476, 25, 6],
                      [4,16,24,16,4],
                      [1,4,6,4,1]
                     ])
   kernel = np.multiply(kernel, -1/256)
   output = cv2.filter2D(image, -1, kernel)
   return output

def m_erode(image, kernel, iterations = 1):
    return cv2.erode(image, kernel, iterations = iterations, borderType = cv2.BORDER_CONSTANT, borderValue = 0)

def m_dilate(image, kernel, iterations = 1):
    return cv2.dilate(image, kernel, iterations = iterations, borderType = cv2.BORDER_CONSTANT, borderValue = 0)

def m_hitmiss(image, kernel, iterations = 1):
    return cv2.morphologyEx(image, cv2.MORPH_HITMISS, kernel, iterations = iterations)

def m_top(image, kernel, iterations = 1):
    return cv2.morphologyEx(image, cv2.MORPH_TOPHAT, kernel, iterations = iterations)

def m_black(image, kernel, iterations = 1):
    return cv2.morphologyEx(image, cv2.MORPH_BLACKHAT, kernel, iterations = iterations)

def m_close(image, kernel, iterations = 1):
    return cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel, iterations = iterations)

def m_open(image, kernel, iterations = 1):
    return cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel, iterations = iterations)

def morph_preprocess(image, w, h, s1x, s1y, s2x, s2y):
    output = image
    win_w = max(int(w / 150), 11)
    win_h = max(int(w / 150), 11)
    if (win_w % 2) == 0:
        win_w += 1
    if (win_h % 2) == 0:
        win_h += 1
    output = cv2.GaussianBlur(output, (win_w, win_h), int(win_w / 2), int(win_w / 2))
    output = cv2.bilateralFilter(output, win_w, int(win_w / 2), int(win_w / 2))

    # 11
    output = cv2.adaptiveThreshold(output,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,win_w,2)

    n = 1
    k_rect = cv2.getStructuringElement(cv2.MORPH_RECT,(5,5))
    output = m_close(output, k_rect, n)
    output = m_close(output, k_rect, n)

    #n = 1
    #k_rect4 = cv2.getStructuringElement(cv2.MORPH_RECT,(4,4))
    #k_circle3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))
    #k_cross4 = cv2.getStructuringElement(cv2.MORPH_CROSS,(4,4))
    #k_cross2 = cv2.getStructuringElement(cv2.MORPH_CROSS,(2,2))
    #k_radial = np.array([
    #                      [  1,  0,  0,  0,  1],
    #                      [  0,  1,  0,  1,  0],
    #                      [  0,  0,  1,  0,  0],
    #                      [  0,  1,  0,  1,  0],
    #                      [  1,  0,  0,  0,  1]
    #                 ], dtype=np.uint8)

    #output = m_close(output, k_circle3, n)
    #output = m_close(output, k_radial, n)
    #output = m_black(output, k_cross2, n)
    #output = m_top(output, k_cross2, n)
    #output = m_top(output, k_cross2, n)
    #output = m_close(output, k_radial, n)

    #output = m_close(output, k_radial, 10)
    #output = m_close(output, k_radial, 10)
    #output = m_erode(output, k_radial, 10)
    #output = m_close(output, k_radial, 10)
    #output = m_close(output, k_radial, 10)
    return output

def filter_preprocess2(image, w, h, s1x, s1y, s2x, s2y):
    win_w = int(w / 100)
    win_h = int(h / 100)
    if (win_w % 2) == 0:
        win_w += 1
    if (win_h % 2) == 0:
        win_h += 1
    print("ROI width: %d, ROI height: %d" %(w, h))
    print("Window width: %d, window height: %d" %(win_w, win_h))

    output = cv2.GaussianBlur(output, (win_w, win_h), int(win_w / 2), int(win_w / 2))
    output = cv2.bilateralFilter(output, win_w, int(win_w / 2), int(win_w / 2))
    output = cv2.equalizeHist(output)
    output = cv2.medianBlur(output, win_w)
    output = cv2.blur(output, (win_w, win_h))
    output = cv2.bilateralFilter(output, win_w, int(win_w / 2), int(win_w / 2))
    output = cv2.bilateralFilter(output, win_w, int(win_w / 2), int(win_w / 2))
    output = cv2.bilateralFilter(output, win_w, int(win_w / 2), int(win_w / 2))
    output = cv2.bilateralFilter(output, win_w, int(win_w / 2), int(win_w / 2))
    output = cv2.bilateralFilter(output, win_w, int(win_w / 2), int(win_w / 2))
    return output

def filter_preprocess(image, w, h, s1x, s1y, s2x, s2y):
    output = image

    win_w = int(w / 100)
    win_h = int(h / 100)
    if (win_w % 2) == 0:
        win_w += 1
    if (win_h % 2) == 0:
        win_h += 1
    print("ROI width: %d, ROI height: %d" %(w, h))
    print("Window width: %d, window height: %d" %(win_w, win_h))
    output = cv2.blur(output, (win_w, win_h))
    output = cv2.GaussianBlur(output, (win_w, win_h), int(win_w / 2), int(win_w / 2))
    output = cv2.medianBlur(output, win_w)
    output = cv2.bilateralFilter(output, win_w, int(win_w / 2), int(win_w / 2))

    return output

# returns processed image
def preprocess(image, w, h, s1x, s1y, s2x, s2y):
    output = image[s1y:s2y, s1x:s2x]

    output = filter_preprocess(output, w, h, s1x, s1y, s2x, s2y)

    whole = np.copy(image)
    whole[s1y:s2y, s1x:s2x] = output

    return whole

def main():
    image_path = "target0.jpg"
    if len(sys.argv) > 1:
        image_path = sys.argv[1]


    # Create window with freedom of dimensions
    cv2.namedWindow("original", cv2.WINDOW_NORMAL)
    cv2.namedWindow("preprocess", cv2.WINDOW_NORMAL)
    cv2.namedWindow("edges", cv2.WINDOW_NORMAL)
    cv2.namedWindow("output", cv2.WINDOW_NORMAL)

    # MOA calculator callback
    cv2.setMouseCallback('original', originalCallback)
    cv2.setMouseCallback('output', pprocCallback)

    # Load an color image in grayscale
    global img, mask, unselected
    img = cv2.imread(image_path, 0)

    cv2.imshow('original', img)

    print("Select ROI and hit any key")
    cv2.waitKey(0)

    # preprocessing
    global s1x, s1y, s2x, s2y
    roi_w = abs(s1x - s2x)
    roi_h = abs(s1y - s2y)
    proc = cv2.bitwise_and(preprocess(img, roi_w, roi_h, s1x, s1y, s2x, s2y), mask)

    cv2.imshow('preprocess', proc)
    cimg = cv2.cvtColor(img,cv2.COLOR_GRAY2BGR)

    hough = Hough()
    hough.dp        = 1.25
    hough.minDist   = 40
    hough.minRadius = 10
    hough.maxRadius = 120
    hough.canny     = 20
    hough.accum     = 60
    cv2.imshow('edges', hough.runCanny(proc))
    global circles
    circles = hough.houghDescent(proc)

    meanX = 0
    meanY = 0
    n = 0
    for i in circles:
        n += 1
        # draw the outer circle
        cv2.circle(cimg,(i.x,i.y),i.r+5,(0,0,0),-2)
        cv2.circle(cimg,(i.x,i.y),i.r,(0,255,0),-2)

        # draw the center of the circle
        cv2.circle(cimg,(i.x,i.y),2,(0,0,255),3)

        cv2.imshow('output',cimg)
        print('%d: (%d, %d)' %(n, i.x, i.y))

        meanX += i.x
        meanY += i.y

    # draw the mean as a cross
    if n > 0:
        meanX = np.uint16(meanX/n)
        meanY = np.uint16(meanY/n)

        thicc = 5
        size  = 40
        # back
        p1 = (meanX - thicc * 2, meanY - size - thicc * 2)
        p2 = (meanX + thicc * 2, meanY + size + thicc * 2)
        cv2.rectangle(cimg, p1, p2, (0,0,0), -1)
        p1 = (meanX - size - thicc * 2, meanY - thicc * 2)
        p2 = (meanX + size + thicc * 2, meanY + thicc * 2)
        cv2.rectangle(cimg, p1, p2, (0,0,0), -1)

        # fore
        p1 = (meanX - thicc * 1, meanY - size - thicc * 1)
        p2 = (meanX + thicc * 1, meanY + size + thicc * 1)
        cv2.rectangle(cimg, p1, p2, (0,0,255), -1)
        p1 = (meanX - size - thicc * 1, meanY - thicc * 1)
        p2 = (meanX + size + thicc * 1, meanY + thicc * 1)
        cv2.rectangle(cimg, p1, p2, (0,0,255), -1)

        print('Mean: (%d, %d)' %(meanX, meanY))
        cv2.imshow('output',cimg)

    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
