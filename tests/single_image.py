from io import BytesIO

from icecream import ic

from src.blob import make_blaz
from PIL import Image


def main():
    with open('tests/remarks.jpg', "rb") as f:
        _bytes = BytesIO(f.read())
    image = Image.open(_bytes)
    result = make_blaz(image)
    # ic(result)
