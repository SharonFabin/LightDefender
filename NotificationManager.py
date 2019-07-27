from twilio.rest import Client
from threading import Thread
from datetime import datetime


class TwilioNotifier:
    def __init__(self, interval=10):
        self.interval = interval
        self.lastSent = datetime.strptime('2017-05-04', "%Y-%m-%d")

    def send(self, conf, msg):
        t = Thread(target=self._send, args=(conf, msg,))
        t.start()

    def _send(self, conf, msg):
        if conf["enable_notifications"]:
            delta = datetime.now() - self.lastSent
            if delta.seconds>int(conf["interval"])*60:
                self.lastSent = datetime.now()
                client = Client(conf["twilio_sid"], conf["twilio_auth"])
                client.messages.create(to=conf["phone"], from_=conf["twilio_from"], body=msg)

    def addNewNumber(self, conf, userName, number):
        client = Client(conf["twilio_sid"], conf["twilio_auth"])
        outgoing_caller_ids = client.outgoing_caller_ids.list(limit=20)
        callNumber = "+972"+number[1:]
        for record in outgoing_caller_ids:
            if callNumber in record.phone_number:
                return callNumber

        validation_request = client.validation_requests \
            .create(
            friendly_name=userName,
            phone_number=callNumber
        )
        return callNumber

    def updateNumer(self, conf, phoneNumnber, newName):
        client = Client(conf["twilio_sid"], conf["twilio_auth"])
        outgoing_caller_ids = client.outgoing_caller_ids.list(limit=20)
        callNumber = "+972" + phoneNumnber[1:]
        sid = ""
        for record in outgoing_caller_ids:
            if callNumber in record.phone_number:
                sid = record.sid
        if len(sid)>0:
            outgoing_caller_id = client \
                .outgoing_caller_ids(sid) \
                .update(friendly_name=newName)
            print(outgoing_caller_id.friendly_name)






