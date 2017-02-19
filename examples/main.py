# PyUPnP - Simple Python UPnP device library built in Twisted
# Copyright (C) 2013  Dean Gardiner <gardiner91@gmail.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from threading import Thread
import time
import grovepi
import lirc  
import os
from lirc import Lirc
import speech_recognition as sr
from twisted.internet import reactor
from pyupnp.device import Device, DeviceIcon
from pyupnp.logr import Logr
from pyupnp.services import register_action
from pyupnp.services.speechToTextService import SpeechToTextService
from pyupnp.services.sendCommandService import SendCommandService
from pyupnp.services.remoteControlService import RemoteControlService
from pyupnp.services.connection_manager import ConnectionManagerService
from pyupnp.services.content_directory import ContentDirectoryService
from pyupnp.services.microsoft.media_receiver_registrar import MediaReceiverRegistrarService
from pyupnp.ssdp import SSDP
from pyupnp.upnp import UPnP

class MediaServerDevice(Device):
    deviceType = 'urn:schemas-upnp-org:device:RaspberryPi:1'

    friendlyName = "Raspberry Pi Voice Commander"
    def __init__(self):
        Device.__init__(self)

        self.uuid = '5df70325-829a-4c85-ba8c-cdb9e9b4aacf'
        # self.connectionManager = MSConnectionManager()

        # self.speechToTextService = MSSpeechToTextService()
        self.sendCommandService = MSSendCommandService()
        self.remoteControlService = MSRemoteControlService()
        self.services = [
            # self.connectionManager,
            self.sendCommandService,
            # self.speechToTextService,
            self.remoteControlService
        ]

        self.icons = [
            DeviceIcon('image/png', 32, 32, 24,
                       'http://172.25.3.103:52323/MediaRenderer_32x32.png')
        ]

        self.namespaces['dlna'] = 'urn:schemas-dlna-org:device-1-0'
        self.extras['dlna:X_DLNADOC'] = 'DMS-1.50'

# class SpeechToTextThread(Thread):
#     def __init__(self, service):
#         Thread.__init__(self)
#         self.service = service

#         self.recognizer = sr.Recognizer()
#         self.recognizer.energy_threshold = 3500
#         self.microphone = sr.Microphone(device_index = 2, sample_rate = 44100, chunk_size = 512)

#     def run(self):
#         print("#########Say something!")
#         with self.microphone as source: audio = self.recognizer.listen(source)
#         print("#########Got it! Now to recognize it...")
#         try:
#             # recognize speech using Google Speech Recognition
#             value = self.recognizer.recognize_google(audio)
#             # we need some special handling here to correctly print unicode characters to standard output
#             if str is bytes:  # this version of Python uses bytes for strings (Python 2)
#                 print(u"#########You said {}".format(value).encode("utf-8"))
#                 self.service.transcribedText = format(value)
#             else:  # this version of Python uses unicode for strings (Python 3+)
#                 print("#########You said {}".format(value))
#                 self.service.transcribedText = format(value)
#         except sr.UnknownValueError:
#             print("#########Oops! Didn't catch that")
#         except sr.RequestError as e:
#             print("#########Uh oh! Couldn't request results from Google Speech Recognition service; {0}".format(e))
#         except IOError:
#             print ("#########Error BUTTON")

class RemoteControlThread(Thread):
    def __init__(self, service):
        Thread.__init__(self)
        self.service = service
        self.recordButton = 2
        self.powerButton = 3
        self.muteButton = 4
        self.volumeButton = 7
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 3500
        self.microphone = sr.Microphone(device_index = 2, sample_rate = 44100, chunk_size = 512)

        grovepi.pinMode(self.recordButton,"INPUT")
        grovepi.pinMode(self.powerButton,"INPUT")
        grovepi.pinMode(self.muteButton,"INPUT")
        grovepi.pinMode(self.volumeButton,"INPUT")

        self.service.beginRecognitionControl = 0
    def run(self):
        print("#########Remote Control Activated ... Waiting for your click")
        while True:
            if (grovepi.digitalRead(self.recordButton) == 1):
                print("#########Say something!")
                with self.microphone as source: audio = self.recognizer.listen(source)
                print("#########Got it! Now to recognize it...")
                try:
                    # recognize speech using Google Speech Recognition
                    recognizedString = self.recognizer.recognize_google(audio)
                    # we need some special handling here to correctly print unicode characters to standard output
                    if str is bytes:  # this version of Python uses bytes for strings (Python 2)
                        print(u"#########You said {}".format(recognizedString).encode("utf-8"))
                    else:  # this version of Python uses unicode for strings (Python 3+)
                        print("#########You said {}".format(recognizedString))
                    #Extracting command from the recognized phrase
                    if "TV" in recognizedString:
                        if "power" in recognizedString:
                            self.service.tvCommandControl = "" # Reset the event
                            self.service.tvCommandControl = "power"
                        if "mute" in recognizedString:
                            self.service.tvCommandControl = "" # Reset the event
                            self.service.tvCommandControl = "mute"
                        if "volume up" in recognizedString:
                            self.service.tvCommandControl = "" # Reset the event
                            self.service.tvCommandControl = "volume up"
                except sr.UnknownValueError:
                    print("#########Oops! Didn't catch that")
                except sr.RequestError as e:
                    print("#########Uh oh! Couldn't request results from Google Speech Recognition service; {0}".format(e))
            elif (grovepi.digitalRead(self.powerButton) == 1):
                self.service.tvCommandControl = "" # Reset the event
                self.service.tvCommandControl = "power"
            elif (grovepi.digitalRead(self.muteButton) == 1):
                self.service.tvCommandControl = "" # Reset the event
                self.service.tvCommandControl = "mute"
            elif (grovepi.digitalRead(self.volumeButton) == 1):
                self.service.tvCommandControl = "" # Reset the event
                self.service.tvCommandControl = "volume up"

