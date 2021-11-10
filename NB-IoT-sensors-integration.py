import base64
import datetime
import asyncio
import os.path
import time

import aiocoap.resource as resource
import aiocoap
from protobuf import proto_measurements_pb2, proto_device_info_pb2, proto_config_pb2
from google.protobuf.json_format import MessageToDict
import psycopg2

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


# Measurements - Class used to handle Measurement messages sent by the sensor
class Measurements(resource.Resource):

    def __init__(self):
        super().__init__()

    async def render_post(self, request):

        # Creating a dictionary from a message received from a sensor
        data = [MessageToDict(proto_measurements_pb2.ProtoMeasurements().FromString(request.payload))]
        record = []

        # iterating through 'data'
        for measurement in data:

            for param in measurement['channels']:
                # iteration in list data/measurement/channels/sampleOffsets.creating a list of sensor parameters(measured_at,serial_number, battery_status) and measurement results with sample offset
                try:
                    for sampleOffset in param['sampleOffsets']:
                        record.extend([(datetime.datetime.fromtimestamp(param['timestamp']),
                                        base64.b64decode((measurement['serialNum'])).hex(),
                                        measurement['batteryStatus'],
                                        param['type'], (param['startPoint'] + sampleOffset) / 10)])
                except:
                    print("")

                measurements = "INSERT INTO measurements(measured_at, serial_number, battery_ok, type, value) VALUES (%s, %s, %s, %s, %s)"
                with conn.cursor() as cur:
                    try:
                        # inserting a list of sensor parameters and measurement to table in PostgresSQL
                        cur.executemany(measurements, record)
                        conn.commit()
                        cur.close()
                    except (Exception, psycopg2.DatabaseError) as error:
                        print(error)
        # returning "ACK"  to the sensor
        return aiocoap.Message(mtype=aiocoap.ACK, code=aiocoap.Code.CREATED,
                               token=request.token, payload="")


# DeviceInfo - Class used to handle Device Info messages sent by the sensor
class DeviceInfo(resource.Resource):

    def __init__(self):
        super().__init__()

    async def render_post(self, request):
        # Creating a dictionary from a message received from a sensor
        data = [MessageToDict(proto_device_info_pb2.ProtoDeviceInfo().FromString(request.payload))]
        # Create the file "Deviceinfo.txt" and save the date in this file
        if not os.path.isfile("Deviceinfo.txt"):
            file = open("Deviceinfo.txt", 'x')
        else:
            file = open("Deviceinfo.txt", 'w')
        file.write(str(data))
        file.close()
        # returning "ACK" to the sensor
        return aiocoap.Message(mtype=aiocoap.ACK, code=aiocoap.Code.CREATED,
                               token=request.token, payload="")


# Configuration - Class used to handle Configuration messages sent by the sensor
class Configuration(resource.Resource):

    def __init__(self):
        super().__init__()

    async def render_post(self, request):
        # Creating a dictionary from a message received from a sensor
        data = [MessageToDict(proto_config_pb2.ProtoConfig().FromString(request.payload))]
        # Create the file "Configuration.txt" and save the date in this file
        if not os.path.isfile("Configuration.txt"):
            file = open("Configuration.txt", 'x')
        else:
            file = open("Configuration.txt", 'w')
        file.write(str(data))
        file.close()
        # returning "ACK" to the sensor
        return aiocoap.Message(mtype=aiocoap.ACK, code=aiocoap.Code.CREATED,
                               token=request.token, payload="")


# Time - Class used to handle Time messages sent by the sensor
class Time(resource.Resource):

    def __init__(self):
        super().__init__()

    async def render_post(self, request):
        time_stamp = int(time.time())
        time_stamp_hex = hex(time_stamp)
        print(time_stamp_hex)

        # returning timestamp to the sensor
        return aiocoap.Message(mtype=aiocoap.ACK, code=aiocoap.Code.CREATED,
                               token=request.token, payload=bytearray.fromhex(time_stamp_hex[2:]))


def main():
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
    asyncio.Task(aiocoap.Context.create_server_context(root, ("192.168.120.132", 5681)))
    # Getting the current event loop and  running until stop() is called.
    asyncio.get_event_loop().run_forever()


if __name__ == '__main__':
    # Getting the current event loop and running until complete main()
    asyncio.get_event_loop().run_until_complete(main())
