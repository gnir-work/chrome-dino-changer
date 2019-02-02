DINO = {
    "LEFT": 848,
    "TOP": 2,
    "HEIGHT": 47,
    "WIDTH": 44,
    "WIDTH_DUCK": 59,
    "HEIGHT_DUCK": 30,
}
OFFSETS = {
    "STANDING": [0, 44, 88, 132, 176, 220],
    "DUCKING": [264, 323]
}

RESOURCES_FILE = "resources.pak"
NEW_RESOURCES_FILE = "new_{}".format(RESOURCES_FILE)
RESOURCE_FOLDER = "resources"
SOURCE_FILE = "17033"
IMAGE_SOURCE_BASE64_MAGIC = "data:image/png;base64,"
# The offset of the base64 data for the start of the src attribute contents
iMAGE_SOURCE_OFFSET = len(IMAGE_SOURCE_BASE64_MAGIC)
IMAGE_SOURCE_ID = "offline-resources-1x"
RESOURCES_LOCATION = r"C:\Program Files (x86)\Google\Chrome\Application\72.0.3626.81\resources.pak"