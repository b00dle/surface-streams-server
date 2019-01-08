"""
This is the images module and supports all the ReST actions for the
CLIENTS collection
"""

# System modules
from datetime import datetime
import uuid
import os

# 3rd party modules
from flask import make_response, abort, send_file


def create_timestamp():
    return datetime.now().strftime(("%Y-%m-%d %H:%M:%S"))


def create_uuid():
    return str(uuid.uuid4())


# Data to serve with our API
TEST_IMAGE = {
    "name": "EMPTY IMAGE",
    "uuid": create_uuid(),
    "timestamp": create_timestamp()
}


IMAGES = {
    #TEST_IMAGE["uuid"]: TEST_IMAGE
}

IMAGE_DATA = {}


def create_image(name):
    """
    Helper function to prepare image upload.
    :param name: name of the image
    :return: Returns the uuid and dict values of the created image.
    """
    new_uuid = create_uuid()
    image = {
        "name": name,
        "uuid": new_uuid,
        "timestamp": create_timestamp()
    }
    IMAGES[new_uuid] = image
    return new_uuid


def remove_image(uuid):
    """
    Helper function for delete
    :param uuid: identifier for the image to be removed
    :return: success of removal
    """
    if uuid in IMAGES:
        del IMAGES[uuid]
        if uuid in IMAGE_DATA:
            fname = IMAGE_DATA[uuid]["filename"]
            del IMAGE_DATA[uuid]
            if os.path.exists(fname):
                os.remove(fname)
        return True
    else:
        return False


def remove_all():
    """
    helper function to delete all images of current session
    """
    ids = [i for i in IMAGES.keys()]
    for id in ids:
        remove_image(id)


def read_all():
    """
    This function responds to a request for /api/images
    with the complete lists of images
    :return:        json string of list of images
    """
    # Create the list of images from our data
    return [IMAGES[key] for key in sorted(IMAGES.keys())]


def create(image):
    """
    This function prepares the image upload on the server side.
    Data can only be uploaded if the server created an upload path (see fill).
    :param image:  image to create in images structure
    :return:        201 on success, 406 on TODO
    """
    name = image.get("name", "")
    uuid = create_image(name)
    return IMAGES[uuid]


def fill(uuid, data):
    """
    This function stores the uploaded data to an image reserved by create(...)
    :param data: uploaded image data
    :param uuid: identifier for the image
    :return: 201 on success, 404 on image not found
    """
    if uuid not in IMAGES:
        abort(
            404,
            "Image with uuid {uuid} not found".format(uuid=uuid)
        )

    IMAGE_DATA[uuid] = {
        "filename": "SERVER_DATA/"+str(uuid)+data.filename,
        "mimetype": data.mimetype
    }
    data.save(IMAGE_DATA[uuid]["filename"])

    return make_response(
        "{name} successfully filled at uuid={uuid}".format(name=IMAGES[uuid]["name"], uuid=uuid), 200
    )


def read(uuid):
    if uuid not in IMAGES or uuid not in IMAGE_DATA:
        abort(
            404,
            "Image with uuid {uuid} not found".format(uuid=uuid)
        )
    return send_file(IMAGE_DATA[uuid]["filename"])


def delete(uuid):
    """
    This function deletes a image from the images structure
    :param uuid:   uuid of image to delete
    :return:        200 on successful delete, 404 if not found
    """
    # Does the image to delete exist?
    if uuid in IMAGES:
        name = IMAGES[uuid]["name"]
        if remove_image(uuid):
            return make_response(
                "{name} successfully deleted at uuid={uuid}".format(name=name, uuid=uuid), 200
            )
    # Otherwise, nope, image to delete not found
    abort(
        404,
        "Image with uuid {uuid} not found".format(uuid=uuid)
    )