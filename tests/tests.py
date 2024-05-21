import asyncio
import os

import aiofiles
from httpx import AsyncClient
import dotenv

dotenv.load_dotenv()
TESTS_SERVER = os.getenv('TESTS_SERVER')


class Failed:
    def __init__(self, path, info):
        self.path = path
        self.info = info

    def __repr__(self):
        return f"{self.path}: {self.info}"


async def request(path: str, failed):
    async with aiofiles.open(path, mode='rb') as f:
        contents = await f.read()
    files = {'image': contents}

    async with AsyncClient(timeout=30) as client:
        response = await client.post(
            url=f"{TESTS_SERVER}/blaz", files=files
        )

    print(f"{path} got status code ", end="")
    print(response.status_code)
    content = response.content.decode()
    print(content)

    if response.status_code != 201:
        failed.append(
            Failed(path=path, info=content)
        )


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


async def main():
    path = os.getenv("TESTS_ROOT")

    to_request = []
    failed = []

    traverse(path, to_request)

    while len(to_request) > 0:
        index = 0

        queue = []
        while len(to_request) > 0 and index != 3:
            path = to_request.pop()

            req = request(path, failed)

            queue.append(req)
            index += 1

        await asyncio.gather(*queue)

    for fail in failed:
        print(str(fail))
