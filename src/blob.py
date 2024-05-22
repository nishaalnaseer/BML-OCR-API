import json

from icecream import ic


def make_blocks():
    with open("../tests/succeeded.json", "r") as file:
        images_content = json.load(file)

    image = images_content["tests/APRIL 2022/APRIL 2022/30-04-2022/failing.jpg"]
    blocks = image["alto"]["Layout"]["Page"]["PrintSpace"]["ComposedBlock"]

    for block in blocks:
        text_block = block["TextBlock"]
        text_line = text_block["TextLine"]

        try:
            ic(text_line["String"])
        except TypeError:
            ic(text_line)


make_blocks()
