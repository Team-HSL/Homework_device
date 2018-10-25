#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Created on Fri Oct 19 2018
@author: Y.S
'''

import cv2
import requests
import time
# If you are using a Jupyter notebook, uncomment the following line.
#%matplotlib inline
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from PIL import Image
from io import BytesIO

#画像切り抜き対象の座標を取得
def getRectByPoints(points):
    points = list(map(lambda x: x[0], points))

    points = sorted(points, key=lambda x:x[1])
    top_points = sorted(points[:2], key=lambda x:x[0])
    bottom_points = sorted(points[2:4], key=lambda x:x[0])
    points = top_points + bottom_points

    left = min(points[0][0], points[2][0])
    right = max(points[1][0], points[3][0])
    top = min(points[0][1], points[1][1])
    bottom = max(points[2][1], points[3][1])
    return (top, bottom, left, right)

#画像を切り抜き
def getPartImageByRect(rect):
    img = cv2.imread(image_dir + image_file, 1)
    return img[rect[0]:rect[1], rect[2]:rect[3]]

image_dir = './raw/'
image_file = 'test.jpg'
im = cv2.imread(image_dir + image_file, 1)

#グレースケール化
im_gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
im_blur = cv2.GaussianBlur(im_gray, (11, 11), 0)
th = cv2.threshold(im_blur, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)[1]

#輪郭の座標を抽出
contours = cv2.findContours(th, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[1]

#輪郭の頂点を元に面積を計算・一定以上の大きさの部分を切り出し
th_area = im.shape[0] * im.shape[1] / 100
contours_large = list(filter(lambda c:cv2.contourArea(c) > th_area, contours))

#画像の切り抜き
outputs = []
rects = []
approxes = []
pixel_th = 50

for (i,cnt) in enumerate(contours_large):
    arclen = cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, 0.02*arclen, True)
    if len(approx) < 4:
        continue
    approxes.append(approx)
    rect = getRectByPoints(approx)
    rects.append(rect)
    outputs.append(getPartImageByRect(rect))
    cv2.imwrite('./output/output' + str(i) + '.jpg', outputs[i])
    #マーカーがあれば正解
    pixelValue = outputs[i][int(outputs[i].shape[1] / 20), int(outputs[i].shape[0] / 20)]
    for pixel in pixelValue:
        if pixel > pixel_th:
            break
    else:
        pre_img = outputs[i]
        pre_img = pre_img.tolist()
        cv2.imwrite('./output/presence_num.jpg', outputs[i])

'''
1.pre_imgをAPIに投げて手書き数字認識
'''

# -------------------  Azureの利用 -------------------------------
#--------------------- API情報を入力 ------------------------------

# キーを入力
file = open('key_cog.txt')
key = file.read()
subscription_key = key
assert subscription_key

vision_base_url = "https://westcentralus.api.cognitive.microsoft.com/vision/v2.0/"
text_recognition_url = vision_base_url + "recognizeText"

# Localから画像を取得する
# 画像へのパスをimage_fileに代入
image_file = './output/presence_num.jpg'
image_data = open(image_file, "rb").read()
headers    = {'Ocp-Apim-Subscription-Key': subscription_key,
              'Content-Type': 'application/octet-stream'}

#--------------- 画像から取得したい情報の指定 -------------------
params  = {'mode': 'Handwritten'}

# Local画像の場合
response = requests.post(
    text_recognition_url, headers=headers, params=params, data=image_data)
response.raise_for_status()

operation_url = response.headers["Operation-Location"]

analysis = {}
poll = True
while (poll):
    response_final = requests.get(
        response.headers["Operation-Location"], headers=headers)
    analysis = response_final.json()
    time.sleep(1)
    if ("recognitionResult" in analysis):
        poll= False
    if ("status" in analysis and analysis['status'] == 'Failed'):
        poll= False

polygons=[]
if ("recognitionResult" in analysis):
    # Extract the recognized text, with bounding boxes.
    polygons = [(line["boundingBox"], line["text"])
        for line in analysis["recognitionResult"]["lines"]]
print(polygons)

'''
2.スプレッドシート上で提出済みとする
'''
