import argparse
import time

from pythonosc import udp_client

from streaming.osc_pattern import OscPattern


class OscSender(object):
    def __init__(self, ip, port):
        self._client = udp_client.SimpleUDPClient(ip, port)

    def _send_message(self, path, arg_lst):
        self._client.send_message(path, arg_lst)


def extract_bnd_args(pattern):
    return [
        pattern.get_s_id(),
        pattern.get_u_id(),
        pattern.get_bnd().x_pos,
        pattern.get_bnd().y_pos,
        pattern.get_bnd().angle,
        pattern.get_bnd().width,
        pattern.get_bnd().height,
    ]


def extract_sym_args(pattern):
    return [
        pattern.get_s_id(),
        pattern.get_u_id(),
        pattern.get_sym().tu_id,
        pattern.get_sym().c_id,
        "uuid",
        pattern.get_sym().uuid
    ]


class CvPatternSender(OscSender):
    def __init__(self, ip, port):
        super().__init__(ip, port)

    def send_pattern(self, pattern):
        if pattern.is_valid():
            self._send_message("/tuio2/bnd", extract_bnd_args(pattern))
            self._send_message("/tuio2/sym", extract_sym_args(pattern))

    def send_patterns(self, patterns):
        for p in patterns:
            self.send_pattern(p)


def run_pattern_sender(ip="127.0.0.1", port=5005):
    from streaming.osc_pattern import OscPatternBnd, OscPatternSym
    import random
    import uuid

    patterns = [OscPattern(u_id=random.randint(0,500))
                for i in range(0, 10)]
    for p in patterns:
        x = random.randint(0, 10)
        y = 10 - x
        p.set_bnd(OscPatternBnd(x, y, 0, 10, 10))
        p.set_sym(OscPatternSym(str(uuid.uuid4())))

    client = CvPatternSender(ip, port)
    client.send_patterns(patterns)

    for x in range(0,10):
        p_idx = random.randint(0, len(patterns)-1)
        p = patterns[p_idx]
        p.set_x_pos(random.randint(0,15))
        p.set_y_pos(random.randint(0,7))
        client.send_pattern(p)
        time.sleep(1)


'''
minimum example of osc sender
'''


def run(ip="127.0.0.1", port=5005):
    client = udp_client.SimpleUDPClient(ip, port)

    for x in range(10):
        client.send_message("/foo", [x, "yo", True])
        time.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--ip",
        default="127.0.0.1",
        help="The ip of the OSC server"
    )

    parser.add_argument(
        "--port", type=int, default=5005,
        help="The port the OSC server is listening on")

    args = parser.parse_args()

    run(args.ip, args.port)
