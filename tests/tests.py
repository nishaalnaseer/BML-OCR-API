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
WORKERS = 6  # int(os.getenv('TESTS_WORKERS'))


async def _test(path: str, failed, success, image: Image):
    with ProcessPoolExecutor() as executor:
        future = executor.submit(make_blaz, *[image])

        try:
            result = future.result()
            success[path] = "SUCCESS"
            ic(result)
            return result
        except Exception as e:
            ic(e)
            failed[path] = str(e)
            path = path.replace("\\", " ")
            path = path.replace("/", " ")
            image.save(f"tests/failed_images/{path}")


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

    ic(f"Going to test {len(to_test)} images")

    queue = {}
    for path, image in to_test.items():
        if len(queue) < WORKERS:
            queue[path] = image
        else:
            reqs = [
                _test(_path, failed, succeeded, _image)
                for _path, _image in queue.items()
            ]
            await asyncio.gather(*reqs)
            queue = {path: image}


async def retrieve_json():
    starting = time.time()
    to_request = {}
    failed = {}
    succeeded = {}

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
