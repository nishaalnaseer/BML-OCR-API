import io
from concurrent.futures import ProcessPoolExecutor
from typing import List, Callable

import cv2
import xmltodict
from PIL import Image
from fastapi import FastAPI, HTTPException, UploadFile, File
from icecream import ic
from pytesseract import pytesseract
from PIL import Image
import numpy as np


app = FastAPI()


def dissect(image_path, output_path):
    img = cv2.imread(image_path)

    # Convert the img to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply edge detection method on the image
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    # This returns an array of r and theta values
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

    # The below for loop runs till r and theta values
    # are in the range of the 2d array
    for r_theta in lines:
        arr = np.array(r_theta[0], dtype=np.float64)
        r, theta = arr
        # Stores the value of cos(theta) in a
        a = np.cos(theta)

        # Stores the value of sin(theta) in b
        b = np.sin(theta)

        # x0 stores the value rcos(theta)
        x0 = a * r

        # y0 stores the value rsin(theta)
        y0 = b * r

        # x1 stores the rounded off value of (rcos(theta)-1000sin(theta))
        x1 = int(x0 + 1000 * (-b))

        # y1 stores the rounded off value of (rsin(theta)+1000cos(theta))
        y1 = int(y0 + 1000 * (a))

        # x2 stores the rounded off value of (rcos(theta)+1000sin(theta))
        x2 = int(x0 - 1000 * (-b))

        # y2 stores the rounded off value of (rsin(theta)-1000cos(theta))
        y2 = int(y0 - 1000 * (a))

        # cv2.line draws a line in img from the point(x1,y1) to (x2,y2).
        # (0,0,255) denotes the colour of the line to be
        # drawn. In this case, it is red.
        cv2.line(img, (x1, y1), (x2, y2), (0, 0, 255), 2)

    # All the changes made in the input image are finally
    # written on a new image houghlines.jpg
    cv2.imwrite('tests/linesDetected.jpg', img)


def _image_to_string(contents: bytes) -> str:
    # Convert to a PIL image
    image = Image.open(io.BytesIO(contents))
    text = pytesseract.image_to_string(image)

    return text


def _image_to_json(contents: bytes) -> dict:
    image = Image.open(io.BytesIO(contents))
    _xml = pytesseract.image_to_alto_xml(image)
    _json = xmltodict.parse(_xml)
    return _json


def _image_to_data(contents: bytes) -> dict:
    image = Image.open(io.BytesIO(contents))
    _dict = pytesseract.image_to_d(image)
    return _dict



async def process_image_in_ppe(image: UploadFile, function: Callable):
    # Read the file contents
    contents = await image.read()
    with ProcessPoolExecutor() as executor:
        future = executor.submit(function, contents)
        text = future.result()

    return text


@app.post("/ocr", status_code=201)
async def image_to_string(image: UploadFile = File(...)):
    text = await process_image_in_ppe(image, _image_to_string)

    return {"text": text}


@app.post("/blaz/json", status_code=201)
async def image_to_json(image: UploadFile = File(...)) -> dict:
    return await process_image_in_ppe(image, _image_to_json)
    # _json = xmltodict.parse(xml)

    # ic(_json)

    # return _json


@app.post("/blaz", status_code=201)
async def image_to_blaz(image: UploadFile = File(...)) -> dict:
    text = await process_image_in_ppe(image)
    tokens: List[str] = text.split()

    token = ""
    for index, token in enumerate(tokens):
        if token[:4] == "BLAZ":
            if len(token) == 4:
                token = tokens[index] + tokens[index + 1]
                break

            print(tokens[index + 1])

            if len(token) != 16 and tokens[index + 1] == "Reference":
                token = token + tokens[index + 2]
                break

            break

    if len(token) != 16:
        raise HTTPException(422, f"Error finding BLAZ {tokens}")

    return {"BLAZ": token}


@app.post("/blaz/data", status_code=201)
async def image_to_data(image: UploadFile = File(...)) -> dict:
    return await process_image_in_ppe(image, _image_to_json)
