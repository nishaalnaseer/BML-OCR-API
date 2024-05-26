import asyncio
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor
from io import BytesIO

import dotenv
from icecream import ic
from PIL import Image
from src.blob import make_blaz

dotenv.load_dotenv()
FEED = os.getenv('TESTS_FEED')
WORKERS = int(os.getenv('TESTS_WORKERS'))


def _test(path: str, image: Image):
    try:
        output = make_blaz(image)
        ic(output)
        return path, False, None
    except Exception as e:
        ic(e)
        path = path.replace("\\", " ")
        path = path.replace("/", " ")

        if image.mode == 'RGBA':
            # Create a new image with an opaque background (white)
            background = Image.new("RGB", image.size, (255, 255, 255))
            # Paste the RGBA image onto the background image
            background.paste(image, (0, 0), image)
            # Save the image as JPEG
            background.save(path, "JPEG")
        else:
            # If the image is not RGBA, save it directly
            image.save(path, "JPEG")

        return path, True, e


def traverse(path: str, images):
    content = os.listdir(path)

    for entry in content:
        new_path = f"{path}/{entry}"

        try:
            isdir = os.path.isdir(new_path)
        except FileNotFoundError:
            continue

        if isdir:
            traverse(new_path, images)
        else:
            root, ext = os.path.splitext(entry)

            ext = ext.lower()

            if ext == ".jpg" or ext == ".png":

                try:
                    with open(new_path, 'rb') as f:
                        image = Image.open(BytesIO(f.read()))
                except Exception:
                    continue

                images.update({new_path: image})


async def start(path, to_test, failed, succeeded):
    traverse(path, to_test)

    if len(to_test) == 0:
        ic(f"No images found in root path {path}, exiting")
        return

    ic(f"Going to test {len(to_test)} images")

    queue = {}
    loop = asyncio.get_event_loop()
    with ProcessPoolExecutor(max_workers=WORKERS) as executor:
        # Create a list of tasks to run in the executor

        for path, image in to_test.items():
            if len(queue) < WORKERS:
                queue[path] = image
            else:
                tasks = [
                    loop.run_in_executor(executor, _test, _path, _image)
                    for _path, _image in queue.items()
                ]

                # Await the completion of all tasks
                results = await asyncio.gather(*tasks)

                for result in results:
                    path, error, exc = result

                    if error:
                        failed[path] = str(exc)
                    else:
                        succeeded[path] = "SUCCESS"

                queue = {path: image}


async def retrieve_json():
    starting = time.time()
    to_request = {}
    failed = {}
    succeeded = {}
    starting_tests = len(to_request)

    try:
        await start(FEED, to_request, failed, succeeded)
    except asyncio.exceptions.CancelledError:
        pass

    ic(f"Passed: {len(succeeded)} Failed: {len(failed)}")

    with open("tests/succeeded.json", "w", ) as outfile:
        json.dump(succeeded, outfile, indent=2)

    with open("tests/failed.json", "w") as outfile:
        json.dump(failed, outfile, indent=2)

    total = time.time() - starting
    total_tests = len(failed) + len(succeeded)
    ic(f"Average time per request: {total / total_tests}")


def main():
    asyncio.run(retrieve_json())
