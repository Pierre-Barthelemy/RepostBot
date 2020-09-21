import re
from io import BytesIO

import aiohttp
import respostbot.image as image
import numpy
import PIL
from PIL import Image, ImageFile

Image.MAX_IMAGE_PIXELS = 1000000000
ImageFile.LOAD_TRUNCATED_IMAGES = True

CONNEXION_TIMEOUT = 5
TOTAL_DOWNLOAD_TIMEOUT = 120


async def resize(img, size):
    # Preserve aspect ratio
    x, y = img.size
    if x > size[0]:
        y = int(max(y * size[0] / x, 1))
        x = int(size[0])
    if y > size[1]:
        x = int(max(x * size[1] / y, 1))
        y = int(size[1])
    size = x, y
    if size == img.size:
        return
    img.draft(None, size)
    im = img.resize(size, Image.NEAREST)
    img.im = im.im
    img.mode = im.mode
    img._size = size
    img.readonly = 0
    img.pyaccess = None


async def dl_image(link):
    try:
        timeout = aiohttp.ClientTimeout(connect=CONNEXION_TIMEOUT, total=TOTAL_DOWNLOAD_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(link) as resp:
                if resp.status == 200:
                    return await resp.read()
                return None
    except:
        return None


async def image_hash(link, author):
    if (re.search(r'(?:http\:|https\:)?\/\/.*\.(?:png|jpg)', link) != None):
        try:
            img = Image.open(BytesIO(await dl_image(link)))
        except (PIL.Image.DecompressionBombError, OSError):
            return None, None
        w = img.size[0]
        h = img.size[1]
        if w > 1000 or h > 1000:
            while w > 1000 and h > 1000:
                h = h / 2
                w = w / 2
            await resize(img, (int(w), int(h)))
        if img.mode == "LA":
            img = img.convert("L")
        imageHash = image.Image(numpy.asarray(img))
        imageHash.setLink(link)
        return imageHash, author


def add_in_tree(tree, value):
    return tree.add(value)
