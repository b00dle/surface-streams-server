import os
import gi
gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "3.0")
gi.require_version("GstVideo", "1.0")
from gi.repository import Gst, Gtk, GObject
import streaming


class GstPipeline(object):
    def __init__(self, name, debug=True):
        GObject.threads_init()
        Gst.init(None)
        self.pipeline = None
        self.bus = None
        self.pipeline = Gst.Pipeline.new(name)
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.enable_sync_message_emission()
        self.bus.connect("message", self.on_bus_message)
        self.bus.connect("sync-message::element", self.on_bus_sync_message)
        self.debug = debug
        self.name = name

    def __del__(self):
        print("##########deleting")
        if self.pipeline != None:
            self.pipeline.set_state(Gst.State.NULL)

    def dump_graph(self):
        dotfile = streaming.DEBUG_GRAPH_DIR+"/"+self.name+".dot"
        if os.access(dotfile, os.F_OK):
            os.remove(dotfile)
        pdffile = streaming.DEBUG_GRAPH_DIR+"/"+self.name+".pdf"
        Gst.debug_bin_to_dot_file(
            self.pipeline,
            Gst.DebugGraphDetails.ALL,
            self.name
        )
        os.system("dot -Tpdf " + dotfile + " -o " + pdffile)

    def start(self):
        self.pipeline.set_state(Gst.State.PLAYING)
        if self.debug:
            print("### PIPELINE GRAPH dumped")
            self.dump_graph()

    def stop(self):
        self.pipeline.set_state(Gst.State.NULL)

    def cleanup(self):
        print("##########cleaning up")
        self.bus.remove_signal_watch()
        self.stop()

    def on_bus_message(self, bus, message):
        """ override in derived classes for message handling. """
        pass

    def on_bus_sync_message(self, bus, message):
        """ override in derived classes for sync message handling. """
        pass

    def make_add_element(self, gst_element_name, name):
        """
        Creates a GstElement with given gst_element_name
        and given name. The element is added to the pipeline
        and then returned.
        """
        gst_element = Gst.ElementFactory.make(gst_element_name, name)
        self.pipeline.add(gst_element)
        return gst_element

    def link_elements(self, src, sink):
        """ Links src-pad of src GstElement to sink-pad of sink GstElement. """
        if not src.link(sink):
            print("## link_elements")
            print(" > could not link")
            print("  > src", src.get_name())
            print("  > sink", sink.get_name())

    def register_callback(self, gst_element, signal_name, function):
        """
        Connects callback function to signal referenced by signal_name
        of given GstElement.
        """
        gst_element.connect(signal_name, function)