import os

from pypylon import pylon
import socket
import urllib.request
import pyrealsense2 as rs
import numpy as np
import datetime
import cv2 as cv
import json
import psutil
import time

HOST = "192.168.1.100"  # Basler camera
STORAGE_PATH = "/home/ovosad/ovosad_data"

ARECONT_URL = "http://192.168.1.36/img.jpg"
ARECONT_SET = "http://192.168.1.36/set?daynight=dual"


def get_disk_space():
    disk = psutil.disk_usage("/")
    return disk.free/1024**3


class Basler:
    def __init__(self, work_dir):
        self.address = HOST
        self.work_dir = work_dir
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
#        Set camera, move to separate method?
        self.cam.ExposureAuto.SetValue('Off')  # was "Continuous", "Once"
        self.cam.ExposureTimeAbs.SetValue(170_000) #exposition tim in nano sec
#        self.cam.Gamma.SetValue(0.4)
        self.cam.GainAuto.SetValue("Off")
        self.cam.GainRaw.SetValue(34) # nastaveni zesileni na minimu
#        a = self.cam.Gain.GetValue()
        self.cam.AutoTargetValue.SetValue(85) # Nastavení celkového požadovaného jasu při autiomatickém nastavení Gani a Exposure time
        self.cam.BalanceWhiteAuto.SetValue("Once")
#        self.cam.BlackLevelRaw.SetValue(500)

        settings_path = os.path.join(self.work_dir, "settings.pfs")
        pylon.FeaturePersistence.Save(settings_path, self.cam.GetNodeMap())

    def set_exposure(self, t=0.2):
        self.cam.Width.SetValue(2304)
        self.cam.OffsetX.SetValue(2304)
        self.cam.ExposureAuto.SetValue('Once')

        self.cam.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        #img = pylon.PylonImage()

        n = 10
        for k in range(n):
            time.sleep(t/n)
        #with self.cam.RetrieveResult(2000) as result:
            #img.AttachGrabResultBuffer(result)
            #time.sleep(t)
            self.expo_value = self.cam.ExposureTimeAbs.GetValue()
            print(k, self.expo_value)

        self.cam.StopGrabbing()
        self.cam.OffsetX.SetValue(0)
        self.cam.Width.SetValue(2*2304)
        print(self.expo_value)
        #self.cam.ExposureTimeRaw.SetValue(int(expo_value))
        self.cam.ExposureAuto.SetValue('Off')

    def take_pic(self, file_path, expo_sleep = 0.2):
        # self.set_exposure(expo_sleep)
        self.cam.StartGrabbing()
        img = pylon.PylonImage()
        with self.cam.RetrieveResult(2000) as result:
            img.AttachGrabResultBuffer(result)
            img.Save(pylon.ImageFileFormat_Tiff, file_path)

            data = {
                    "file_path": file_path,
                    "exposure": self.cam.ExposureTimeAbs.GetValue(),
                    "gain": self.cam.GainRaw.GetValue(),
                }

            img.Release()

        self.cam.StopGrabbing()

        return data


    def close_cam(self):
        self.cam.Close()



if __name__ == "__main__":
    basler = Basler("")

    basler.set_exposure(30)
