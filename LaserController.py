import serial
import serial.tools.list_ports


class LaserController:

    def __init__(self, frameHeight, frameWidth):
        comPorts = list(serial.tools.list_ports.comports())
        self.connection = serial.Serial(comPorts[0][0], 9600)
        self.height = frameHeight
        self.width = frameWidth
        self.xPos = 90
        self.yPos = 90


    @staticmethod
    def listPorts():
        comPorts = list(serial.tools.list_ports.comports())
        for port in comPorts:
            print(port[0])

    def sendCoords(self, startX, startY, endX, endY):
        self.fourCornersManualMethod(startX,startY,endX,endY)
        self.send(str(self.xPos) + ":" + str(self.yPos))

    def sendAngle(self, x, y):
        self.send(str(x) + ":" + str(y))

    def toggleLaser(self):
        self.send("t")

    def startLaser(self):
        self.send("start")

    def stopLaser(self):
        self.send("stop")

    def fourCornersManualMethod(self, x1, y1, x2, y2):
        sY = 69
        sX = 63
        eY = 103
        eX = 109
        midX = 84
        midY = 88
        lY = eY - sY
        lX = eX - sX
        self.xPos = int(lX - ((x1 + x2) / 2 / self.width) * lX + sX)
        self.yPos = int((y1 + y2) / 2 / self.height * lY + sY)

    def send(self, string):
        self.connection.write(string.encode())

