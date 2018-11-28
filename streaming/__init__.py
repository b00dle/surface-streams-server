import threading
import gi
import os
from streaming.udp_video_mixer import UdpVideoMixer
gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "3.0")
gi.require_version("GstVideo", "1.0")
from gi.repository import Gst, Gtk, GObject


PIPELINES = {}

THREAD_RUNNING = False

DEBUG_GRAPH_DIR = os.getcwd()

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


def create_multi_mixing_pipeline(CLIENTS, mode="other"):
    """
    Creates a SurfaceStream video mixing pipeline.
    :param CLIENTS: client dicts denoting connection and stream descriptive data.
    :param mode: use 'other' to only merge streams of other clients connected for each client.
    use 'all' to merge alle streams.
    :return:
    """
    clear_pipelines()
    _ensure_gtk_thread_running()
    print("################# CREATING MULTI MIXING PIPELINE")
    mixer = UdpVideoMixer([CLIENTS[k] for k in CLIENTS.keys()], mode=mode)
    i = 0
    for uuid in CLIENTS.keys():
        in_port = CLIENTS[uuid]["in-port"]
        out_address = CLIENTS[uuid]["in-ip"]
        out_port = CLIENTS[uuid]["out-port"]
        mixer.set_in_port(in_port, i)
        mixer.set_out_address(out_address, i)
        mixer.set_out_port(out_port, i)
        print("#### CLIENT "+ str(i))
        print(" > in-port" + str(in_port))
        print(" > out-address" + str(out_address))
        print(" > out-port" + str(out_port))
        i += 1
    PIPELINES[uuid] = mixer
    mixer.start()


def update_pipelines(CLIENTS):
    """
    Function to update current SurfaceStreams pipeline based on connected clients
    :param CLIENTS: client dicts denoting connection and stream descriptive data.
    :return:
    """
    if len(CLIENTS) == 0:
        clear_pipelines()
    else:
        create_multi_mixing_pipeline(CLIENTS, mode="other" if len(CLIENTS) > 1 else "all")
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