"""
    TODO
"""

from osgar.node import Node
from osgar.bus import BusShutdownException
import datetime
import os.path
import numpy as np
import cv2


class MeasureNode(Node):
    def __init__(self, config, bus):
        super().__init__(config, bus)
        bus.register('work_dir', "arecont_prev", "basler_prev", "rs_prev", "depth_prev")
        self.control_msg = None
        self.bus = bus
        self.storage_path = config.get("storage_path", "/home/ovosad/ovosad_data")
        self.wdn1 = datetime.datetime.now().strftime("%y%m%d") # day working dir

        self.arecont_image = None
        self.basler_image = None
        self.rs_image = None
        self.rs_depth = None


    def make_dir(self, label):
        wdn2 = f"{datetime.datetime.now().strftime('%H%M%S')}_{label}"
        work_dir_name = os.path.join(self.storage_path, self.wdn1, wdn2)
        os.makedirs(work_dir_name)

        return work_dir_name

    def process_image(self, image_data):
        im_arr = cv2.imdecode(np.frombuffer(image_data, dtype=np.uint8), 1)  # numpy arr from basler and rs?
        resized = cv2.resize(im_arr, (600, 450))
        __, ret_im = cv2.imencode('*.jpeg', resized)

        return ret_im


    def process_depth(self, depth):
        pass


    def run(self):
        try:
            while self.is_bus_alive():
                self.update()
                if self.control_msg is not None:
                    work_dir_name = self.make_dir(self.control_msg)
                    self.publish("work_dir", work_dir_name)
                    self.control_msg = None

                elif self.arecont_image:
                    self.publish("arecont_prev", self.process_image(self.arecont_image))
                elif self.basler_image:
                    self.publish("basler_prev", self.process_image(self.basler_image))
                elif self.rs_image:
                    self.publish("rs_prev", self.process_image(self.rs_image))
                elif self.rs_depth:
                    self.publish("depth_prev", self.process_depth(self.rs_depth))


        except BusShutdownException:
            pass
