import json
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from io import BytesIO
from typing import List, Any, Tuple

import xmltodict
from fastapi import HTTPException, UploadFile
from icecream import ic
from PIL import Image
from pytesseract import pytesseract

from src.models import *


def _image_to_string(image: Image) -> str:
    # Convert to a PIL image
    text = pytesseract.image_to_string(image)

    return text


def _append(array: List[dict], key: str, obj: Any) -> None:
    next_block = obj["String"]
    if type(next_block) is list:
        array.extend(next_block)
    else:
        array.append(next_block)


def _traverse(obj: dict | list, array: List[dict]):
    try:
        _append(array, "String", obj)
    except TypeError:
        for _obj in obj:
            _traverse(_obj, array)
    except KeyError:
        try:
            next_block = obj["TextLine"]
            _traverse(next_block, array)
        except KeyError:
            pass


def is_white(_input: tuple[int]):
    for x in _input:
        if x < 253:
            return False

    return True


def get_next_gray_line(img: Image, start_cors: tuple[int, int]) -> tuple[int, int]:
    start_x, start_y = start_cors[0], start_cors[1]

    for y in range(start_y, img.height):
        cors = (134, y,)
        color = img.getpixel(cors)

        if not is_white(color):
            flag = True
            for x in range(start_x, 50 + start_x):
                new_color = img.getpixel((x, y))
                if is_white(new_color):
                    flag = False
                    break

            if flag:
                return start_x, y,

    raise GrayLineNotFound()


def crop_next_section(img: Image, y_cors: int, x_crop: int) -> tuple[Image, int]:
    next_gray_line = get_next_gray_line(img, (134, y_cors,))
    _cropped = img.crop((x_crop, y_cors, img.width, next_gray_line[1]))
    return _cropped, next_gray_line[1]


def get_x_crop_cors(block: dict) -> int:
    return int(block["@HPOS"]) + int(block["@WIDTH"]) + 10


def _format_string(string: str):
    return string.replace("\n", "").replace(" ", "")


def make_blaz(content: bytes) -> BLAZ:
    image = Image.open(BytesIO(content))

    xml = pytesseract.image_to_alto_xml(image)
    image_content = xmltodict.parse(xml)

    blocks = image_content["alto"]["Layout"]["Page"]["PrintSpace"]["ComposedBlock"]

    string_block_array: List[Any] = []

    for block in blocks:
        text_block = block["TextBlock"]
        _traverse(text_block, string_block_array)

    blocks = {
        block["@CONTENT"]: block for block in
        string_block_array
    }

    # get where to start cropping from the x axis
    status_block = blocks["Status"]
    message_block = blocks["Message"]
    reference_block = blocks["Reference"]
    date_block = blocks["date"]
    from_block = blocks["From"]
    amount_block = blocks["Amount"]

    status_x_cors = get_x_crop_cors(status_block)
    message_x_cors = get_x_crop_cors(message_block)
    reference_x_cors = get_x_crop_cors(reference_block)
    date_x_cors = get_x_crop_cors(date_block)
    from_x_cors = get_x_crop_cors(from_block)
    amount_x_cors = get_x_crop_cors(amount_block)

    # crop status block
    status_start = int(status_block["@VPOS"]) - 10
    status_end = int(status_block["@HEIGHT"]) + 30 + status_start

    upper = status_start
    right = image.width
    lower = status_end

    status_cropped = image.crop((status_x_cors, upper, right, lower))
    status_cropped.save("status.jpg")

    # crop message block
    message_section_start = lower + 10
    start_x = 134
    message_start = get_next_gray_line(image, (start_x, message_section_start,))
    message_cropped, next_y = crop_next_section(image, message_start[1] + 10, message_x_cors)
    # message_cropped.save("message.jpg")

    ref_cropped, next_y = crop_next_section(image, next_y + 10, reference_x_cors)
    # ref_cropped.save("ref.jpg")

    datetime_cropped, next_y = crop_next_section(image, next_y + 10, date_x_cors)
    # datetime_cropped.save("datetime.jpg")

    sender_cropped, next_y = crop_next_section(image, next_y + 10, from_x_cors)
    # sender_cropped.save("sender.jpg")

    receiver_cropped, next_y = crop_next_section(image, next_y + 10, from_x_cors)
    # receiver_cropped.save("receiver.jpg")

    amount_cropped = image.crop((amount_x_cors, next_y + 10, image.width, next_y + 100))
    # amount_cropped.save("amount.jpg")

    status = _format_string(_image_to_string(status_cropped)).rstrip()
    message = _image_to_string(message_cropped).replace("\n", " ").rstrip()
    reference = _format_string(_image_to_string(ref_cropped)).rstrip()
    date = _image_to_string(datetime_cropped).replace("\n", " ").rstrip()
    receiver = _image_to_string(receiver_cropped).replace("\n", " ").rstrip()
    sender = _format_string(_image_to_string(sender_cropped)).rstrip()
    amount = _format_string(_image_to_string(amount_cropped)).rstrip()

    blaz = BLAZ(
        status=status,
        message=message,
        reference=reference,
        date=datetime.strptime(date, '%d/%m/%Y %H:%M'),
        receiver=receiver,
        sender=sender,
        amount=amount,
    )

    try:
        blaz
    except Exception as e:
        print(e)
        raise HTTPException(422, "Could not process image")

    return blaz