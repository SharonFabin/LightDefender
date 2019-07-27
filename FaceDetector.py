import numpy as np
import cv2
import datetime

class FaceDetector:
    net = {}
    accuracy = 0.5

    def __init__(self, accuracy=0.5):
        self.accuracy = accuracy
        self.startX = 0
        self.startY = 0
        self.endX = 0
        self.endY = 0
        self.initNeuralNetwork()
        self.detected = False

    def initNeuralNetwork(self):
        deploy = "resources/deploy.prototxt.txt"
        model = "resources/res10_300x300_ssd_iter_140000.caffemodel"
        self.net = cv2.dnn.readNetFromCaffe(deploy, model)

    def detect(self, frame):
        (h, w) = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
        self.net.setInput(blob)
        detections = self.net.forward()
        self.detected = False
        for i in range(0, detections.shape[2]):
            probability = detections[0, 0, i, 2]
            if probability < self.accuracy:
                continue
            self.detected = True

            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")

            self.startX = startX
            self.startY = startY
            self.endX = endX
            self.endY = endY

            text = "{:.2f}%".format(probability * 100)
            y = startY - 10 if startY - 10 > 10 else startY + 10
            cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 0, 255), 2)
            cv2.putText(frame, text, (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 2)

        return frame
