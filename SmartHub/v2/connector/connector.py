from multiprocessing import Semaphore
import paho.mqtt.client as mqtt
import configparser
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import time
import json
from threading import Thread
import queue
import json

config = configparser.ConfigParser()
config.read("config.ini")

to_publish = queue.Queue()
thingsboard = None

class MQTTClient:
    def __init__(self, ip, port = 1883, username = None, password = None):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password

        self.client = mqtt.Client("connector-stv")

        if self.username is not None or self.password is not None:
            self.client.username_pw_set(self.username if self.username is not None else "", \
                                        self.password if self.password is not None else "")

        self.client.connect(self.ip, int(self.port))

    def publish(self, topic, message):
        _ = self.client.publish(topic, message)

def thread_publish():
    while True:
        item = to_publish.get()
        print(item.value)
        thingsboard.publish("v1/devices/me/telemetry", json.dumps(item.value))
        to_publish.task_done()

if __name__ == "__main__":
    try:
        thingsboard = MQTTClient(ip = config["thingsboard"]["ip"], port = config["thingsboard"]["port"], username = config["thingsboard"]["access_token"])
        thingsboard.client.loop_start()

        Thread(target = thread_publish, daemon = True).start()

        consumer = KafkaConsumer(group_id='my-group',
                                bootstrap_servers=[f'{config["kafka"]["hostname"]}:{config["kafka"]["port"]}'],
                                auto_offset_reset="latest",
                                enable_auto_commit=False,
                                value_deserializer=lambda msg: json.loads(msg.decode("utf-8")))

        consumer.subscribe(topics = ("smarthub"))

        for message in consumer:
            to_publish.put(message)
                     
        to_publish.join()

    except Exception as e:
        print(e)
        thingsboard.client.disconnect()
        thingsboard.client.loop_stop()