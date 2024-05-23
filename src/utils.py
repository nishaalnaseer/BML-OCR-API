from concurrent.futures import ProcessPoolExecutor
from typing import Callable

from fastapi import UploadFile


async def process_image_in_ppe(image: UploadFile, function: Callable):
    # Read the file contents
    contents = await image.read()
    with ProcessPoolExecutor() as executor:
        future = executor.submit(function, contents)
        text = future.result()

    return text
