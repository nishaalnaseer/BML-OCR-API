import asyncio
import json
import os

import aiofiles
from httpx import AsyncClient
import dotenv
from icecream import ic

dotenv.load_dotenv()
TESTS_SERVER = os.getenv('TESTS_SERVER')


class Failed:
    def __init__(self, path, info):
        self.path = path
        self.info = info

    def __repr__(self):
        return f"{self.path}: {self.info}"


async def request(path: str, failed, success):
    async with aiofiles.open(path, mode='rb') as f:
        contents = await f.read()
    files = {'image': contents}

    async with AsyncClient(timeout=30) as client:
        response = await client.post(
            url=f"{TESTS_SERVER}/blaz", files=files
        )

    status_code = response.status_code
    ic(f"{path} got status code {status_code}")
    content = response.content.decode()

    if status_code != 201:
        failed[path] = content
    else:
        success[path] = json.loads(content)


def traverse(path: str, paths):
    content = os.listdir(path)

    for entry in content:
        new_path = f"{path}/{entry}"

        try:
            isdir = os.path.isdir(new_path)
        except FileNotFoundError:
            continue

        if isdir:
            traverse(new_path, paths)
        else:
            root, ext = os.path.splitext(entry)

            ext = ext.lower()

            if ext == ".jpg" or ext == ".png":
                paths.append(new_path)


async def start_reqs(path, to_request, failed, succeeded):
    traverse(path, to_request)

    ic(f"Going to test {len(to_request)} images")

    while len(to_request) > 0:
        index = 0

        queue = []
        while len(to_request) > 0 and index != 3:
            path = to_request.pop()

            req = request(path, failed, succeeded)

            queue.append(req)
            index += 1

        await asyncio.gather(*queue)


async def retrieve_json():
    path = os.getenv("TESTS_ROOT")

    to_request = []
    failed = {}
    succeeded = {}

    try:
        await start_reqs(path, to_request, failed, succeeded)
    except asyncio.exceptions.CancelledError:
        pass

    ic(f"Passed: {len(succeeded)} Failed: {len(failed)}")

    with open("tests/succeeded.json", "w",) as outfile:
        json.dump(succeeded, outfile, indent=2)

    with open("tests/failed.json", "w") as outfile:
        json.dump(failed, outfile, indent=2)


async def main():
    await retrieve_json()
