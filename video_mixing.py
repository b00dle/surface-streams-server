import threading
import gi
import os
from core.gstreamer.udp_video_mixer import UdpVideoMixer
from database.api import ClientApi
from database.base import engine
gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "3.0")
gi.require_version("GstVideo", "1.0")
from gi.repository import Gst, Gtk, GObject


PIPELINES = {}

THREAD_RUNNING = False

DEBUG_GRAPH_DIR = os.getcwd()

MERGED_STREAM_WIDTH = 640

MERGED_STREAM_HEIGHT = 360

os.environ["GST_DEBUG_DUMP_DOT_DIR"] = DEBUG_GRAPH_DIR
os.putenv('GST_DEBUG_DUMP_DIR_DIR', DEBUG_GRAPH_DIR)


def _run_thread():
    """
    Function executed on separate thread,
    to keep GStreamer MainLoop and Server running concurrently.
    :return:
    """
    GObject.threads_init()
    Gst.init(None)
    Gtk.main()


def _ensure_gtk_thread_running():
    """
    Checks if GStreamer MainLoop thread is running
    and runs it if not.
    :return:
    """
    global THREAD_RUNNING
    if not THREAD_RUNNING:
        gtk_main = threading.Thread(target=_run_thread)
        gtk_main.start()
        THREAD_RUNNING = True


def create_multi_mixing_pipeline(mode="other"):
    """
    Creates a SurfaceStream video mixing pipeline.
    :param CLIENTS: client dicts denoting connection and stream descriptive data.
    :param mode: use 'other' to only merge streams of other clients connected for each client.
    use 'all' to merge alle streams.
    :return:
    """
    global MERGED_STREAM_WIDTH, MERGED_STREAM_HEIGHT

    clear_pipelines()
    _ensure_gtk_thread_running()

    c_api = ClientApi(bind=engine)
    c_api.open()
    clients = c_api.get_clients()
    print("################# CREATING MULTI MIXING PIPELINE")
    mixer = UdpVideoMixer(
        [c.as_dict() for c in clients],
        default_mode=mode,
        width=MERGED_STREAM_WIDTH,
        height=MERGED_STREAM_HEIGHT
    )
    i = 0
    uuid = ""
    for c in clients:
        mixer.set_in_port(c.video_src_port, i)
        mixer.set_out_address(c.ip, i)
        mixer.set_out_port(c.video_sink_port, i)
        uuid = c.uuid
        print("#### CLIENT "+ str(i))
        print(" > video_src_port" + str(c.video_src_port))
        print(" > ip" + str(c.ip))
        print(" > video_sink_port" + str(c.video_sink_port))
        i += 1
    PIPELINES[uuid] = mixer
    c_api.close()
    mixer.start()


def update_pipelines():
    """
    Function to update current SurfaceStreams pipeline based on connected clients
    :return:
    """
    c_api = ClientApi(bind=engine)
    c_api.open()
    len_clients = len(c_api.get_clients())
    c_api.close()

    if len_clients == 0:
        clear_pipelines()
    else:
        create_multi_mixing_pipeline(mode="other" if len_clients > 1 else "all")

    return True


def remove_pipeline(uuid):
    """
    Deletes pipeline referenced by given uuid.
    :param uuid: uuid of pipeline to remove.
    :return:
    """
    if uuid in PIPELINES:
        PIPELINES[uuid].cleanup()
        del PIPELINES[uuid]
        print("###### removed pipeline\n  > pipelines", PIPELINES.keys())
        return True
    else:
        return False


def clear_pipelines():
    """
    Deletes all SurfaceStream pipelines.
    :return:
    """
    uuid_list = [k for k in PIPELINES.keys()]
    for uuid in uuid_list:
        remove_pipeline(uuid)