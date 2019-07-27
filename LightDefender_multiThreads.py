import sys
import time

import cv2
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import pyqtSlot, QThread, QObject, pyqtSignal, Qt
from PyQt5.QtGui import QImage, QPixmap, QGuiApplication
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.uic import loadUi
from PyQt5.QtMultimedia import QSound
from FaceDetector import FaceDetector
from Configuration import Conf
from NotificationManager import TwilioNotifier
from SoundManager import SoundManager
from LaserController import LaserController
from calibrate import Calibration


class VideoStream(QObject):
    finished = pyqtSignal()
    frame = pyqtSignal(object)
    # image = pyqtSignal(QImage)
    # play = pyqtSignal(int)
    # coordinates = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.videoStream = None
        self.stopped = False
        self.spottedSound = QSound("resources/voices/target_aquaired.wav")
        self.searchingSound = QSound("resources/voices/searching.wav")

    def long_running(self):
        print("Starting")
        self.stopped = False
        self.videoStream = cv2.VideoCapture(0)
        fd = FaceDetector(0.5)
        cl = Calibration()
        detected = False
        # lc = LaserController(640,480)

        while not self.stopped:
            ret, frame = self.videoStream.read()
            if ret:
                # frame = cl.mapImage(frame)
                # https://stackoverflow.com/a/55468544/6622587
                # frame = fd.detect(frame)
                self.frame.emit(frame)
                # self.coordinates.emit((fd.startX, fd.startY))
                # lc.sendCoords(fd.startX, fd.startY, fd.endX, fd.endY)
                # if fd.detected:
                #     if not detected:
                #         self.play.emit(1)
                #     detected = True
                # else:
                #     if detected:
                #         self.play.emit(2)
                #     detected = False

                # rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # h, w, ch = rgb_image.shape
                # bytesPerLine = ch * w
                # convertToQtFormat = QtGui.QImage(rgb_image.data, w, h, bytesPerLine, QtGui.QImage.Format_RGB888)
                # p = convertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
                # self.image.emit(p)
        # self.image.emit(QImage("resources/bg3.jpg"))
        self.finished.emit()

    def stop(self):
        self.stopped = True
        # self.videoStream.release()


class Detector(QObject):
    finished = pyqtSignal()
    image = pyqtSignal(QImage)
    coordinates = pyqtSignal(object)
    play = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.stopped = False
        self.spottedSound = QSound("resources/voices/target_aquaired.wav")
        self.searchingSound = QSound("resources/voices/searching.wav")
        self.frame = []

    def run(self):
        print("Starting Detection")
        self.stopped = False
        fd = FaceDetector(0.5)
        detected = False
        # lc = LaserController(640,480)

        while not self.stopped:

            if len(self.frame)>0:

                frame = fd.detect(self.frame)
                self.coordinates.emit((fd.startX, fd.startY))
                # lc.sendCoords(fd.startX, fd.startY, fd.endX, fd.endY)
                if fd.detected:
                    if not detected:
                        self.play.emit(1)
                    detected = True
                else:
                    if detected:
                        self.play.emit(2)
                    detected = False

                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytesPerLine = ch * w
                convertToQtFormat = QtGui.QImage(rgb_image.data, w, h, bytesPerLine, QtGui.QImage.Format_RGB888)
                p = convertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
                self.image.emit(p)
        self.image.emit(QImage("resources/bg3.jpg"))
        self.finished.emit()

    def stop(self):
        self.stopped = True
        # self.videoStream.release()

    def updateFrame(self, frame):
        self.frame = frame


