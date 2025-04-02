
# mz2mqtt
**Publish all Car Data to MQTT**

![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)
![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)
---
># !!! WARNING !!!  !!! WARNING !!!
>***A too frequent refresh of the data can discharge your 12V starter battery of the car.  
So use this Program at your own risk***
---

This Program based on code from bdr99, and it may stop working at any time without warning.

---

Prerequisites:
1. Set up your Car in the app.
2. Create a second Driver for mz2mqtt.

## Installation Guide:
Clone the git repository.  
Create a virtual environment and install the requirements:  
```
apt install python-virtualenv
cd mz2mqtt 

virtualenv -p python3 ../mz2mqtt.env
source ../mz2mqtt.env/bin/activate

pip3 install -r requirements.txt
```
Then copy config_example.yaml to config.yaml an insert your data.  
Start mz2mqtt:
```
cd mz2mqtt
source ../mz2mqtt.env/bin/activate
python mz2mqtt.py
```

Or download the Docker Image
```
docker pull ghcr.io/c64axel/mz2mqtt:main
```
Start the container with /usr/src/app/config.yaml mapped to the config file
```
docker run -d --name mz2mqtt --restart unless-stopped -v <YOUR_DIR/config.yaml>:/usr/src/app/config.yaml mz2mqtt:main
```
---
**MQTT-API**

To trigger a manual refresh for one car, publish the following via MQTT:  
(replace < VIN > with the VIN of the Car)
```
mz2mqtt/SET/<VIN>/refresh
```

---
### History:

| Date       | Change                                                              |
|------------|---------------------------------------------------------------------|
| 26.04.2023 | Initial Version                                                     |
| 03.06.2023 | only one refresh at the beginning because risk of battery discharge |
| 08.06.2023 | refresh Data via MQTT                                               |

