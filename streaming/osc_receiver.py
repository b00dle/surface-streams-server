import argparse
import time

from pythonosc import dispatcher
from pythonosc import osc_server
import multiprocessing

from streaming.osc_pattern import OscPattern, OscPatternBnd, OscPatternSym


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


def bnd_handler(path, fixed_args, s_id, u_id, x_pos, y_pos, angle, width, height):
    msg_queue = fixed_args[0]
    msg_queue.put({"s_id": s_id, "u_id": u_id, "bnd": OscPatternBnd(x_pos, y_pos, angle, width, height)})


def sym_handler(path, fixed_args, s_id, u_id, tu_id, c_id, sym_type, sym_value):
    if sym_type != "uuid":
        raise ValueError("FAILURE: sym_type must be 'uuid'\n  > got:", sym_type)
    msg_queue = fixed_args[0]
    msg_queue.put({"s_id": s_id, "u_id": u_id, "sym": OscPatternSym(sym_value, tu_id, c_id)})


class CvPatternDispatcher(dispatcher.Dispatcher):
    def __init__(self, bnd_queue=multiprocessing.Queue(), sym_queue=multiprocessing.Queue()):
        super().__init__()
        self.bnd_queue = bnd_queue
        self.sym_queue = sym_queue
        self.map("/tuio2/bnd", bnd_handler, self.bnd_queue)
        self.map("/tuio2/sym", sym_handler, self.sym_queue)


class CvPatternReceiver(OscReceiver):
    def __init__(self, ip, port):
        self._dispatcher = CvPatternDispatcher()
        super().__init__(ip, port, self._dispatcher)
        self._patterns = {}

    def update_patterns(self):
        """ Updates all patterns given the unprocessed messages
            stored by the dispatcher. Returns an update log,
            listing all updated_bnd s_ids and all
            updated_sim s_ids changed that way.
            Structure:
            update_log = {
                "bnd": [num1, ..., numX],
                "sym": [num1, ..., numY]
            }"""
        update_log = {"bnd": [], "sym": []}
        # extract bnd updates
        while not self._dispatcher.bnd_queue.empty():
            bnd_msg = self._dispatcher.bnd_queue.get()
            s_id = bnd_msg["s_id"]
            u_id = bnd_msg["u_id"]
            if s_id not in self._patterns.keys():
                self._patterns[s_id] = OscPattern(s_id=s_id, u_id=u_id)
            self._patterns[s_id].set_bnd(bnd_msg["bnd"])
            if s_id not in update_log["bnd"]:
                update_log["bnd"].append(s_id)
        # extract sym updates
        while not self._dispatcher.sym_queue.empty():
            sym_msg = self._dispatcher.sym_queue.get()
            s_id = sym_msg["s_id"]
            u_id = sym_msg["u_id"]
            if s_id not in self._patterns.keys():
                self._patterns[s_id] = OscPattern(s_id=s_id, u_id=u_id)
            if self._patterns[s_id].get_sym() != sym_msg["sym"]:
                self._patterns[s_id].set_sym(sym_msg["sym"])
                if s_id not in update_log["sym"]:
                    update_log["sym"].append(s_id)
        return update_log

    def get_pattern(self, s_id):
        if s_id not in self._patterns:
            return None
        return self._patterns[s_id]

    def get_patterns(self, s_ids=[]):
        if len(s_ids) == 0:
            return self._patterns
        res = {}
        for s_id in s_ids:
            p = self.get_pattern(s_id)
            if p is not None:
                res[s_id] = p
        return res


def run_pattern_receiver(ip="127.0.0.1", port=5005):
    server = CvPatternReceiver(ip, port)
    server.start()

    while True:
        update_log = server.update_patterns()

        nothing_updated = True
        if len(update_log["bnd"]) > 0:
            nothing_updated = False
            print("Received BND update\n  > ", server.get_patterns(update_log["bnd"]))
        if len(update_log["sym"]) > 0:
            nothing_updated = False
            print("Received SYM update\n  > ", server.get_patterns(update_log["sym"]))
        if nothing_updated:
            print("Waiting for BND or SYM update")

        time.sleep(1)


'''
minimum example of osc receiver
'''


def _print_foo_handler(unused_addr, fixed_args, *lst):
    fixed_args[0].put([unused_addr, lst])


def _print_foo_handler_fixed(unused_addr, fixed_args, num, str, bool):
    fixed_args[0].put([unused_addr, num, str, bool])


def _print_foo_handler_mixed(unused_addr, fixed_args, num, *lst):
    fixed_args[0].put([unused_addr, num, lst])


def run(ip="127.0.0.1", port=5005):
    msg_queue = multiprocessing.Queue()

    osc_disp = dispatcher.Dispatcher()
    osc_disp.map("/foo", _print_foo_handler_mixed, msg_queue)

    server = osc_server.ThreadingOSCUDPServer((ip, port), osc_disp)
    print("Serving on {}".format(server.server_address))
    server_process = multiprocessing.Process(target=server.serve_forever)
    server_process.start()

    # this piece should be embedded into the frame by frame reconstruction on the client side
    while True:
        print("WAITING FOR MESSAGE")

        while not msg_queue.empty():
            print(msg_queue.get())

        time.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--ip",
        default="127.0.0.1",
        help="The ip to listen on")

    parser.add_argument(
        "--port",
        type=int,
        default=5005,
        help="The port to listen on"
    )

    args = parser.parse_args()

    run(args.ip, args.port)
