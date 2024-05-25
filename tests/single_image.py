from src.blob import make_blaz
from PIL import Image


async def main():
    image = Image.open('tests/remarks.jpg')
    make_blaz(image)
