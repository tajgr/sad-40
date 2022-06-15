"""
    Simple zmq transmitter and receiver
"""

import zmq
import contextlib
import osgar.lib.serialize


def pull_msg():
    context = zmq.Context.instance()
    socket = context.socket(zmq.PULL)
    # https://stackoverflow.com/questions/7538988/zeromq-how-to-prevent-infinite-wait
    socket.RCVTIMEO = 200  # milliseconds

    socket.LINGER = 100
    socket.bind("tcp://*:5555")
    with contextlib.closing(socket):
        try:
            channel, raw = socket.recv_multipart()
            data = osgar.lib.serialize.deserialize(raw)
            return channel, data

        except:  # zmq.error.Again:  # TODO
                pass


def push_msg(data):
    context = zmq.Context.instance()
    socket = context.socket(zmq.PUSH)
    socket.setsockopt(zmq.LINGER, 100)  # milliseconds
    socket.bind("tcp://*:5556")

    try:
        with contextlib.closing(socket):
            raw = osgar.lib.serialize.serialize(data)
            socket.send_multipart([bytes("control_msg", 'ascii'), raw])
    except zmq.ZMQError as e:
        print(e)
