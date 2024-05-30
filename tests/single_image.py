from io import BytesIO

from icecream import ic
import os
from src.blob import make_blaz
from PIL import Image


def main():

    files = os.listdir("tests/data/")

    for file in files:
        file_path = f"tests/data/{file}"
        ic(file_path)

        try:

            with open(file_path, "rb") as f:
                _bytes = BytesIO(f.read())
            image = Image.open(_bytes)
            result = make_blaz(image)
            ic(result)
        except Exception as e:
            ic(f"{file_path}: {e}")

        break

