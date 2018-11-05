"""
This is the clients module and supports all the ReST actions for the
CLIENTS collection
"""

# System modules
from datetime import datetime
import uuid
import streaming

# 3rd party modules
from flask import make_response, abort


def create_timestamp():
    return datetime.now().strftime(("%Y-%m-%d %H:%M:%S"))


def create_uuid():
    return str(uuid.uuid4())


CLIENT_LIMIT = 3

# Data to serve with our API
TEST_CLIENT = {
    "name": "Bilbo Baggins",
    "uuid": create_uuid(),
    "in-ip": "0.0.0.0",
    "in-port": 5001,
    "out-ip": "0.0.0.0",
    "out-port": 5002,
    "timestamp": create_timestamp()
}

CLIENTS = {
    #TEST_CLIENT["uuid"]: TEST_CLIENT
}


def create_client(name, in_port, in_ip, out_port):
    """
    Helper function to create a client.
    :param name: name of the client
    :param in_ip: incoming stream ip
    :param in_port: incoming stream port
    :return: Returns the uuid and dict values of the created client.
    """
    global CLIENTS
    uuid = create_uuid()
    in_port = in_port if in_port > 0 else 5000 + 2*len(CLIENTS) + 1
    client = {
        "name": name,
        "uuid": uuid,
        "in-ip": in_ip if len(in_ip) > 0 else "0.0.0.0",
        "in-port": in_port,
        "out-ip": "0.0.0.0",
        "out-port": out_port if out_port > 0 else in_port + 1,
        "timestamp": create_timestamp()
    }
    streaming.create_loopback_pipeline(uuid, in_port, client["out-port"], client["in-ip"])
    return uuid, client


def read_all():
    """
    This function responds to a request for /api/clients
    with the complete lists of clients
    :return:        json string of list of clients
    """
    # Create the list of clients from our data
    return [CLIENTS[key] for key in sorted(CLIENTS.keys())]


def read_one(uuid):
    """
    This function responds to a request for /api/clients/{uuid}
    with one matching client from clients
    :param uuid:   uuid of client to find
    :return:        client matching uuid
    """
    # Does the client exist in clients?
    if uuid in CLIENTS:
        return CLIENTS[uuid]

    # otherwise, nope, not found
    else:
        abort(
            404,
            "Client with uuid {uuid} not found".format(uuid=uuid)
        )


def create(client):
    """
    This function creates a new client in the clients structure
    based on the passed in client data
    :param client:  client to create in clients structure
    :return:        201 on success, 406 on client exists
    """
    name = client.get("name", "")
    in_ip = client.get("in-ip", "")
    in_port = client.get("in-port", -1)
    out_port = client.get("out-port", -1)

    if len(CLIENTS) >= CLIENT_LIMIT:
        abort(
            406,
            "Client list already at maximum capacity"
        )
    else:
        uuid, client = create_client(name, in_port, in_ip, out_port)
        CLIENTS[uuid] = client
        return client


def update(uuid, client):
    """
    This function updates an existing client in the clients structure
    :param uuid:   last name of client to update in the clients structure
    :param client:  client to update
    :return:        updated client structure
    """
    # Does the client exist in clients?
    if uuid in CLIENTS:
        n = client.get("name", "")
        in_ip = client.get("in-ip", "")
        in_port = client.get("in-port", -1)
        out_port = client.get("out-port", -1)
        CLIENTS[uuid]["name"] = n if len(n) > 0 else CLIENTS[uuid]["name"]
        CLIENTS[uuid]["in-ip"] = in_ip if len(in_ip) > 0 else CLIENTS[uuid]["in-ip"]
        CLIENTS[uuid]["in-port"] = in_port if in_port > 0 else CLIENTS[uuid]["in-port"]
        CLIENTS[uuid]["out-port"] = out_port if out_port > 0 else CLIENTS[uuid]["out-port"]
        CLIENTS[uuid]["timestamp"] = create_timestamp()
        return CLIENTS[uuid]

    # otherwise, nope, that's an error
    else:
        abort(
            404,
            "Client with uuid {uuid} not found".format(uuid=uuid)
        )


def delete(uuid):
    """
    This function deletes a client from the clients structure
    :param uuid:   uuid of client to delete
    :return:        200 on successful delete, 404 if not found
    """
    # Does the client to delete exist?
    if uuid in CLIENTS:
        name = CLIENTS[uuid]["name"]
        del CLIENTS[uuid]
        if streaming.remove_pipeline(uuid):
            return make_response(
                "{name} successfully deleted at uuid={uuid}".format(name=name, uuid=uuid), 200
            )
        else:
            abort(
                406,
                "could not delete {name} at uuid={uuid}".format(name=name, uuid=uuid)
            )

    # Otherwise, nope, client to delete not found
    else:
        abort(
            404,
            "Client with uuid {uuid} not found".format(uuid=uuid)
        )