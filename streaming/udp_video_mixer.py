import gi
gi.require_version("Gst", "1.0")
gi.require_version("GstVideo", "1.0")
gi.require_version('Gtk', '3.0')
from gi.repository import Gst, GstVideo, GdkX11, Gtk
from streaming.gst_pipeline import GstPipeline

class UdpVideoMixer(GstPipeline):
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

    client_sizes = [
        {
            "width" : 1280,
            "height" : 960
        },
        {
            "width": 640,
            "height": 480
        },
        {
            "width": 320,
            "height": 480
        }
    ]

    def __init__(self, num_clients, width=620, height=480):
        super().__init__("Udp-Video-Mixer")
        self.mixer = self.make_add_element("videomixer", "mixer")
        # create and link client bins
        self.client_bins = []
        for i in range(0, num_clients):
            # create elements
            #self.mixer.set_property("sink_"+str(i)+"::zorder", i)
            udp_src = self.make_add_element("udpsrc", "udpsrc"+str(i))
            udp_src.set_property("caps", Gst.caps_from_string("application/x-rtp, media=(string)application, clock-rate=(int)90000, encoding-name=(string)X-GST, caps=(string)aW1hZ2UvanBlZywgc29mLW1hcmtlcj0oaW50KTAsIHdpZHRoPShpbnQpMTI4MCwgaGVpZ2h0PShpbnQpNzIwLCBwaXhlbC1hc3BlY3QtcmF0aW89KGZyYWN0aW9uKTEvMSwgZnJhbWVyYXRlPShmcmFjdGlvbikyNDAwMC8xMDAx, capsversion=(string)0, payload=(int)96, ssrc=(uint)2277765570, timestamp-offset=(uint)3095164038, seqnum-offset=(uint)16152"))
            src_queue = self.make_add_element("queue", "src_queue"+str(i))
            rtp_depay = self.make_add_element("rtpgstdepay", "rtp_depay"+str(i))
            jpeg_decoder = self.make_add_element("jpegdec", "jpeg_decoder"+str(i))
            videoscale = self.make_add_element("videoscale", "videoscale"+str(i))
            capsfilter = self.make_add_element("capsfilter", "capsfilter"+str(i))
            capsfilter.set_property("caps", Gst.caps_from_string("video/x-raw, width="+str(self.client_sizes[i]["width"])+", height="+str(self.client_sizes[i]["height"])+""))
            #alpha = self.make_add_element("alpha", "alpha"+str(i))
            #alpha.set_property("method", "green")
            # link elements
            self.link_elements(udp_src, src_queue)
            self.link_elements(src_queue, rtp_depay)
            self.link_elements(rtp_depay, jpeg_decoder)
            self.link_elements(jpeg_decoder, videoscale)
            self.link_elements(videoscale, capsfilter)
            #self.link_elements(capsfilter, alpha)
            #self.link_elements(alpha, self.mixer)
            self.link_elements(capsfilter, self.mixer)
            # remember client bin
            self.client_bins.append({
                "udpsrc": udp_src,
                "queue": src_queue,
                "rtpgstdepay": rtp_depay,
                "jpegdec": jpeg_decoder,
                "videoscale": videoscale,
                "capsfilter": capsfilter#,
                #"alpha": alpha
            })
        # create mixer pipeline
        self.queue_out = self.make_add_element("queue", "queue_out")
        self.videoconvert = self.make_add_element("videoconvert", "mixer_convert")
        self.jpeg_encoder = self.make_add_element("jpegenc", "jpeg_encoder")
        self.rtp_packer = self.make_add_element("rtpgstpay", "rtp_packer")
        self.udp_sink = self.make_add_element("udpsink", "udp_sink")
        # link mixer pipeline
        self.link_elements(self.mixer, self.queue_out)
        self.link_elements(self.queue_out, self.videoconvert)
        self.link_elements(self.videoconvert, self.jpeg_encoder)
        self.link_elements(self.jpeg_encoder, self.rtp_packer)
        self.link_elements(self.rtp_packer, self.udp_sink)

    def set_in_port(self, port, client_idx):
        self.client_bins[client_idx]["udpsrc"].set_property("port", port)

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