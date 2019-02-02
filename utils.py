import cStringIO
from PIL import Image
from os import path
from bs4 import BeautifulSoup
import base64

from consts import RESOURCES_FILE, RESOURCE_FOLDER, IMAGE_SOURCE_ID, SOURCE_FILE, iMAGE_SOURCE_OFFSET, IMAGE_SOURCE_BASE64_MAGIC


def _get_dino_source_bs4():
    source = ''
    with open(path.join(RESOURCE_FOLDER, SOURCE_FILE), 'rb') as source_file:
        source = source_file.read()
    return BeautifulSoup(source, features="html.parser")


def load_source_image():
    source_bs = _get_dino_source_bs4()
    source_image = source_bs.find("img", {"id": IMAGE_SOURCE_ID})
    source_image_data_base64 = source_image.get('src')[iMAGE_SOURCE_OFFSET:]
    source_image_data = source_image_data_base64.decode('base64')
    return Image.open(cStringIO.StringIO(source_image_data))


def save_new_source_image(new_image_data):
    source_bs = _get_dino_source_bs4()
    source_image = source_bs.find("img", {"id": IMAGE_SOURCE_ID})
    source_image['src'] = "{}{}".format(
        IMAGE_SOURCE_BASE64_MAGIC, new_image_data)
    with open(path.join(RESOURCE_FOLDER, SOURCE_FILE), 'wb') as source_file:
        source_file.write(str(source_bs))


def _pil_image_to_base64(image):
    buffer = cStringIO.StringIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue())
