import json
from typing import List, Any
from icecream import ic


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


def make_blocks():
    with open("../tests/succeeded.json", "r") as file:
        images_content = json.load(file)

    image = images_content["tests/APRIL 2022/APRIL 2022/30-04-2022/failing.jpg"]
    blocks = image["alto"]["Layout"]["Page"]["PrintSpace"]["ComposedBlock"]

    string_block_array: List[Any] = []

    for block in blocks:
        text_block = block["TextBlock"]
        _traverse(text_block, string_block_array)

        #
        #
        # try:
        #     text_lines = text_block["TextLine"]
        # except TypeError:
        #     string_block_array.append(text_block["String"])
        #     continue
        # # try:
        # # text_string_block = text_line["String"]
        #
        # if type(text_lines) is list:
        #     for line in text_lines:
        #         block = line["String"]
        #
        #         if type(block) is list:
        #             string_block_array.extend(block)
        #         else:
        #             string_block_array.append(block)
        # else:
        #     block = text_lines["String"]
        #     if type(block) is list:
        #         string_block_array.extend(block)
        #     else:
        #         string_block_array.append(block)

    blocks = {
        block["@CONTENT"]: block for block in
        string_block_array
    }

    with open("out.json", 'w') as f:
        json.dump(blocks, f, indent=4)


make_blocks()
