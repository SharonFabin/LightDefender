import sys
import time

import cv2
from PyQt5 import QtGui, QtCore, QtMultimedia
from PyQt5.QtCore import pyqtSlot, QThread, QObject, pyqtSignal, Qt, QUrl
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox
from PyQt5.uic import loadUi
from PyQt5.QtMultimedia import QSound
from PyQt5.QtWidgets import QSplashScreen
from playsound import playsound
from FaceDetector import FaceDetector
from Configuration import Conf
from NotificationManager import TwilioNotifier
from SoundManager import SoundManager
from LaserController import LaserController
from calibrate import Calibration


class VideoStream(QObject):
    finished = pyqtSignal()
    image = pyqtSignal(QImage)
    pic = pyqtSignal(object)
    play = pyqtSignal(int)
    coordinates = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.videoStream = None
        self.stopped = False

    def long_running(self):
        print("Starting")
        self.stopped = False
        self.videoStream = cv2.VideoCapture(0)
        fd = FaceDetector(0.5)
        cl = Calibration()
        detected = False

        while not self.stopped:
            ret, frame = self.videoStream.read()
            if ret:
                self.pic.emit(frame)
                frame = fd.detect(frame)
                self.coordinates.emit((fd.startX, fd.startY, fd.endX, fd.endY))
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


