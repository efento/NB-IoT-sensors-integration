import base64
import datetime
import asyncio
import os.path
import time
import logging

import aiocoap.resource as resource
import aiocoap
from protobuf import proto_measurements_pb2
from protobuf import proto_device_info_pb2
from protobuf import proto_config_pb2
from google.protobuf.json_format import MessageToDict
import psycopg2

# Add new logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# To save logs to a file set debug_logs to true
debug_logs = True

# Enter your database host, database user, database password and database name
DATABASE_HOST = 'host_name';
DATABASE_USER = 'database_user';
DATABASE_PASSWORD = 'database_password';
DATABASE_NAME = 'database_name';

# Making the initial connection:
conn = psycopg2.connect(
    dbname=DATABASE_NAME,
    user=DATABASE_USER,
    host=DATABASE_HOST,
    password=DATABASE_PASSWORD
)


class Tools:

    def __init__(self):
        self.time = int(time.time())

    def setTimestamp(self):
        # Serializing device config.
        device_config = proto_config_pb2.ProtoConfig()
        # Set request_device_info to true
        device_config.request_device_info = True
        # Sending current time to the sensor in order to synchronise its internal clock
        device_config.current_time = self.time
        return device_config.SerializeToString()


# Measurements - Class used to handle Measurement messages sent by the sensor
class Measurements(resource.Resource):

    def __init__(self):
        super().__init__()

    async def render_post(self, request):
        # Creating a dictionary from a received message.
        data = [MessageToDict(proto_measurements_pb2.ProtoMeasurements().FromString(request.payload), True)]

        record = []
        changeAt = []
        tools = Tools()
        response_payload = tools.setTimestamp()

        # iteration in list data
        for measurement in data:
            measurementPeriod = measurement['measurementPeriodBase'] * measurement['measurementPeriodFactor']
            # Keep this log format to facilitate troubleshooting with Efento support
            logger.info(" request: " + str(request) + " serial number: " + str(
                base64.b64decode((measurement['serialNum'])).hex()) + " payload: " + str(
                request.payload.hex()))

            for param in measurement['channels']:
                # iteration in list data/measurement/channels/sampleOffsets.
                # Creating a list of sensor parameters(measured_at,serial_number, battery_status)
                # and measurement results with sample offset
                if param != {}:
                    if param['type'] == "MEASUREMENT_TYPE_OK_ALARM":
                        numberOfMeasurements = 1 + (abs(param['sampleOffsets'][-1]) - 1) / measurementPeriod
                        for sampleOffset in param['sampleOffsets']:
                            timeDifference = abs(sampleOffset) - 1
                            if sampleOffset > 0:
                                changeAt.extend([param['timestamp'] + timeDifference, "Alarm"])
                            elif sampleOffset < 1:
                                changeAt.extend([param['timestamp'] + timeDifference, "OK"])
                        for measurementNumber in range(int(numberOfMeasurements)):
                            timeDifference = measurementPeriod * measurementNumber
                            if param['timestamp'] + timeDifference in changeAt:
                                value = changeAt[changeAt.index(param['timestamp'] + timeDifference) + 1]
                            record.extend([(datetime.datetime.fromtimestamp(param['timestamp'] + timeDifference),
                                            base64.b64decode((measurement['serialNum'])).hex(),
                                            measurement['batteryStatus'],
                                            param['type'].replace("MEASUREMENT_TYPE_", ""), value)])
                    else:
                        for index, sampleOffset in enumerate(param['sampleOffsets']):
                            if param['type'] == "MEASUREMENT_TYPE_TEMPERATURE" or param[
                                'type'] == "MEASUREMENT_TYPE_ATMOSPHERIC_PRESSURE":
                                value = (param['startPoint'] + sampleOffset) / 10
                            else:
                                value = param['startPoint'] + sampleOffset
                            timeDifference = measurementPeriod * index

                            record.extend([(datetime.datetime.fromtimestamp(param['timestamp'] + timeDifference),
                                            base64.b64decode((measurement['serialNum'])).hex(),
                                            measurement['batteryStatus'],
                                            param['type'].replace("MEASUREMENT_TYPE_", ""),
                                            value)])

        measurements = "INSERT INTO measurements(measured_at, serial_number, battery_ok, type, value) VALUES (%s, %s, %s, %s, %s)"
        with conn.cursor() as cur:
            try:
                # inserting a list of sensor parameters and measurement to table in PostgresSQL
                cur.executemany(measurements, record)
                conn.commit()
                cur.close()
                code = aiocoap.Code.CREATED
            except (Exception, psycopg2.DatabaseError) as error:
                print(error)
                code = aiocoap.Code.INTERNAL_SERVER_ERROR

        # returning "ACK" and response payload to the sensor
        response = aiocoap.Message(mtype=aiocoap.ACK, code=code,
                                   token=request.token, payload=response_payload)
        logger.info(" response: " + str(response) + " payload: " + str(response.payload.hex()))
        return response


