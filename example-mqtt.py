#!/usr/bin/env python
import subprocess
import paho.mqtt.client as mqtt
import fauxmo
from debounce_handler import debounce_handler
import threading
import logging
import time
logging.basicConfig(level=logging.DEBUG)

# ---------- Network constants -----------
ECHO_LIVINGROOM = "192.168.1.53"
ECHO_KITCHEN  = "192.168.1.243"
MQTT_HOST = "jarvis"
MQTT_PORT = 1883

# ---------- Device callback functions ----------
class light_handler(debounce_handler):
    """Publishes state to two different lighting MQTT topics
       depending on which Echo the request came from.
    """
    TRIGGERS = {"lights": 52002, "lamp": 52003}

    def __init__(self, mqtt):
        debounce_handler.__init__(self)
        self.mqtt = mqtt

    def act(self, client_address, state):
        if client_address == ECHO_LIVINGROOM:
            self.mqtt.publish("livingroom", state)
            print "Published to living room"
        elif client_address == ECHO_KITCHEN:
            self.mqtt.publish("kitchen", state)
            print "Published to kitchen"
        return True

if __name__ == "__main__":
    # Startup the MQTT client in a separate thread
    client = mqtt.Client()
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    ct = threading.Thread(target=client.loop_forever)
    ct.daemon = True
    ct.start()

    # Startup the fauxmo server
    fauxmo.DEBUG = True
    p = fauxmo.poller()
    u = fauxmo.upnp_broadcast_responder()
    u.init_socket()
    p.add(u)

    # Register each device callback as a fauxmo handler
    h = light_handler(client)
    for trig, port in h.TRIGGERS.items():
        fauxmo.fauxmo(trig, u, p, None, port, h)

    # Loop and poll for incoming Echo requests
    logging.debug("Entering fauxmo polling loop")
    while True:
        try:
            # Allow time for a ctrl-c to stop the process
            p.poll(100)
            time.sleep(0.1)
        except Exception, e:
            logging.critical("Critical exception: " + str(e))
            break