class App(QMainWindow):
    def __init__(self):
        super(App, self).__init__()
        self.conf = Conf("resources/config_minify.json")
        loadUi("gui2.ui", self)
        self.soundManager = self.initSounds()
        self.soundManager.setEnableSounds(self.conf["enable_sound"])
        self.soundManager.play("Activation")

        self.textSender = TwilioNotifier()

        self.loginButton.clicked.connect(self.login)
        self.backButton.clicked.connect(self.showDetectionPage)
        self.saveButton.clicked.connect(self.saveSettings)
        self.startButton.clicked.connect(self.startStream)
        self.stopButton.clicked.connect(self.stopStream)
        self.settingsButton.clicked.connect(self.showSettings)

        self.videoThread = QThread()
        self.videoStream = VideoStream()
        self.videoStream.moveToThread(self.videoThread)
        self.videoStream.frame.connect(self.updateFrame)
        # self.videoStream.image.connect(self.setImage)
        # self.videoStream.coordinates.connect(self.displayCoords)
        # self.videoStream.play.connect(self.playSound)
        self.videoStream.finished.connect(self.videoThread.quit)
        self.videoThread.started.connect(self.videoStream.long_running)
        self.videoThread.finished.connect(self.enable)

        self.detectionThread = QThread()
        self.detector = Detector()
        self.detector.moveToThread(self.detectionThread)
        self.detector.image.connect(self.setImage)
        self.detector.coordinates.connect(self.displayCoords)
        self.detector.play.connect(self.playSound)
        self.detector.finished.connect(self.detectionThread.quit)
        self.detectionThread.started.connect(self.detector.run)

    @pyqtSlot(object)
    def updateFrame(self, frame):
        self.detector.updateFrame(frame)

    @pyqtSlot()
    def login(self):
        username = self.userText.text()
        password = self.passText.text()
        if username == "admin" and password == "admin":
            self.sceneManager.setCurrentIndex(2)
            self.soundManager.play("Login")
        else:
            self.loginMessage.setText("Wrong username or password!")
        # TODO: check username and password

    @pyqtSlot()
    def showDetectionPage(self):
        self.sceneManager.setCurrentIndex(2)

    @pyqtSlot()
    def showSettings(self):
        self.stopStream()
        self.phoneText.setText(self.conf["phone"])
        self.intervalText.setText(self.conf["interval"])
        self.notificationBox.setChecked(self.conf["enable_notifications"])
        self.muteBox.setChecked(self.conf["enable_sound"])
        self.sceneManager.setCurrentIndex(1)

    @pyqtSlot()
    def saveSettings(self):
        phone = self.phoneText.text()
        interval = self.intervalText.text()
        enableNotifications = self.notificationBox.isChecked()
        enableSound = self.muteBox.isChecked()
        try:
            int(phone)
            int(interval)
            self.errorMessage.setText("")
            data = {
                "phone": phone,
                "interval": interval,
                "enable_notifications": enableNotifications,
                "enable_sound": enableSound
            }
            self.conf.save("resources/config_minify.json", data)
            self.soundManager.setEnableSounds(self.conf["enable_sound"])
            self.soundManager.play("Save")
        except ValueError:
            self.errorMessage.setText("Invalid inputs!")
            self.soundManager.play("Error")

    @pyqtSlot(QImage)
    def setImage(self, image):
        self.imageLabel.setPixmap(QPixmap.fromImage(image))

    @pyqtSlot()
    def startStream(self):
        self.startButton.setEnabled(False)
        self.coords.setText("hello")
        self.soundManager.play("DetectionMode")
        # self.detector.start()
        self.videoThread.start()
        self.detectionThread.start()

    @pyqtSlot()
    def enable(self):
        self.startButton.setEnabled(True)

    @pyqtSlot()
    def stopStream(self):
        self.coords.setText("hello")
        self.soundManager.play("SleepMode")
        self.detector.stop()
        self.videoStream.stop()

    @pyqtSlot(object)
    def displayCoords(self, coords):
        (x, y) = coords
        self.coords.setText("X: " + str(x) + " Y: " + str(y))

    @pyqtSlot(int)
    def playSound(self, sound):
        if sound == 1:
            self.soundManager.play("Spotted")
            self.textSender.send(self.conf, "Intruder Detected!")
        else:
            self.soundManager.play("Searching")

    def initSounds(self):
        sounds = {
            "DetectionMode": QSound("resources/voices/detect_start.wav"),
            "SleepMode": QSound("resources/voices/sleep_mode.wav"),
            "Activation": QSound("resources/voices/activated.wav"),
            "Spotted": QSound("resources/voices/target_aquaired.wav"),
            "Shutdown": QSound("resources/voices/shutdown.wav"),
            "Searching": QSound("resources/voices/searching.wav"),
            "StartUp": QSound("resources/voices/startup.mp3"),
            "Login": QSound("resources/voices/login_sound.wav"),
            "Save": QSound("resources/voices/save_sound.wav"),
            "Error": QSound("resources/voices/error.wav"),
            "Moron": QSound("resources/voices/hey_moron.wav")
        }
        return SoundManager(sounds)

    def closeEvent(self, *args, **kwargs):
        print("hello")


def main():
    sys_argv = sys.argv
    sys_argv += ['--style', 'material']
    app = QApplication(sys.argv)
    widget = App()
    widget.show()
    sys._excepthook = sys.excepthook

    def exception_hook(exctype, value, traceback):
        print(exctype, value, traceback)
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)

    sys.excepthook = exception_hook
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
