from database.base import engine
from database.api import ClientApi
from core.tuio.osc_receiver import OscReceiver
from pythonosc import dispatcher, udp_client


def forward_tuio_message(path, *lst):
    c_api = ClientApi(bind=engine)
    c_api.open()
    for c in c_api.get_clients():
        if c.tuio_sink_port is None or c.tuio_sink_port <= 0:
            continue
        tuio_sink = udp_client.SimpleUDPClient(c.ip, c.tuio_sink_port)
        tuio_sink.send_message(path, lst)
    c_api.close()


class TuioForwardingDispatcher(dispatcher.Dispatcher):
    def __init__(self):
        super().__init__()
        self.set_default_handler(forward_tuio_message)


class TuioForwardingServer(OscReceiver):
    def __init__(self, ip, port):
        super().__init__(ip, port, TuioForwardingDispatcher())