class SendCommandThread(Thread):
    def __init__(self, service,command):
        Thread.__init__(self)
        self.service = service
        if(os.path.isfile("/var/run/lirc/lircd.pid")):
            print("#########Lircd was correctly set up")
        else:
            os.system("lircd -d /dev/lirc0")
            print("#########Lircd is set up")
        self.lirc_obj = Lirc()
        self.remote = self.lirc_obj.devices()[0]
        self.command = command
    def run(self):
        if(self.command == "power"):
            self.lirc_obj.send_once(self.remote,"BTN_POWER")
            print("#########command power is sent")
        elif(self.command == "mute"):
            self.lirc_obj.send_once(self.remote,"BTN_MUTE")
            print("#########command mute is sent")
        elif(self.command == "volume up"):
            self.lirc_obj.send_once(self.remote,"KEY_VOLUMEUP")
            print("#########command volume up is sent")
        else:
            print("#########command is not valid... you can send turn on, mute, volume up")
 
# class MSSpeechToTextService(SpeechToTextService):
#     def __init__(self):
#         SpeechToTextService.__init__(self)
#     @register_action('BeginRecognition')
#     def beginRecognition(self):
#         self.thread = SpeechToTextThread(self)
#         self.thread.start()

class MSRemoteControlService(RemoteControlService):
    def __init__(self):
        RemoteControlService.__init__(self)
        self.thread = RemoteControlThread(self)
        self.thread.start()
    # @register_action('SetTvCommand')
    # def setTvCommand(self,command):
    #     self.tvCommandControl = command

class MSSendCommandService(SendCommandService):
    def __init__(self):
        SendCommandService.__init__(self)
    @register_action('SendCommand')
    def sendCommand(self,tvCommand):
        if (tvCommand != ""):
            self.thread = SendCommandThread(self,tvCommand)
            self.thread.start()
            self.tvCommand = tvCommand
   
# class MSConnectionManager(ConnectionManagerService):
#     def __init__(self):
#         ConnectionManagerService.__init__(self)

#         self.source_protocol_info = 'http-get:*:*:*'
#         self.current_connection_ids = '0'     


class CommandThread(Thread):
    def __init__(self, device, upnp, ssdp):
        """

        :type device: Device
        :type upnp: UPnP
        :type ssdp: SSDP
        """
        Thread.__init__(self)
        self.device = device
        self.upnp = upnp
        self.ssdp = ssdp

        self.running = True

    def run(self):
        while self.running:
            try:
                command = 'command_' + raw_input('')

                if hasattr(self, command):
                    getattr(self, command)()
            except EOFError:
                self.command_stop()

    def command_stop(self):
        # Send 'byebye' NOTIFY
        self.ssdp.clients.sendall_NOTIFY(None, 'ssdp:byebye', True)

        # Stop everything
        self.upnp.stop()
        self.ssdp.stop()
        reactor.stop()
        self.running = False

if __name__ == '__main__':
    Logr.configure(logging.DEBUG)

    device = MediaServerDevice()

    upnp = UPnP(device)
    ssdp = SSDP(device)

    upnp.listen()
    ssdp.listen()

    def event_test():
#        device.contentDirectory.system_update_id = time.time()
        reactor.callLater(5, event_test)

    event_test()

    r = CommandThread(device, upnp, ssdp)
    r.start()

    reactor.run()
