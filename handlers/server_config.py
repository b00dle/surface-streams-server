"""
This is the server-config module and supports all the ReST actions for the
configuration of the SurfaceStreams server config,
including merged-stream-width & merged-stream-height.
"""

# System modules
import video_mixing

# 3rd party modules
from flask import make_response, abort


def read_all():
    """
    This function responds to a request for /api/server-config
    with the complete list of Surface Streams server config parameters
    :return:        json string of config values
    """
    return {
        "merged-stream-width": video_mixing.MERGED_STREAM_WIDTH,
        "merged-stream-height": video_mixing.MERGED_STREAM_HEIGHT
    }


def update(config):
    """
    This function updates an existing client in the clients structure
    :param config: updated SurfaceStreams server config
    :return:
    """
    width = config.get("merged-stream-width", -1)
    height = config.get("merged-stream-height", -1)

    # Does the client exist in clients?
    if width > 0 and height > 0:
        video_mixing.MERGED_STREAM_WIDTH = width
        video_mixing.MERGED_STREAM_HEIGHT = height
        video_mixing.update_pipelines()
        return make_response("Update the current SurfaceStreams server config", 200)
    # otherwise, nope, that's an error
    else:
        abort(404, "not all arguments supplied.")
