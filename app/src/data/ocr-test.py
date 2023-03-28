import pytesseract
import argparse
from PIL import Image, ImageOps
# import cv2
import pickle
import pandas as pd
import numpy as np
import datetime
import pytz
import re


def preprocess_image(image):
    pixels = image.load()
    th = 120
    for i in range(image.size[0]):  # for every pixel:
        for j in range(image.size[1]):
            if max(pixels[i, j]) > th:
                pixels[i, j] = (255, 255, 255)
            else:
                pixels[i, j] = (0, 0, 0)

    image = ImageOps.invert(image)

    return image

def crop_image(image):
    image = image.crop(0,0,800,140)
    return image


def image_to_text(image):
    pytesseract.pytesseract.tesseract_cmd = r'D:\Programas\Tesseract-OCR\tesseract.exe'
    config = '--oem 3 --psm 6'
    text = pytesseract.image_to_string(image, config=config, lang="eng")

    # Clean the text for deleting white lines
    new_text = ""
    text = text.split("\n")
    for i, line in enumerate(text):
        if not re.match(r'^\s*$', line):
            new_text += line + "\n"

    return new_text

def rows_to_columns(dic):
    cols = dic[0].keys()
    new_dic = {}
    for col in cols:
        new_dic[col] = []
        for elem in dic:
            new_dic[col].append(elem[col])
    return new_dic

def extract_info(text):
    if "LIVE" in text:
        bet_type = "Live"
    else:
        bet_type = "Pre match"

    lines = text.split("\n")
    try:
        stake = lines[-1].split(" ")[1].split("——")[0]
    except IndexError:
        stake = None

    try:
        tournament = lines[1][1:-1]
    except IndexError:
        tournament = None

    return {"bet_type": bet_type, "stake": stake, "tournament": tournament}

def extract_info_from_image(image_text, data, type=1):
    lines = image_text.split("\n")
    result = {}
    if type == 1:
        if data["bet_type"] == "Live":
            game = " ".join(lines[3].split(" ")[:-1])
        else:
            game = " ".join(lines[3].split(" ")[:-4])

        result["option"] = " ".join(lines[1].split(" ")[1:-1])
        try:
            result["home"] = game.split(" v ")[0].strip()
            result["away"] = game.split(" v ")[1].strip()
        except IndexError:
            # There are some times where the ocr does not work completely properly
            # and reads the "v" of versus as "vy"
            result["home"] = None
            result["away"] = None

        result["bet"] = lines[2]

    elif type == 2:
        try:
            result["option"] = " ".join(lines[0].split(" ")[:-1])
        except IndexError:
            result["option"] = None

        try:
            result["home"] = lines[2].split(" v ")[0].strip()
            result["away"] = lines[2].split(" v ")[1].strip()
        except IndexError:
            result["home"] = None
            result["away"] = None

        try:
            result["bet"] = lines[1]
        except IndexError:
            result["bet"] = None

    return result



if __name__ == "__main__":
    path = 'bet-history-images/'
    utc = pytz.UTC
    with open(path + "/text.pickle", "rb") as f:
        info = pickle.load(f)

    # i=58
    # img_path = path + "img" + str(i+1) + ".jpg"
    # image = Image.open(img_path, "r")
    # image = preprocess_image(image)
    # text = image_to_text(image)
    # print(text)
    # bet_info = extract_info(info[i]["text"])
    # info[i].update(bet_info)
    # print(info[i])
    # bet_info_1 = extract_info_from_image(text, info[i], type=1)
    # info[i].update(bet_info_1)
    # print(info[i])

    i = 713
    img_path = path + "img" + str(i + 1) + ".jpg"
    image = Image.open(img_path, "r")
    image = image.crop((0, 0, 800, 140))
    text = image_to_text(image)
    print(text)
    print(info[i])
    bet_info = extract_info(info[i]["text"])
    info[i].update(bet_info)
    print(info[i])
    bet_info_1 = extract_info_from_image(text, info[i], type=2)
    info[i].update(bet_info_1)
    print(info[i])




    # print(pd.DataFrame(rows_to_columns(info))[["id", "text"]])
    # for line in info[-1]["text"].split("\n"):
    #     print(line)
    for i in range(int(info[-1]["id"])):
    # for i in range(10):

        img_path = path + "img" + str(i+1) + ".jpg"
        image = Image.open(img_path, "r")
        print("img: ", i, " date: ", info[i]["date"])
        if info[i]["date"] >= utc.localize(datetime.datetime(2021, 6, 30)):
            image = preprocess_image(image)
            text = image_to_text(image)
            bet_info = extract_info(info[i]["text"])
            info[i].update(bet_info)
            bet_info_1 = extract_info_from_image(text, info[i], type=1)
            info[i].update(bet_info_1)
        else:
            image = image.crop((0, 0, 800, 140))
            text = image_to_text(image)
            bet_info = extract_info(info[i]["text"])
            info[i].update(bet_info)
            bet_info_1 = extract_info_from_image(text, info[i], type=2)
            info[i].update(bet_info_1)

    df = pd.DataFrame(rows_to_columns(info))
    print(df.head(10))

    with open("bet-history-images/stats.pickle", "wb") as f:
        pickle.dump(info, f)
