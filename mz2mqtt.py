import asyncio
import logging
from queue import SimpleQueue

import paho.mqtt.client as mqtt_client
import mzlib
import yaml

async def main() -> None:

    cmd_queue = SimpleQueue()

    def create_msg(object, vehicleid, mqtt_topic, indent='/'):
        for key in object:
            if type(object[key]) == dict:
                create_msg(object[key], vehicleid, mqtt_topic, indent + key + '/')
            else:
                mqttc.publish(mqtt_topic + '/' + str(vehicleid) + indent + key, object[key], 0, True)
        return

    async def get_and_publish(vehicle):
        logging.info('get and publish data for ' + vehicle['vin'])
        vehicle_status = await mazda_client.get_vehicle_status(vehicle['id'])
        create_msg(vehicle_status, vehicle['vin'], mqtt_topic)
        if vehicle['isElectric']:
            vehicle_ev_status = await mazda_client.get_ev_vehicle_status(vehicle['id'])
            create_msg(vehicle_ev_status, vehicle['vin'], mqtt_topic)

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logging.info("MQTT connected OK")
        else:
            logging.error("Bad connection Returned code=", rc)

    def on_message(mosq, obj, msg):
        msg.payload = str(msg.payload)
        logging.info("received " + msg.topic + " " + msg.payload)
        mqtt_cmd = msg.topic.split("/")
        if mqtt_cmd[1].upper() == "SET":
            cmd_queue.put(mqtt_cmd[2] + ':' + mqtt_cmd[3] + ':' + msg.payload)

    logger = logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                                 datefmt='%Y-%m-%d %H:%M:%S',
                                 level=logging.INFO)

    # Read Config
    with open('config.yaml', 'r') as configfile:
        config = yaml.safe_load(configfile)

    # Connect to myMazda
    logging.info('Initialize myMazda')
    mazda_user = config['mazda']['user']
    mazda_password = config['mazda']['password']
    mazda_region = config['mazda']['region'] or 'MME'
    mazda_client = mzlib.Client(mazda_user, mazda_password, mazda_region, use_cached_vehicle_list=True)

    status_wait = (config['status']['wait'] or 30) * 12
    status_refreshwait = (config['status']['refreshwait'] or 2) * 60

    # Connect to MQTT-Broker
    logging.info('Initalize MQTT')
    mqtt_broker_address = config['mqtt']['host']
    mqtt_broker_port = config['mqtt']['port'] or 1883
    mqtt_broker_user = config['mqtt']['user'] or None
    mqtt_broker_password = config['mqtt']['password'] or None
    mqtt_topic = config['mqtt']['topic'] or 'mz2mqtt'
    mqtt_clientname = config['mqtt']['clientname'] or 'mz2mqtt'

    mqttc = mqtt_client.Client(mqtt_clientname)
    mqttc.enable_logger(logger)
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    mqttc.username_pw_set(username=mqtt_broker_user, password=mqtt_broker_password)
    mqttc.connect(mqtt_broker_address, mqtt_broker_port, 60)
    mqttc.subscribe(mqtt_topic + '/' + 'SET/#', 0)
    mqttc.loop_start()

    # Get all Vehicles and publish base
    logging.info('Get all vehicles')
    try:
        vehicles = await mazda_client.get_vehicles()
    except Exception:
        raise Exception("Failed to get list of vehicles")

    # Publish vehicle data
    logging.info('publish all vehicles base data')
    for vehicle in vehicles:
        create_msg(vehicle,vehicle['vin'], mqtt_topic)

    # refresh all vehicle data at startup
    try:
        for vehicle in vehicles:
            logging.info('refresh data for ' + vehicle['vin'])
            await mazda_client.refresh_vehicle_status(vehicle['id'])
    except:
        logging.error('can not refresh all vehicles data')
        await mazda_client.close()

    logging.info('wait ' + str(status_refreshwait) + 's for data after refresh')
    await asyncio.sleep(status_refreshwait)

    # Main loop
    try:
        count = 0
        while True:
            # look for new API input
            while not cmd_queue.empty():
                r = cmd_queue.get_nowait()
                mqtt_cmd = r.split(':')
                match mqtt_cmd[1]:
                    case 'refresh':
                        found = False
                        for vehicle in vehicles:
                            if vehicle['vin'] == mqtt_cmd[0]:
                                found = True
                                logging.info('send refresh for ' + vehicle['vin'] +  ' and wait' + str(status_refreshwait) + 's')
                                await mazda_client.refresh_vehicle_status(vehicle['id'])
                                await asyncio.sleep(status_refreshwait)
                                await get_and_publish(vehicle)
                        if not found:
                            logging.error('VIN ' + mqtt_cmd[0] + ' not found')
                    case _:
                        logging.error("invalid command: " + mqtt_cmd[1])

            # wait time reached and get data
            if count == 0:
                for vehicle in vehicles:
                    await get_and_publish(vehicle)
                    count = status_wait

            count -= 1
            await asyncio.sleep(5)
    except:
        # Close the session
        mqttc.loop_stop()
        await mazda_client.close()


if __name__ == "__main__":
    asyncio.run(main())
