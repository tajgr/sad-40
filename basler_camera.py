"""
   Osgar driver for Basler camera.
"""

import time
import os
import json
from threading import Thread
from osgar.node import Node

from pypylon import pylon


class BaslerCamera(Node):

    def __init__(self, config, bus):
        super().__init__(config, bus)
        self.address = config.get("address", False)
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

        self.cam.ExposureAuto.SetValue('Off')
        self.cam.ExposureTimeAbs.SetValue(170_000)
        self.cam.GainAuto.SetValue("Off")
        self.cam.GainRaw.SetValue(34)


        self.bus.register('picture')
        self.bus.register('metadata')

        self.expo_value = -1
        self.set_exposure()


    def set_exposure(self):
        """ Wait till exposure is adapted - timeout is 20 seconds.
        """
        self.cam.Width.SetValue(2304)
        self.cam.OffsetX.SetValue(2304)
        self.cam.ExposureAuto.SetValue('Once')

        self.cam.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

        for k in range(20):
            time.sleep(1)
            new_expo = self.cam.ExposureTimeAbs.GetValue()
            if abs(new_expo - self.expo_value) < 50:
                break
            #print(k, new_expo)
            self.expo_value = new_expo


        self.cam.StopGrabbing()
        self.cam.OffsetX.SetValue(0)
        self.cam.Width.SetValue(2*2304)
        print(self.expo_value)
        #self.cam.ExposureTimeRaw.SetValue(int(expo_value))
        self.cam.ExposureAuto.SetValue('Off')


    def update(self):
        dt, channel, data = self.listen()
        # print(dt, channel, data)
        if channel != "work_dir":
            return
        # data = "/home/ovosad/ovosad_data/test_basler_02"
        save_path = data

        metadata = {"pictures": {}}
        ev_values = [1, 0.5, 0.25, 0.125, 2, 4, 8]
        for ii, ev in enumerate(ev_values):
            try:
                self.cam.ExposureTimeAbs.SetValue(self.expo_value * ev)
                short_name = "im_basler_EV{}.tiff".format(ii)
                long_name = os.path.join(save_path, short_name)
                self.take_pic(long_name)
                metadata["pictures"][short_name] = {
                    "path": str(long_name),
                    "exposure": self.cam.ExposureTimeAbs.GetValue(),
                }
            except Exception as e:
                pass
                print(e)
                try:
                    self.cam.StopGrabbing()
                except:
                    pass

        self.bus.publish("metadata", json.dumps(metadata))
        #self.bus.publish("picture:null", data) # TODO not ready for production

        meta_path = os.path.join(save_path, "basler_meta.json")
        with open(meta_path, "w") as f:
            f.write(json.dumps(metadata, indent=4))

    def take_pic(self, savepath):
        self.cam.StartGrabbing()
        img = pylon.PylonImage()
        with self.cam.RetrieveResult(1000) as result:
            img.AttachGrabResultBuffer(result)
            img.Save(pylon.ImageFileFormat_Tiff, savepath)
            img.Release()
        self.cam.StopGrabbing()

    def request_stop(self):
        self.cam.StopGrabbing()
        self.cam.Close()
        self.bus.shutdown()
