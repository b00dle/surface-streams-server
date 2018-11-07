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

    def __init__(self, num_clients):
        super().__init__("Udp-Video-Mixer")
        self.mixer = self.make_add_element("videomixer", "mixer")
        # create and link client bins
        self.client_bins = []
        for i in range(0, num_clients):
            # create elements
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


class UdpMultiVideoMixer(GstPipeline):
    '''
    TODO: add dynamic pipeline adjustment
    '''

    client_properties = [
        {
            "pattern": 0,
            "width": 1280,
            "height": 960
        },
        {
            "pattern": 1,
            "width": 640,
            "height": 480
        },
        {
            "pattern": 4,
            "width": 320,
            "height": 480
        }
    ]

    def __init__(self, num_clients, mode="other", width=640, height=480):
        if mode != "other" and mode != "all":
            raise ValueError("Unknown mode '"+mode+"'\n  > 'other' and 'all' are supported.")

        super().__init__("Udp-Multi-Video-Mixer")

        self.mixers = [
            self.make_add_element("videomixer", "mixer"+str(i))
            for i in range(0, num_clients)
        ]

        self.tees = [
            self.make_add_element("tee", "tee"+str(i))
            for i in range(0, num_clients)
        ]

        # create and link udpsrc inputs to tee
        self.src_bins = []
        for i in range(0, num_clients):
            # create elements
            udp_src = self.make_add_element("udpsrc", "udpsrc"+str(i))
            udp_src.set_property("caps", Gst.caps_from_string("application/x-rtp, media=(string)application, clock-rate=(int)90000, encoding-name=(string)X-GST, caps=(string)aW1hZ2UvanBlZywgc29mLW1hcmtlcj0oaW50KTAsIHdpZHRoPShpbnQpMTI4MCwgaGVpZ2h0PShpbnQpNzIwLCBwaXhlbC1hc3BlY3QtcmF0aW89KGZyYWN0aW9uKTEvMSwgZnJhbWVyYXRlPShmcmFjdGlvbikyNDAwMC8xMDAx, capsversion=(string)0, payload=(int)96, ssrc=(uint)2277765570, timestamp-offset=(uint)3095164038, seqnum-offset=(uint)16152"))
            src_queue = self.make_add_element("queue", "src_queue"+str(i))
            rtp_depay = self.make_add_element("rtpgstdepay", "rtp_depay"+str(i))
            jpeg_decoder = self.make_add_element("jpegdec", "jpeg_decoder"+str(i))
            # link elements
            self.link_elements(udp_src, src_queue)
            self.link_elements(src_queue, rtp_depay)
            self.link_elements(rtp_depay, jpeg_decoder)
            self.link_elements(jpeg_decoder, self.tees[i])
            # remember src bin
            self.src_bins.append({
                "udpsrc": udp_src,
                "queue": src_queue,
                "rtpgstdepay": rtp_depay,
                "jpegdec": jpeg_decoder
            })

        # create and link tee inputs to mixer
        self.mixer_bins = []
        for i in range(0, num_clients):
            for tee_idx in range(0, num_clients):
                if mode == "other" and tee_idx == i:
                    continue
                name_post_fix = str(i) + "-t" + str(tee_idx)
                mixer_queue = self.make_add_element("queue", "mixer_queue"+name_post_fix)
                videoscale = self.make_add_element("videoscale", "videoscale"+name_post_fix)
                capsfilter = self.make_add_element("capsfilter", "capsfilter"+name_post_fix)
                capsfilter.set_property("caps", Gst.caps_from_string("video/x-raw, width=" + str(width) + ", height=" + str(height) + ""))
                alpha = self.make_add_element("alpha", "alpha"+name_post_fix)
                alpha.set_property("method", "green")
                # get and link tee src pad to mixer queue sink pad
                tee_src_pad_template = self.tees[tee_idx].get_pad_template("src_%u")
                tee_src = self.tees[tee_idx].request_pad(tee_src_pad_template, None, None)
                mixer_queue_sink = mixer_queue.get_static_pad("sink")
                self.link_elements(tee_src, mixer_queue_sink)
                # link mixing pipeline
                self.link_elements(mixer_queue, videoscale)
                self.link_elements(videoscale, capsfilter)
                self.link_elements(capsfilter, alpha)
                self.link_elements(alpha, self.mixers[i])

        # create and link mixer outputs to udpsink
        self.sink_bins = []
        for i in range(0, num_clients):
            queue_out = self.make_add_element("queue", "queue_out"+str(i))
            videoconvert = self.make_add_element("videoconvert", "mixer_convert"+str(i))
            jpeg_encoder = self.make_add_element("jpegenc", "jpeg_encoder"+str(i))
            rtp_packer = self.make_add_element("rtpgstpay", "rtp_packer"+str(i))
            udp_sink = self.make_add_element("udpsink", "udp_sink"+str(i))
            # link mixer pipeline
            self.link_elements(self.mixers[i], queue_out)
            self.link_elements(queue_out, videoconvert)
            self.link_elements(videoconvert, jpeg_encoder)
            self.link_elements(jpeg_encoder, rtp_packer)
            self.link_elements(rtp_packer, udp_sink)
            # remember sink bin
            self.sink_bins.append({
                "queue": queue_out,
                "videoconvert": videoconvert,
                "jpegenc": jpeg_encoder,
                "rtpgstpay": rtp_packer,
                "udpsink": udp_sink
            })

    def set_in_port(self, port, client_idx):
        self.src_bins[client_idx]["udpsrc"].set_property("port", port)

    def set_out_address(self, address, client_idx):
        self.sink_bins[client_idx]["udpsink"].set_property("host", address)

    def set_out_port(self, port, client_idx):
        self.sink_bins[client_idx]["udpsink"].set_property("port", port)

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