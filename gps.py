import machine
import time

uart = machine.UART(1,rx=12, tx=15, baudrate=9600, bits=8)

def gps_working():
    gps_data = str(uart.read()) # read all available characters
    gps_array = gps_data.split(',')
    # print("Array[0]: {0} \n".format(gps_array[0]))
    # print("DAta: {0} \n".format(gps_data))

    # print("Array: {0} \n".format(gps_array))

    if(gps_array[0]=="b'$GPRMC"):
        if(gps_array[1]!= '' or gps_array[3]!= ''):
            data = {"status": "success","timestamp":gps_array[1],"latitude": gps_array[3],"longitude": gps_array[5]} 
        else:
            data = {"status": "Can not detect latitude and longitude."} 

    else:
        data = {"status": "GPS doesn't work."}
    # print("GPS: {0} \n".format(data))
    return data