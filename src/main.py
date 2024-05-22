import io
from concurrent.futures import ProcessPoolExecutor
from typing import List, Callable

import xmltodict
from PIL import Image
from fastapi import FastAPI, UploadFile, File, HTTPException
from pytesseract import pytesseract

app = FastAPI()


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
    _dict = pytesseract.image_to_data(image)
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
    text = await process_image_in_ppe(image, _image_to_string)
    tokens: List[str] = text.split()

    token = ""
    for index, token in enumerate(tokens):
        if token[:4] == "BLAZ":
            if len(token) == 4:
                token = tokens[index] + tokens[index + 1]
                break

            print(tokens[index + 1])

            if len(token) != 16 and tokens[index + 1] == "Reference":
                # edge case where BLAZ reference takes more than 1 line
                # and therefore is an insufficient number of characters
                token = token + tokens[index + 2]
                break

            break

    if len(token) != 16:
        raise HTTPException(422, f"Error finding BLAZ {tokens}")

    return {"BLAZ": token}


@app.post("/blaz/data", status_code=201)
async def image_to_data(image: UploadFile = File(...)) -> dict:
    return await process_image_in_ppe(image, _image_to_json)
