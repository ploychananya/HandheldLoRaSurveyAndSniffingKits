import machine
import time
uart = machine.UART(1,rx=12, tx=15,baudrate=9600, bits=8)


def gprmcConverter(value):
    val_dd =  math.floor(value/100)
    val_ss = value - (val_dd *100)
    new_val = val_dd + (val_ss/60)
    return new_val


def gps_working():
    gps_data = str(uart.read()) # read all available characters
    gps_array = gps_data.split(',')
    # print("Array[0]: {0} \n".format(gps_array[0]))
    # print("DAta: {0} \n".format(gps_data))
    # print("Array: {0} \n".format(gps_array))
    if(gps_array[0]=="b'$GPRMC"):
        if(gps_array[5]!= "" or gps_array[3]!= ""):
            lat = gprmcConverter(float(gps_array[3]))
            long = gprmcConverter(float(gps_array[5]))
            data = {"status": "success","timestamp":gps_array[1],"latitude": lat,"longitude": long} 
        else:
            data = {"status": "Can not detect latitude and longitude."} 
    else:
        data = {"status": "GPS doesn't work."}
    return data