class App(QMainWindow):
    def __init__(self):
        super(App, self).__init__()
        self.conf = Conf("resources/config_minify.json")
        loadUi("gui2.ui", self)

        self.soundManager = self.initSounds()
        self.soundManager.setEnableSounds(self.conf["enable_sound"])
        self.soundManager.play("Activation")
        self.textSender = TwilioNotifier()
        self.faceRecognition = False
        self.picCounter = 0
        self.lc = None

        self.loginButton.clicked.connect(self.login)
        self.backButton.clicked.connect(self.showDetectionPage)
        self.saveButton.clicked.connect(self.saveSettings)
        self.startButton.clicked.connect(self.startStream)
        self.stopButton.clicked.connect(self.stopStream)
        self.settingsButton.clicked.connect(self.showSettings)

        self.videoThread = QThread()
        self.videoStream = VideoStream()
        self.videoStream.moveToThread(self.videoThread)
        self.videoStream.image.connect(self.setImage)
        self.videoStream.coordinates.connect(self.sendCoords)
        self.videoStream.play.connect(self.playSound)
        self.videoStream.finished.connect(self.videoThread.quit)
        self.videoThread.started.connect(self.videoStream.long_running)
        self.videoThread.finished.connect(self.enable)
        self.x = 90
        self.y = 90
        # self.topLeftX = 120
        # self.topLeftY = 77
        # self.bottomRightX = 70
        # self.bottomRightY = 113
        self.topLeftX = 119
        self.topLeftY = 71
        self.bottomRightX = 71
        self.bottomRightY = 108

    @pyqtSlot()
    def login(self):
        username = self.userText.text()
        password = self.passText.text()
        try:
            self.lc = LaserController(640, 480)
            if username == "admin" and password == "admin":
                self.sceneManager.setCurrentIndex(3)
                self.soundManager.play("Login")
            else:
                self.loginMessage.setText("Wrong username or password!")
        except Exception as e:
            self.loginMessage.setText("Please Connect Laser!")
            print(str(e))
        # TODO: add user database

    @pyqtSlot()
    def showDetectionPage(self):
        self.sceneManager.setCurrentIndex(3)

    @pyqtSlot()
    def showSettings(self):
        self.stopStream()
        self.phoneText.setText("0" + self.conf["phone"][4:])
        self.intervalText.setText(self.conf["interval"])
        self.notificationBox.setChecked(self.conf["enable_notifications"])
        self.muteBox.setChecked(self.conf["enable_sound"])
        self.autoRadio.setChecked(self.conf["auto_mode"])
        self.manualRadio.setChecked(not self.conf["auto_mode"])
        self.sceneManager.setCurrentIndex(1)

    @pyqtSlot()
    def saveSettings(self):
        phone = self.phoneText.text()
        interval = self.intervalText.text()
        enableNotifications = self.notificationBox.isChecked()
        enableSound = self.muteBox.isChecked()
        autoMode = self.autoRadio.isChecked()
        try:
            int(phone)
            int(interval)
            phone = self.textSender.addNewNumber(self.conf, "admin", phone)

            ##self.textSender.updateNumer(self.conf, phone, "admin")
            # self.textSender.showNumbers(self.conf)
            self.errorMessage.setText("")
            data = {
                "phone": phone,
                "interval": interval,
                "enable_notifications": enableNotifications,
                "enable_sound": enableSound,
                "auto_mode": autoMode
            }
            self.conf.save("resources/config_minify.json", data)
            self.soundManager.setEnableSounds(self.conf["enable_sound"])
            self.soundManager.play("Save")
        except ValueError:
            self.errorMessage.setText("Invalid inputs!")
            self.soundManager.play("Error")
        except Exception as e:
            self.errorMessage.setText("Cant change phone number!")
            print(str(e))
            self.soundManager.play("Error")

    @pyqtSlot(QImage)
    def setImage(self, image):
        self.imageLabel.setPixmap(QPixmap.fromImage(image))

    @pyqtSlot()
    def startStream(self):
        self.startButton.setEnabled(False)
        self.soundManager.play("DetectionMode")
        self.videoThread.start()

    @pyqtSlot()
    def enable(self):
        self.startButton.setEnabled(True)

    @pyqtSlot()
    def stopStream(self):
        self.soundManager.play("SleepMode")
        self.videoStream.stop()
        self.faceCoords.setText("")

    @pyqtSlot(object)
    def sendCoords(self, coords):
        (x1, y1, x2, y2) = coords
        cameraWidth = self.topLeftX - self.bottomRightX
        cameraHeight = self.bottomRightY - self.topLeftY
        x = int(cameraWidth - (x1 + x2) / 2 / 640 * cameraWidth) + self.bottomRightX
        y = int((y1 + y2) / 2 / 480 * cameraHeight) + self.topLeftY

        if self.conf["auto_mode"]:
            self.x = x
            self.y = y
            self.lc.send(str(self.x) + ":" + str(self.y))
            self.laserCoords.setText("X: " + str(self.x) + " Y: " + str(self.y))

        self.faceCoords.setText("X: " + str(x) + " Y: " + str(y))

    @pyqtSlot(int)
    def playSound(self, sound):
        if sound == 1:
            # TODO: blink the laser
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
            "Moron": QSound("resources/voices/hey_moron.wav"),
            "Daft": QSound("resources/voices/daftPunk.wav")
        }
        return SoundManager(sounds)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_T:
            self.lc.toggleLaser()
        if not self.conf["auto_mode"]:
            if e.key() == Qt.Key_W:
                if self.y > 0:
                    self.y -= 1
                    self.laserCoords.setText("X: " + str(self.x) + " Y: " + str(self.y))
                    self.lc.sendAngle(self.x, self.y)
            elif e.key() == Qt.Key_S:
                if self.y < 180:
                    self.y += 1
                    self.laserCoords.setText("X: " + str(self.x) + " Y: " + str(self.y))
                    self.lc.sendAngle(self.x, self.y)
            elif e.key() == Qt.Key_D:
                if self.x < 180:
                    self.x += 1
                    self.laserCoords.setText("X: " + str(self.x) + " Y: " + str(self.y))
                    self.lc.sendAngle(self.x, self.y)
            elif e.key() == Qt.Key_A:
                if self.x > 0:
                    self.x -= 1
                    self.laserCoords.setText("X: " + str(self.x) + " Y: " + str(self.y))
                    self.lc.sendAngle(self.x, self.y)
            elif e.key() == Qt.Key_R:
                self.x = 90
                self.y = 90
                self.laserCoords.setText("X: " + str(self.x) + " Y: " + str(self.y))
                self.lc.sendAngle(self.x, self.y)
            elif e.key() == Qt.Key_1:
                self.topLeftX = self.x
                self.topLeftY = self.y
                print(str(self.x) + " " + str(self.y))
            elif e.key() == Qt.Key_2:
                self.bottomRightX = self.x
                self.bottomRightY = self.y
                print(str(self.x) + " " + str(self.y))
            elif e.key() == Qt.Key_P:
                cv2.imwrite("sharon1/img_" + str(self.picCounter) + ".jpg", self.videoStream.pic)
                self.picCounter += 1
                if self.picCounter == 10:
                    self.picCounter = 0
                    self.faceRecognition = False
                    self.sceneManager.setCurrentIndex(1)

    def closeEvent(self, event):
        close = QMessageBox()
        close.setWindowTitle("Exit")
        close.setWindowIcon(QIcon("resources/bg4.jpg"))
        close.setText("Are you sure you want to exit?")
        close.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        close = close.exec()
        if close == QMessageBox.Yes:
            self.videoStream.stop()
            playsound("resources/voices/shutdown.wav")
            event.accept()
            print("System Shutdown")
        else:
            event.ignore()


def main():
    sys_argv = sys.argv
    sys_argv += ['--style', 'material']
    app = QApplication(sys.argv)
    splash_pix = QtGui.QPixmap('resources/splash.png')
    splash = QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
    splash.show()
    app.processEvents()
    widget = App()
    widget.show()
    splash.finish(widget)
    sys._excepthook = sys.excepthook

    def exception_hook(exctype, value, traceback):
        print(exctype, value, traceback)
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)

    sys.excepthook = exception_hook
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
