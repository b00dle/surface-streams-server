import threading
import gi
from streaming.udp_video_loopback import UdpVideoLoopback
gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "3.0")
gi.require_version("GstVideo", "1.0")
from gi.repository import Gst, Gtk, GObject


PIPELINES = {}

THREAD_RUNNING = False


def _run_thread():
    GObject.threads_init()
    Gst.init(None)
    Gtk.main()


def _ensure_gtk_thread_running():
    global THREAD_RUNNING
    if not THREAD_RUNNING:
        gtk_main = threading.Thread(target=_run_thread)
        gtk_main.start()
        THREAD_RUNNING = True


def create_loopback_pipeline(uuid, in_port, out_port, in_address):
    _ensure_gtk_thread_running()
    loopback = UdpVideoLoopback()
    loopback.set_in_port(in_port)
    loopback.set_out_address(in_address)
    loopback.set_out_port(out_port)
    #loopback.set_in_address(in_address)

    print("################# CREATING LOOPBACK PIPELINE")
    print("in-port:", in_port)
    print("in-ip:", in_address)
    print("out-port:", out_port)

    PIPELINES[uuid] = loopback
    loopback.start()


def remove_pipeline(uuid):
    if uuid in PIPELINES:
        PIPELINES[uuid].cleanup()
        del PIPELINES[uuid]
        print("###### removed pipeline\n  > pipelines", PIPELINES.keys())
        return True
    else:
        return False