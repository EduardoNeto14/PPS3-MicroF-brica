import paho.mqtt.client as mqtt
import random
import configparser
import time

config = configparser.ConfigParser()
config.read("config.ini")

global client_broker
global client_thingsboard
global wait_to_connect

wait_to_connect = False

def connect_broker():
    def on_connect(client, userdata, flags, rc):
        global wait_to_connect

        if rc == 0:
            print("Connected to MQTT Broker!")
            wait_to_connect = True
        else:
            print(f"Failed to connect, return code {rc}\n")

    client = mqtt.Client("Shelly-Parser")
    # client.username_pw_set(config["broker"]["user"], config["broker"]["passwd"])
    client.on_connect = on_connect
    client.connect(config["broker-local"]["ip"], int(config["broker-local"]["port"]))
    return client

# def connect_thingsboard():
#     def on_connect(client, userdata, flags, rc):
#         global wait_to_connect
#         if rc == 0:
#             print("Connected to Thingsboard!")
#             wait_to_connect = True
#         else:
#             print(f"Failed to connect, return code {rc}\n")

#     client = mqtt.Client("thingsboard-connector")
#     client.username_pw_set(config["thingsboard"]["access_token"], "")
#     client.on_connect = on_connect
#     client.connect(config["thingsboard"]["ip"], int(config["thingsboard"]["port"]))
#     return client

# def publish(client, topic, msg):
#     result = client.publish(topic, msg)
#     status = result[0]
    
#     if status == 0:
#         print(f"Send `{msg}` to topic `{topic}`")
#     else:
#         print(f"Failed to send message to topic {topic}")

def subscribe(client, topic):
    def on_message(client, userdata, msg):
        # client_thingsboard.publish("v1/devices/me/telemetry", msg.payload.decode())
        parse_topic = msg.topic.split("/")
        data = msg.payload.decode()

        if data == "on":
            data = 1
        elif data == "off":
            data = 0
        else:
            data = float(data)
        
        gen_msg = {
            "timestamp" : time.time(),
            "id" : parse_topic[1],
            "measure" : parse_topic[-1] if len(parse_topic) == 5 else parse_topic[-2],
            "channel" : parse_topic[-2] if len(parse_topic) == 5 else parse_topic[-1],
            "value" : data
        }

        print(gen_msg)
        
    client.on_message = on_message
    client.subscribe(topic)

def run():
    global client_broker
    #global client_thingsboard
    global wait_to_connect
    
    client_broker = connect_broker()
    subscribe(client_broker, "shellies/#")
    client_broker.loop_start()
    
    #print(wait_to_connect)

    #while not wait_to_connect:
    #    time.sleep(0.05)
    
    #wait_to_connect = False

    #client_thingsboard = connect_thingsboard()
    #client_thingsboard.loop_start()

if __name__ == "__main__":
    try:
        run()
        while True:
            pass
    except Exception as e:
        print(e)
        client_broker.disconnect()
        client_broker.loop_stop()

        #client_thingsboard.disconnect()
        #client_thingsboard.loop_stop()