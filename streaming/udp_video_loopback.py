import gi
gi.require_version("Gst", "1.0")
gi.require_version("GstVideo", "1.0")
gi.require_version('Gtk', '3.0')
from gi.repository import Gst, GstVideo, GdkX11, Gtk
from streaming.gst_pipeline import GstPipeline

class UdpVideoLoopback(GstPipeline):
    '''
    Debugging gst pipeline for gstreamer video loopback.
    Implements a GST pipeline to receive jpeg encoded rtp-gst frames over udp,
    decode them, convert them to video, encode them back to jpeg, payload rtp-gst
    packeges and dump into udpsink.

    gst pipeline description:
    gst-launch-1.0 udpsrc port=5000 ! application/x-rtp, media=application ! queue !
        rtpgstdepay ! jpegdec ! jpegenc ! rtpgstpay !  udpsink port=5001

    TODO: add dynamic pipeline adjustment
    '''

    def __init__(self):
        super().__init__("Udp-Video-Loopback")
        #self.audiosrc = self.make_add_element("videotestsrc", "audiosrc")
        #self.audiosink = self.make_add_element("autovideosink", "audiosink")
        #self.link_elements(self.audiosrc, self.audiosink)
        # create necessary elements
        self.udp_src = self.make_add_element("udpsrc", "udpsrc")
        self.udp_src.set_property("caps", Gst.caps_from_string("application/x-rtp, media=(string)application, clock-rate=(int)90000, encoding-name=(string)X-GST, caps=(string)aW1hZ2UvanBlZywgc29mLW1hcmtlcj0oaW50KTAsIHdpZHRoPShpbnQpMTI4MCwgaGVpZ2h0PShpbnQpNzIwLCBwaXhlbC1hc3BlY3QtcmF0aW89KGZyYWN0aW9uKTEvMSwgZnJhbWVyYXRlPShmcmFjdGlvbikyNDAwMC8xMDAx, capsversion=(string)0, payload=(int)96, ssrc=(uint)2277765570, timestamp-offset=(uint)3095164038, seqnum-offset=(uint)16152"))
        self.src_queue = self.make_add_element("queue", "src_queue")
        self.rtp_depay = self.make_add_element("rtpgstdepay", "rtp_depay")
        self.jpeg_decoder = self.make_add_element("jpegdec", "jpeg_decoder")
        #
        # DO STUFF HERE
        #
        self.jpeg_encoder = self.make_add_element("jpegenc", "jpeg_encoder")
        self.rtp_packer = self.make_add_element("rtpgstpay", "rtp_packer")
        self.udp_sink = self.make_add_element("udpsink", "udp_sink")

        self.link_elements(self.udp_src, self.src_queue)
        self.link_elements(self.src_queue, self.rtp_depay)
        self.link_elements(self.rtp_depay, self.jpeg_decoder)
        self.link_elements(self.jpeg_decoder, self.jpeg_encoder)
        self.link_elements(self.jpeg_encoder, self.rtp_packer)
        self.link_elements(self.rtp_packer, self.udp_sink)

    def set_in_port(self, port):
        self.udp_src.set_property("port", port)

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