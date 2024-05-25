from icecream import ic

from tests.single_image import main
import time

if __name__ == '__main__':

    _time = time.time()
    for _ in range(100):
        main()

    ic(time.time() - _time)
