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
from database.api import ImageApi
from database.base import engine


def create_timestamp():
    return datetime.now().strftime(("%Y-%m-%d %H:%M:%S"))


def create_uuid():
    return str(uuid.uuid4())


def response_image_dict(img_dict):
    return {
        "created_datetime": img_dict["created_datetime"],
        "name": img_dict["name"],
        "uuid": img_dict["uuid"]
    }


def create_image(name):
    """
    Helper function to prepare image upload.
    :param name: name of the image
    :return: Returns dict values of the created image.
    """
    new_uuid = create_uuid()

    i_api = ImageApi(bind=engine)
    i_api.open()
    img = i_api.add_image_file(uuid=new_uuid, name=name)
    i_api.commit()
    img_dict = img.as_dict()
    i_api.close()

    return img_dict


def remove_image(uuid):
    """
    Helper function for delete
    :param uuid: identifier for the image to be removed
    :return: success of removal
    """
    i_api = ImageApi(bind=engine)
    i_api.open()
    img = i_api.get_image_file(uuid)
    if img is not None:
        if img.filename is not None:
            if os.path.exists(img.filename):
                os.remove(img.filename)
        i_api.delete(img)
        i_api.commit()
        return True
    i_api.close()
    return False


def remove_all():
    """
    helper function to delete all images of current session
    """
    i_api = ImageApi(bind=engine)
    i_api.open()

    images = i_api.get_image_files()
    if len(images) == 0:
        i_api.close()
        return

    for img in images:
        if img.filename is not None:
            if os.path.exists(img.filename):
                os.remove(img.filename)
        i_api.delete(img)
    i_api.commit()
    i_api.close()


def read_all():
    """
    This function responds to a request for /api/images
    with the complete lists of images
    :return:        json string of list of images
    """
    i_api = ImageApi(bind=engine)
    i_api.open()
    res = [
        response_image_dict(img.as_dict())
        for img in i_api.get_image_files()
    ]
    i_api.close()

    # Create the list of images from our data
    return res


def create(image):
    """
    This function prepares the image upload on the server side.
    Data can only be uploaded if the server created an upload path (see fill).
    :param image:  image to create in images structure
    :return:        201 on success, 406 on TODO
    """
    name = image.get("name", "")
    return response_image_dict(create_image(name))


def fill(uuid, data):
    """
    This function stores the uploaded data to an image reserved by create(...)
    :param data: uploaded image data
    :param uuid: identifier for the image
    :return: 201 on success, 404 on image not found
    """
    i_api = ImageApi(bind=engine)
    i_api.open()
    img = i_api.get_image_file(uuid)
    name = ""
    if img is not None:
        img.mimetype = data.mimetype
        img.filename = "SERVER_DATA/"+str(uuid)+data.filename
        data.save(img.filename)
        name = img.name
        i_api.commit()
    else:
        i_api.close()
        abort(
            404,
            "Image with uuid {uuid} not found".format(uuid=uuid)
        )

    return make_response(
        "{name} successfully filled at uuid={uuid}".format(name=name, uuid=uuid), 200
    )


def read(uuid):
    i_api = ImageApi(bind=engine)
    i_api.open()
    img = i_api.get_image_file(uuid)
    if img is None or img.filename is None:
        i_api.close()
        abort(
            404,
            "Image with uuid {uuid} not found".format(uuid=uuid)
        )
    filename = img.filename
    i_api.close()
    return send_file(filename)


def delete(uuid):
    """
    This function deletes a image from the images structure
    :param uuid:   uuid of image to delete
    :return:        200 on successful delete, 404 if not found
    """
    if remove_image(uuid):
        return make_response(
            "Successfully deleted image at uuid={uuid}".format(uuid=uuid), 200
        )
    else:
        abort(
            404,
            "Image with uuid {uuid} not found".format(uuid=uuid)
        )