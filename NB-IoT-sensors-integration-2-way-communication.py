import base64
import datetime
import asyncio
import os.path

import aiocoap.resource as resource
import aiocoap
from protobuf import proto_measurements_pb2
from protobuf import proto_device_info_pb2
from protobuf import proto_config_pb2
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


class Measurements(resource.Resource):

    def __init__(self):
        super().__init__()

    async def render_post(self, request):

        # Creating a dictionary from a received message.
        data = [MessageToDict(proto_measurements_pb2.ProtoMeasurements().FromString(request.payload))]
        record = []
        # Set request_device_info to true
        device_config = proto_config_pb2.ProtoConfig()
        device_config.request_device_info = True
        # Serializing device config.
        response_payload = device_config.SerializeToString()

        # iteration in list data
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
        # returning "ACK" and response payload to the sensor
        return aiocoap.Message(mtype=aiocoap.ACK, code=aiocoap.Code.CREATED,
                               token=request.token, payload=response_payload)


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


def main():
    # Resource tree creation
    root = resource.Site()
    # Set up "m" endpoint, which will be receiving the data sent by Efento NB-IoT sensor using POST method.
    root.add_resource(["m"], Measurements())
    # Set up "i" endpoint, which will be receiving the data sent by Efento NB-IoT sensor using POST method.
    root.add_resource(["i"], DeviceInfo())
    # Starting the application on set IP address and port.
    asyncio.Task(aiocoap.Context.create_server_context(root, ("192.168.120.132", 5683)))
    # Getting the current event loop and  running until stop() is called.
    asyncio.get_event_loop().run_forever()


if __name__ == '__main__':
    # Getting the current event loop and running until complete main()
    asyncio.get_event_loop().run_until_complete(main())
