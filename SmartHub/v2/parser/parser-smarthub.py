import paho.mqtt.client as mqtt
import json
import time
import configparser
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import queue

config = configparser.ConfigParser()
config.read("config.ini")

producer = KafkaProducer(bootstrap_servers=[f'{config["kafka"]["hostname"]}:{config["kafka"]["port"]}'], value_serializer = lambda x: json.dumps(x).encode("utf-8"))

data_to_send = queue.Queue()

class MQTTClient:
    def __init__(self, ip, port = 1883, username = None, password = None):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password

        self.client = mqtt.Client("parser-stv")

        if self.username is not None or self.password is not None:
            self.client.username_pw_set(self.username if self.username is not None else "", \
                                        self.password if self.password is not None else "")

        self.client.connect(self.ip, int(self.port))

    def publish(self, topic, message):
        _ = self.client.publish(topic, message)

    def subscribe(self, topic, on_message_fnc):
        self.client.on_message = on_message_fnc
        self.client.subscribe(topic)

def parser(client, userdata, message):
    data_to_send.put({"topic" : message.topic, "data" : json.loads(message.payload.decode('utf8'))})

broker = MQTTClient(ip = config["broker"]["ip"], port = config["broker"]["port"], username = config["broker"]["username"], password = config["broker"]["password"])
broker.subscribe("smarthub/#", parser)
broker.client.loop_start()

if __name__ == "__main__":
    try:
        while True:
            data = data_to_send.get()
            print(data)
            
            producer.send(topic = "smarthub", value = data["data"], key = bytes(data["topic"], "utf-8"))
            producer.flush()

            data_to_send.task_done()
    except:
        data_to_send.join()
        broker.client.disconnect()
        broker.client.loop_stop()