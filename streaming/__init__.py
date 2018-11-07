import threading
import gi
from streaming.udp_video_loopback import UdpVideoLoopback
from streaming.udp_video_mixer import UdpVideoMixer, UdpMultiVideoMixer
from streaming.video_mixer import VideoMixer
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


def create_udp_mixing_pipeline(uuid, in_port, out_port, in_address, CLIENTS):
    _ensure_gtk_thread_running()
    mixer = UdpVideoMixer(len(CLIENTS))
    mixer.set_in_port(in_port, 0)
    i = 1
    for k in PIPELINES.keys():
        mixer.set_in_port(CLIENTS[k]["in-port"], i)
        i += 1
    mixer.set_out_address(in_address)
    mixer.set_out_port(out_port)

    print("################# CREATING UDP MIXING PIPELINE")
    print("in-port:", in_port)
    print("in-ip:", in_address)
    print("out-port:", out_port)

    PIPELINES[uuid] = mixer
    mixer.start()


def create_mixing_pipeline(uuid, in_port, out_port, in_address):
    _ensure_gtk_thread_running()
    mixer = VideoMixer()
    mixer.set_out_address(in_address)
    mixer.set_out_port(out_port)

    print("################# CREATING MIXING PIPELINE")
    print("in-port:", in_port)
    print("in-ip:", in_address)
    print("out-port:", out_port)

    PIPELINES[uuid] = mixer
    mixer.start()


def create_multi_mixing_pipeline(CLIENTS, mode="other"):
    clear_pipelines()
    _ensure_gtk_thread_running()
    print("################# CREATING MULTI MIXING PIPELINE")
    mixer = UdpMultiVideoMixer(len(CLIENTS), mode=mode)
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
    if len(CLIENTS) == 0:
        clear_pipelines()
    else:
        create_multi_mixing_pipeline(CLIENTS, mode="other" if len(CLIENTS) > 1 else "all")
    return True


def remove_pipeline(uuid):
    if uuid in PIPELINES:
        PIPELINES[uuid].cleanup()
        del PIPELINES[uuid]
        print("###### removed pipeline\n  > pipelines", PIPELINES.keys())
        return True
    else:
        return False


def clear_pipelines():
    uuid_list = [k for k in PIPELINES.keys()]
    for uuid in uuid_list:
        remove_pipeline(uuid)