# DeviceInfo - Class used to handle Device Info messages sent by the sensor
class DeviceInfo(resource.Resource):

    def __init__(self):
        super().__init__()

    async def render_post(self, request):
        logger.info(" request: " + str(request) + " payload: " + str(request.payload.hex()))
        # Creating a dictionary from a message received from a sensor
        data = [MessageToDict(proto_device_info_pb2.ProtoDeviceInfo().FromString(request.payload), True)]
        tools = Tools()
        response_payload = tools.setTimestamp()

        # Create the file "Deviceinfo.txt" and save the date in this file
        if not os.path.isfile("Deviceinfo.txt"):
            file = open("Deviceinfo.txt", 'x')
        else:
            file = open("Deviceinfo.txt", 'w')
        file.write(str(data))
        file.close()

        # returning "ACK" to the sensor
        response = aiocoap.Message(mtype=aiocoap.ACK, code=aiocoap.Code.CREATED,
                                   token=request.token, payload=response_payload)
        logger.info(" response: " + str(response))
        return response


# Configuration - Class used to handle Configuration messages sent by the sensor
class Configuration(resource.Resource):

    def __init__(self):
        super().__init__()

    async def render_post(self, request):

        logger.info(" request: " + str(request) + " payload: " + str(request.payload.hex()))
        # Creating a dictionary from a message received from a sensor
        data = [MessageToDict(proto_config_pb2.ProtoConfig().FromString(request.payload), True)]
        tools = Tools()
        response_payload = tools.setTimestamp()
        # Create the file "Configuration.txt" and save the date in this file
        if not os.path.isfile("Configuration.txt"):
            file = open("Configuration.txt", 'x')
        else:
            file = open("Configuration.txt", 'w')
        file.write(str(data))
        file.close()

        # returning "ACK" to the sensor
        response = aiocoap.Message(mtype=aiocoap.ACK, code=aiocoap.Code.CREATED,
                                   token=request.token, payload=response_payload)
        logger.info(" response: " + str(response))
        return response


# Time - Class used to handle Time messages sent by the sensor
class Time(resource.Resource):

    def __init__(self):
        super().__init__()

    async def render_post(self, request):
        logger.info(" request: " + str(request) + " payload: " + str(request.payload.hex()))
        time_stamp = int(time.time())
        time_stamp_hex = hex(time_stamp)

        # returning timestamp to the sensor
        response = aiocoap.Message(mtype=aiocoap.ACK, code=aiocoap.Code.CREATED,
                                   token=request.token, payload=bytearray.fromhex(time_stamp_hex[2:]))
        logger.info(" response: " + str(response) + " payload: " + str(response.payload.hex()))
        return response


async def main():
    # Resource tree creation
    root = resource.Site()
    # Set up “m” endpoint, which will be receiving measurements sent by Efento NB-IoT sensor using POST method
    root.add_resource(["m"], Measurements())
    # Set up “i” endpoint, which will be receiving device info messages sent by Efento NB-IoT sensor using POST method
    root.add_resource(["i"], DeviceInfo())
    # Set up “c” endpoint, which will be receiving configuration messages sent by Efento NB-IoT sensor using POST method
    root.add_resource(["c"], Configuration())
    # Set up “t” endpoint, which will be receiving time sent by Efento NB-IoT sensor using POST method
    root.add_resource(["t"], Time())

    # Starting the application on set IP address and port.
    await aiocoap.Context.create_server_context(root, ("192.168.120.132", 5681))
    # Getting the current event loop and create an asyncio.Future object attached to the event loop.
    await asyncio.get_running_loop().create_future()


if __name__ == '__main__':
    # Logging to a file
    if debug_logs is True:
        file_handler = logging.FileHandler(filename='logs.log', mode="w")
        formatter = logging.Formatter('%(asctime)s %(message)s', '%m/%d/%Y %I:%M:%S')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    # Run the coroutine, taking care of managing the asyncio event loop,
    asyncio.run(main())
