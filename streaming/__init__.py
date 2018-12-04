import threading
import gi
import os
from streaming.udp_video_mixer import UdpVideoMixer
gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "3.0")
gi.require_version("GstVideo", "1.0")
from gi.repository import Gst, Gtk, GObject

JPEG_CAPS = "application/x-rtp, " \
            "media=(string)application, " \
            "clock-rate=(int)90000, " \
            "encoding-name=(string)X-GST, " \
            "caps=(string)aW1hZ2UvanBlZywgc29mLW1hcmtlcj0oaW50KTAsIHdpZHRoPShpbnQpMTI4MCwgaGVpZ2h0PShpbnQpNzIwLCBwaXhlbC1hc3BlY3QtcmF0aW89KGZyYWN0aW9uKTEvMSwgZnJhbWVyYXRlPShmcmFjdGlvbikyNDAwMC8xMDAx, " \
            "capsversion=(string)0, " \
            "payload=(int)96, " \
            "ssrc=(uint)2277765570, " \
            "timestamp-offset=(uint)3095164038, " \
            "seqnum-offset=(uint)16152"

VP8_CAPS = "application/x-rtp, " \
           "media=(string)video, " \
           "clock-rate=(int)90000, " \
           "encoding-name=(string)VP8-DRAFT-IETF-01, " \
           "payload=(int)96, " \
           "ssrc=(uint)2990747501, " \
           "clock-base=(uint)275641083, " \
           "seqnum-base=(uint)34810"

MP4_CAPS = "application/x-rtp, " \
           "media=(string)video, " \
           "clock-rate=(int)90000, " \
           "encoding-name=(string)MP4V-ES, " \
           "profile-level-id=(string)1, " \
           "config=(string)000001b001000001b58913000001000000012000c48d8800cd3204709443000001b24c61766335362e312e30, " \
           "payload=(int)96, " \
           "ssrc=(uint)2873740600, " \
           "timestamp-offset=(uint)391825150, " \
           "seqnum-offset=(uint)2980"

H264_CAPS = "application/x-rtp, " \
            "media=video, " \
            "clock-rate=90000, " \
            "encoding-name=H264, " \
            "packetization-mode=1, " \
            "profile-level-id=f40032, " \
            "payload=96, " \
            "ssrc=1577364544, " \
            "timestamp-offset=1721384841, " \
            "seqnum-offset=7366, " \
            "a-framerate=25"

H265_CAPS = "application/x-rtp, " \
            "media=video, " \
            "payload=96, " \
            "clock-rate=90000, " \
            "encoding-name=H265, " \
            "ssrc=2828246746, " \
            "timestamp-offset=1863230164, " \
            "seqnum-offset=12204, " \
            "a-framerate=23.976023976023978"

PIPELINES = {}

THREAD_RUNNING = False

DEBUG_GRAPH_DIR = os.getcwd()

MERGED_STREAM_WIDTH = 640

MERGED_STREAM_HEIGHT = 480

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
    mixer = UdpVideoMixer(
        [CLIENTS[k] for k in CLIENTS.keys()],
        mode=mode,
        width=MERGED_STREAM_WIDTH,
        height=MERGED_STREAM_HEIGHT
    )
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