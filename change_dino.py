from PIL import Image
from bs4 import BeautifulSoup
from pak_utils import UnpackFileIntoDirectory, PackDirectoryIntoFile
import shutil
import os

from consts import RESOURCES_FILE, RESOURCE_FOLDER, DINO, OFFSETS, NEW_RESOURCES_FILE, RESOURCES_LOCATION
from utils import load_source_image, save_new_source_image, _pil_image_to_base64


def change_dino_to_avatar_globally(avatar_image_name, resources_location=RESOURCES_LOCATION):
    shutil.copy(resources_location, os.path.join('.', RESOURCES_FILE))
    change_dino_to_avatar_locally(avatar_image_name)
    os.remove(resources_location)
    shutil.copy(os.path.join('.', NEW_RESOURCES_FILE), resources_location)
    os.remove(NEW_RESOURCES_FILE)
    os.remove(RESOURCES_FILE)

def change_dino_to_avatar_locally(avatar_image_name, resources_file=RESOURCES_FILE, new_resources_file=NEW_RESOURCES_FILE):
    UnpackFileIntoDirectory(resources_file, RESOURCE_FOLDER)
    source_image = load_source_image()
    avatar = Image.open(avatar_image_name)
    new_source_image = _paste_avatar_on_source_image(source_image, avatar)
    new_source_image_base64 = _pil_image_to_base64(new_source_image)
    save_new_source_image(new_source_image_base64)
    PackDirectoryIntoFile(RESOURCE_FOLDER, new_resources_file)
    shutil.rmtree(RESOURCE_FOLDER)

def _paste_avatar_on_source_image(source, avatar):
    standing_avatar = avatar.resize((DINO["WIDTH"], DINO["HEIGHT"]))
    ducking_avatar = avatar.resize((DINO["WIDTH_DUCK"], DINO["HEIGHT_DUCK"]))
    _paste_standing_image(source, standing_avatar)
    _paste_ducking_image(source, ducking_avatar)
    return source

def _paste_standing_image(source, img_to_paste):
    for offset in OFFSETS["STANDING"]:
        box = DINO["LEFT"] + offset, DINO["TOP"], DINO["LEFT"] + DINO["WIDTH"] + offset, DINO["TOP"] + DINO['HEIGHT']
        source.paste(img_to_paste, box)

def _paste_ducking_image(source, img_to_paste):
    for offset in OFFSETS["DUCKING"]:
        box = DINO["LEFT"] + offset, DINO["TOP"] + (DINO["HEIGHT"] - DINO["HEIGHT_DUCK"]), DINO["LEFT"] + DINO["WIDTH_DUCK"] + offset, DINO["TOP"] + DINO['HEIGHT']
        source.paste(img_to_paste, box)

if __name__ == "__main__":
    change_dino_to_avatar_globally('avatar.png')









