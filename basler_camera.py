"""
   Osgar driver for Basler camera.
"""

import time
import os
import json
from threading import Thread

from pypylon import pylon


class BaslerCamera:
    def __init__(self, config, bus):
        self.input_thread = Thread(target=self.run_input, daemon=True)
        self.bus = bus
        # Some parameters could be loaded from config file (see the example).
        self.address = config.get("address", False)
        self.storage_path = config.get("storage", ".")


        tlf = pylon.TlFactory.GetInstance()
        if not self.address:
            self.cam = pylon.InstantCamera(tlf.CreateFirstDevice())
        else:
            self.cam = None
            for dev_info in tlf.EnumerateDevices():
                if dev_info.GetDeviceClass() == 'BaslerGigE':
                    if dev_info.GetIpAddress() == self.address:
                        self.cam = pylon.InstantCamera(tlf.CreateDevice(dev_info))
                        break
            else:
                raise EnvironmentError("no GigE device found")

        self.cam.Open()
        self.cam.ExposureAuto.SetValue('Continuous')
#        self.cam.Gamma.SetValue(0.4)
        self.cam.GainAuto.SetValue("Continuous")
        #self.cam.GainRaw.SetValue(34)

#        a = self.cam.Gain.GetValue()
#        print(a)
        self.bus.register('data')


    def start(self):
        self.input_thread.start()

    def join(self, timeout=None):
        self.input_thread.join(timeout=timeout)

    def run_input(self):
        folder_name = "set_{}".format(int(time.time()))
        os.mkdir(os.path.join(self.storage_path, folder_name))
        
        settings_path = os.path.join(self.storage_path, folder_name, "settings.pfs")
        pylon.FeaturePersistence.Save(settings_path, self.cam.GetNodeMap())
        
        self.cam.StartGrabbing()
        img = pylon.PylonImage()
        while self.bus.is_alive():

            with self.cam.RetrieveResult(2000) as result:
                img.AttachGrabResultBuffer(result)

                short_name = "picture_{}.tiff".format(time.time())
                long_name = os.path.join(folder_name, short_name)
                filename = os.path.join(self.storage_path, long_name)
                # filename = os.path.join(self.storage_path, name)
                img.Save(pylon.ImageFileFormat_Tiff, filename)

                # In order to make it possible to reuse the grab result for grabbing
                # again, we have to release the image (effectively emptying the
                # image object).
                data = json.dumps({
                    "path": long_name,
                    "name": short_name,
                    "exposure": self.cam.ExposureTimeAbs.GetValue(),
                    "gain": self.cam.GainRaw.GetValue(), 
                })
                self.bus.publish("data", data)
                img.Release()
                

    def request_stop(self):
        self.cam.StopGrabbing()
        self.cam.Close()
        self.bus.shutdown()
