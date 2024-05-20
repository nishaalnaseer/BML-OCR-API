import io
from concurrent.futures import ProcessPoolExecutor

from PIL import Image
from fastapi import FastAPI, HTTPException, UploadFile, File
from pytesseract import pytesseract

app = FastAPI()


def _process_image(contents: bytes) -> str | None:
    # Convert to a PIL image
    image = Image.open(io.BytesIO(contents))
    text = pytesseract.image_to_string(image)

    # sample =/\n\nThank you. Transfer transaction is successful.\n\n1200\n\nMVR\n\nStatus SUCCESS\nThank you.
    # Transfer transaction is\n\nMessage\nsuccessful.\nReference BLAZ123\nTransaction date 12/02/2024 20:19\nFrom
    # AHMD.N.NASEER\n. wwhereOs\n° 7730000123456\nAmount MVR 1234.00\n\nBank of Maldives\n
    tokens = text.split()

    for token in tokens:
        if token[:4] == "BLAZ":
            return token

    return None


@app.post("/ocr")
async def image_to_string(image: UploadFile = File(...)):
    # Read the file contents
    contents = await image.read()
    with ProcessPoolExecutor() as executor:
        future = executor.submit(_process_image, contents)
        text = future.result()

    if not text:
        raise HTTPException(500, "Something went wrong while processing image!")

    return {"text": text}
