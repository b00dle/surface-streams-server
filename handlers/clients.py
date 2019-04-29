"""
This is the clients module and supports all the ReST actions for the
CLIENTS collection
"""

# System modules
from datetime import datetime
import uuid
import video_mixing

# 3rd party modules
from flask import make_response, abort
from database.api import ClientApi
from database.base import engine


def create_timestamp():
    return datetime.now().strftime(("%Y-%m-%d %H:%M:%S"))


def create_uuid():
    return str(uuid.uuid4())


CLIENT_LIMIT = 3


def create_client(name, video_src_port, ip, video_sink_port, streaming_protocol, tuio_port, mixing_mode):
    """
    Helper function to create a client.
    :param name: name of the client
    :param ip: incoming stream ip
    :param video_src_port: incoming stream port
    :return: Returns the uuid and dict values of the created client.
    """
    c_api = ClientApi(bind=engine)
    c_api.open()
    num_clients = len(c_api.get_clients())

    new_uuid = create_uuid()
    ip = ip if len(ip) > 0 else "0.0.0.0"
    video_src_port = video_src_port if video_src_port > 0 else 5001 + 3 * num_clients + 1
    video_sink_port = video_sink_port if video_sink_port > 0 else video_src_port + 1
    tuio_port = tuio_port if tuio_port > 0 else video_sink_port + 1

    c = c_api.add_client(
        new_uuid, name, ip if len(ip) > 0 else "0.0.0.0",
        video_src_port, video_sink_port, streaming_protocol, tuio_port,
        mixing_mode
    )
    c_api.commit()
    res = c.as_dict()
    c_api.close()

    video_mixing.update_pipelines()
    return res


def read_all():
    """
    This function responds to a request for /api/clients
    with the complete lists of clients
    :return:        json string of list of clients
    """
    c_api = ClientApi(bind=engine)
    c_api.open()
    res = [c.as_dict() for c in c_api.get_clients()]
    c_api.close()
    return res


def read_one(uuid):
    """
    This function responds to a request for /api/clients/{uuid}
    with one matching client from clients
    :param uuid:   uuid of client to find
    :return:        client matching uuid
    """
    c_api = ClientApi(bind=engine)
    c_api.open()
    c = c_api.get_client(uuid)
    if c is None:
        c_api.close()
        abort(
            404,
            "Client with uuid {uuid} not found".format(uuid=uuid)
        )
    res = c.as_dict()
    c_api.close()
    return res


def create(client):
    """
    This function creates a new client in the clients structure
    based on the passed in client data
    :param client:  client to create in clients structure
    :return:        201 on success, 406 on client exists
    """
    c_api = ClientApi(bind=engine)
    c_api.open()
    len_clients = len(c_api.get_clients())
    c_api.close()

    if len_clients > CLIENT_LIMIT:
        abort(
            406,
            "Client list already at maximum capacity"
        )

    name = client.get("name", "")
    ip = client.get("ip", "")
    video_src_port = client.get("video_src_port", -1)
    video_sink_port = client.get("video_sink_port", -1)
    video_protocol = client.get("video_protocol", "jpeg")
    tuio_sink_port = client.get("tuio_sink_port", -1)
    mixing_mode = client.get("mixing_mode", "other")

    return create_client(name, video_src_port, ip, video_sink_port,
                         video_protocol, tuio_sink_port, mixing_mode)


def update(uuid, client):
    """
    This function updates an existing client in the clients structure
    :param uuid:   last name of client to update in the clients structure
    :param client:  client to update
    :return:        updated client structure
    """
    c_api = ClientApi(bind=engine)
    c_api.open()
    c = c_api.get_client(uuid)
    if c is None:
        c_api.close()
        abort(
            404,
            "Client with uuid {uuid} not found".format(uuid=uuid)
        )

    n = client.get("name", "")
    ip = client.get("ip", "")
    video_src_port = client.get("video_src_port", -1)
    video_sink_port = client.get("video_sink_port", -1)
    tuio_sink_port = client.get("tuio_sink_port", -1)
    mixing_mode = client.get("mixing_mode", "other")

    c.name = n if len(n) > 0 else c.name
    c.ip = ip if len(ip) > 0 else c.ip
    c.video_src_port = video_src_port if video_src_port > 0 else c.video_src_port
    c.video_sink_port = video_sink_port if video_sink_port > 0 else c.video_sink_port
    c.tuio_sink_port = tuio_sink_port if tuio_sink_port > 0 else c.tuio_sink_port
    c.mixing_mode = mixing_mode
    c.created_datetime = datetime.now()

    c_api.commit()
    res = c.as_dict()
    c_api.close()

    video_mixing.update_pipelines()

    return res


def delete(uuid):
    """
    This function deletes a client from the clients structure
    :param uuid:   uuid of client to delete
    :return:        200 on successful delete, 404 if not found
    """
    c_api = ClientApi(bind=engine)
    c_api.open()
    c = c_api.get_client(uuid)
    if c is None:
        abort(
            404,
            "Client with uuid {uuid} not found".format(uuid=uuid)
        )
        c_api.close()
    name = c.name
    c_api.delete(c)
    c_api.commit()
    c_api.close()

    if video_mixing.update_pipelines():
        return make_response(
            "{name} successfully deleted at uuid={uuid}".format(name=name, uuid=uuid), 200
        )
    else:
        abort(
            406,
            "could not delete {name} at uuid={uuid}".format(name=name, uuid=uuid)
        )