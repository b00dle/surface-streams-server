from pythonosc import dispatcher, osc_server
import multiprocessing


class OscReceiver(object):
    def __init__(self, ip, port, osc_disp=dispatcher.Dispatcher()):
        self._server = osc_server.ThreadingOSCUDPServer((ip, port), osc_disp)
        self._server_process = multiprocessing.Process(target=self._server.serve_forever)

    def start(self):
        print("Serving on {}".format(self._server.server_address))
        self._server_process.start()

    def terminate(self):
        print("Server terminated.")
        self._server_process.terminate()

    def join(self):
        self._server_process.join()