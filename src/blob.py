import random
from collections import defaultdict
from typing import List, Any, Callable, Tuple
import os
import xmltodict
from PIL import Image
from icecream import ic
from pytesseract import pytesseract

from src.models import *

if os.name == "nt":
    pytesseract.tesseract_cmd = os.getenv("TESSERACT_PATH")


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
        # if type is lise
        for _obj in obj:
            _traverse(_obj, array)
    except KeyError:
        # if the traverse dict keyerrors
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


def is_black(_input: tuple[int]):
    for x in _input:
        if x < 35:
            return False

    return True


def is_bg_white(image: Image) -> True:
    white = 0
    black = 0
    for x in range(500):
        x_cor = random.randint(0, image.width - 1)
        y_cor = random.randint(0, image.height - 1)

        pixel = image.getpixel((x_cor, y_cor))
        if is_white(pixel):
            white += 1
        elif is_black(pixel):
            black += 1

    return white > black


def get_next_gray_line(
        img: Image, start_cors: tuple[int, int],
        detector: Callable[[Tuple[int]], bool]
) -> tuple[int, int]:
    start_x, start_y = start_cors[0], start_cors[1]

    for y in range(start_y, img.height):
        cors = (134, y,)
        color = img.getpixel(cors)

        if not detector(color):
            flag = True
            for x in range(start_x, 50 + start_x):
                new_color = img.getpixel((x, y))
                if detector(new_color):
                    flag = False
                    break

            if flag:
                return start_x, y,

    raise GrayLineNotFound()


def _get_next_section(
        img: Image, y_start: int, x_crop: int,
        blocks: dict[str, any], detector: Callable[[Tuple[int]], bool]
) -> tuple[str, int]:
    _end = get_next_gray_line(img, (134, y_start + 10,), detector)
    y_end = _end[1]

    _string = _get_string(blocks, y_start + 10, y_end, x_crop)
    return _string, y_end


def get_x_crop_cors(block: dict) -> int:
    return int(block["@HPOS"]) + int(block["@WIDTH"]) + 10


def _format_string(string: str):
    return string.replace("\n", "").replace(" ", "")


def _append_string(
        _object: dict | list,
        y_upper: int,
        y_lower: int,
        x_cors: int,
        content: list
):
    y_value = int(_object["@VPOS"])
    x_value = int(_object["@HPOS"]) + int(_object["@WIDTH"])
    if y_lower > y_value > y_upper and x_cors < x_value:
        content.append(_object)


def _get_string(objects: dict, y_upper: int, y_lower: int, x_cors: int):
    content = []

    for _object in objects.values():
        for __object in _object:
            _append_string(__object, y_upper, y_lower, x_cors, content)

    strings = [c["@CONTENT"] for c in content]
    return " ".join(strings)


def make_blaz(image: Image) -> BLAZ | dict:
    xml = pytesseract.image_to_alto_xml(image)
    image_content = xmltodict.parse(xml)

    blocks = image_content["alto"]["Layout"]["Page"]["PrintSpace"]["ComposedBlock"]

    string_block_array: List[Any] = []

    if is_bg_white(image):
        detector = is_white
    else:
        detector = is_black

    for block in blocks:
        text_block = block["TextBlock"]
        _traverse(text_block, string_block_array)

    blocks = defaultdict(list)
    for block in string_block_array:
        _key = block["@CONTENT"]
        ic(block)
        blocks[_key].append(block)

    key_blocks: [str, dict] = {
        value["@CONTENT"]: value
        for value in string_block_array if 100 > int(value["@HPOS"])
    }

    # get where to start cropping from the x axis
    status_block = key_blocks["Status"]
    message_block = key_blocks["Message"]
    reference_block = key_blocks["Reference"]
    date_block = blocks["date"][0]
    from_block = key_blocks["From"]
    amount_block = key_blocks["Amount"]
    status_x_cors = get_x_crop_cors(status_block)
    message_x_cors = get_x_crop_cors(message_block)
    reference_x_cors = get_x_crop_cors(reference_block)
    date_x_cors = get_x_crop_cors(date_block)
    from_x_cors = get_x_crop_cors(from_block)
    amount_x_cors = get_x_crop_cors(amount_block)

    # crop status block
    status_start = int(status_block["@VPOS"]) - 10
    status_end = status_start + int(status_block["@HEIGHT"]) + 5 + 10

    # ic(blocks)
    status = _get_string(blocks, status_start, status_end, status_x_cors)
    message_section_start = status_end + 10
    start_x = 134

    message_start = get_next_gray_line(
        image, (start_x, message_section_start,), detector
    )
    message, message_end = _get_next_section(
        image, message_start[1] + 10, message_x_cors, blocks, detector
    )
    reference, ref_end = _get_next_section(
        image, message_end + 10, reference_x_cors, blocks, detector
    )
    _datetime, datetime_end = _get_next_section(
        image, ref_end + 10, date_x_cors, blocks, detector
    )
    sender, sender_end = _get_next_section(
        image, datetime_end + 10, from_x_cors, blocks, detector
    )
    receiver, receiver_end = _get_next_section(
        image, sender_end + 10, from_x_cors, blocks, detector
    )
    amount, amount_end = _get_next_section(
        image, receiver_end + 10, amount_x_cors, blocks, detector
    )

    try:
        remarks_block = key_blocks["Remarks"]
        remarks_x_crop = get_x_crop_cors(remarks_block)
        remarks, remarks_end = _get_next_section(
            image, amount_end + 10, remarks_x_crop, blocks, detector
        )
    except KeyError:
        remarks = None
        pass

    status = status,
    message = message,
    reference = reference.replace(" ", ""),
    date = datetime.strptime(_datetime, '%d/%m/%Y %H:%M'),
    receiver = receiver,
    sender = sender,
    amount = amount,
    remarks = remarks

    ic(status)
    ic(message)
    ic(reference)
    ic(datetime)
    ic(receiver)
    ic(sender)
    ic(amount)
    ic(remarks)

    blaz = BLAZ(
        status=status,
        message=message,
        reference=reference,
        date=date,
        receiver=receiver,
        sender=sender,
        amount=amount,
        remarks=remarks
    )

    # ic(return_dict)
    # if return_dict:
    #     return blaz.model_dump()
    # else:
    return blaz
