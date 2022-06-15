"""
    TODO
"""
import os.path
import socket
import urllib.request

from osgar.node import Node


class Arecont(Node):
    def __init__(self, config, bus):
        super().__init__(config, bus)
        bus.register('image')
        self.bus = bus
        self.set_camera()
        self.work_dir = None
        self.url = "http://192.168.1.36/img.jpg"

    def set_camera(self):
        pass

    def save_image(self, image):
        with open(os.path.join(self.work_dir, "arecont_im.jpg"), "wb") as f:
                f.write(image)


    def arecont_take_pic(self):
        image = None
        for ii in range(5):  # the camera adapts to the environment.
            try:
                # https://github.com/mesonbuild/meson/issues/4087
                # without timeout the call can hang the process forever
                with urllib.request.urlopen(self.url, timeout=0.5) as f:
                    data = f.read()
                if len(data) > 0:
                    image = data
            except socket.timeout:
                pass
            self.sleep(0.2)

        return image  # use the last one image


    def update(self):
        timestamp, channel, data = self.listen()
        if channel == "work_dir":
            self.work_dir = data
            image = self.arecont_take_pic()
            if image:
                self.publish("image", image)
                self.save_image(image)
