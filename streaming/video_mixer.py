import gi
gi.require_version("Gst", "1.0")
gi.require_version("GstVideo", "1.0")
gi.require_version('Gtk', '3.0')
from gi.repository import Gst, GstVideo, GdkX11, Gtk
from streaming.gst_pipeline import GstPipeline

class VideoMixer(GstPipeline):
    '''
    gst pipeline for gstreamer video mixing.
    UDP Received client motion jpeg frames are alpha keyed on green pixels and then overlayed.
    The result is jpeg encoded and rtp-gst payloaded and then dumped into udpsink.

    example gst pipeline description:
    gst-launch-1.0 videomixer name=mixer sink_0::zorder=0 sink_1::zorder=1 sink_2::zorder=2 ! videoconvert ! jpegenc ! rtpgstpay ! udpsink host=0.0.0.0 port=5000 \
        udpsrc port=5001 caps="application/x-rtp, media=video" ! rtpgstdepay ! jpegdec ! videoscale ! video/x-raw, width=640, height=480 ! alpha method=green ! mixer.sink_0 \
        udpsrc port=5002 caps="application/x-rtp, media=video" ! rtpgstdepay ! jpegdec ! videoscale ! video/x-raw, width=640, height=480 ! alpha method=green ! mixer.sink_1 \
        udpsrc port=5003 caps="application/x-rtp, media=video" ! rtpgstdepay ! jpegdec ! videoscale ! video/x-raw, width=640, height=480 ! alpha method=green ! mixer.sink_2

    TODO: add dynamic pipeline adjustment
    '''

    client_properties = [
        {
            "pattern": 0,
            "width": 1280,
            "height": 960,
        },
        {
            "pattern": 1,
            "width": 640,
            "height": 480,
        },
        {
            "pattern": 4,
            "width": 320,
            "height": 240,
        }
    ]

    def __init__(self):
        super().__init__("Udp-Video-Mixer")
        self.mixer = self.make_add_element("videomixer", "mixer")
        # create and link client bins
        self.client_bins = []
        for i in range(0, len(self.client_properties)):
            # create elements
            #self.mixer.set_property("sink_"+str(i)+"::zorder", i)
            videosrc = self.make_add_element("videotestsrc", "videosrc"+str(i))
            videosrc.set_property("pattern", self.client_properties[i]["pattern"])
            videoscale = self.make_add_element("videoscale", "videoscale"+str(i))
            capsfilter = self.make_add_element("capsfilter", "capsfilter"+str(i))
            capsfilter.set_property("caps", Gst.caps_from_string("video/x-raw, width="+str(self.client_properties[i]["width"])+", height="+str(self.client_properties[i]["height"])+""))
            # link elements
            self.link_elements(videosrc, videoscale)
            self.link_elements(videoscale, capsfilter)
            self.link_elements(capsfilter, self.mixer)
            # remember client bin
            self.client_bins.append({
                "videotestsrc": videosrc,
                "videoscale": videoscale,
                "capsfilter": capsfilter
            })
        # create mixer pipeline
        self.videoconvert = self.make_add_element("videoconvert", "mixer_convert")
        self.jpeg_encoder = self.make_add_element("jpegenc", "jpeg_encoder")
        self.rtp_packer = self.make_add_element("rtpgstpay", "rtp_packer")
        self.udp_sink = self.make_add_element("udpsink", "udp_sink")
        # link mixer pipeline
        self.link_elements(self.mixer, self.videoconvert)
        self.link_elements(self.videoconvert, self.jpeg_encoder)
        self.link_elements(self.jpeg_encoder, self.rtp_packer)
        self.link_elements(self.rtp_packer, self.udp_sink)

    def set_out_address(self, address):
        self.udp_sink.set_property("host", address)

    def set_out_port(self, port):
        self.udp_sink.set_property("port", port)

    def on_udp_bus_message(self, bus, message):
        print("### on_udp_bus_message")
        print("  > message.src", message.src.get_name())

    def on_bus_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.STREAM_START:
            print("stream start")
            #self.pipeline.set_state(Gst.State.PLAYING)
        elif t == Gst.MessageType.ERROR:
            self.pipeline.set_state(Gst.State.NULL)
            err, debug = message.parse_error()
            print(message.src.get_name()+" Error: %s" % err, debug)
        elif t == Gst.MessageType.STATE_CHANGED:
            old_state, new_state, pending_state = message.parse_state_changed()
            print(message.src.get_name()+" state changed from %s to %s." %
                  (old_state.value_nick, new_state.value_nick))
        elif t == Gst.MessageType.ELEMENT:
            msg_src = message.src.get_name()
            if "udp" in msg_src:
                print(msg_src)
        elif t == Gst.MessageType.EOS:
            print("reached end")
        elif t == Gst.MessageType.WARNING:
            wrn, debug = message.parse_warning()
            print(message.src.get_name() + " Warning: %s" % wrn, debug)
        else:
            print(t)