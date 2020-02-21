import network
import machine
import utime, gc, _thread
import os

import json
import gps
import time
from sx127x import SX127x
from controller_esp32 import ESP32Controller
from microWebSrv import MicroWebSrv
from ssd1306_i2c import Display

# log = "timeStamp,gps_status,latitude,longitude,macAddr,data,rssi,snr\r\n"


ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid='CHANANYA-AP')
print('network config : ',ap.ifconfig())

try:
    display = Display()
except:
    pass
controller = ESP32Controller()
lora = controller.add_transceiver(SX127x(name = 'LoRa'),
        pin_id_ss = ESP32Controller.PIN_ID_FOR_LORA_SS,
        pin_id_RxDone = ESP32Controller.PIN_ID_FOR_LORA_DIO0)

print("LoRa Receiver")
#dont open web client
def LoRaInternal():
    while(True):
        files = os.listdir()
        if('machine.log' not in files):
            logM = open('machine.log', 'w')
            logM.write("timeStamp,data,rssi,snr,gps_status,latitude,longitude\n")
            print("CREAT LOG FILE")
        else:
            logM = open('machine.log', 'a')
            
        gps_data = gps.gps_working()
        lora.receivedPacket()
        lora.blink_led()
        payload, rssi, snr= lora.read_payload(),lora.packetRssi(),lora.packetSnr()
        # transform json to obj before convert to json again      
        print("MACHINE: {0}".format(payload))
        if(gps_data['status']=='success' and payload != None):
            logM.write("{0},{1},{2},{3},{4},{5},{6} \r\n".format(gps_data['timestamp'],payload,rssi,snr,gps_data['status'],gps_data['latitude'],gps_data['longitude']))
        elif(payload != None):
            logM.write("{0},{1},{2},{3},{4},{5},{6} \r\n".format("undefined",payload,rssi,snr,gps_data['status'],"undefined","undefined"))
        time.sleep(10.0)




def _httpHandlerLoRaGet(httpClient, httpResponse):
    try:    
        files = os.listdir()
        if('web.log' not in files):
            log = open('web.log', 'w')
            log.write("timeStamp,data,rssi,snr,gps_status,latitude,longitude\r\n")
            print("CREAT LOG FILE")
        else:
            log = open('web.log', 'a')

        gps_data = gps.gps_working()
        lora.receivedPacket()
        lora.blink_led()
        payload, rssi, snr, flag = lora.read_payload(),lora.packetRssi(),lora.packetSnr(),lora.getIrqFlags()
        # transform json to obj before convert to json again      
        print(("WEB_CLIENT: {0}").format(payload))
        if(payload != None and chr(payload[0])=='{'):
            payload = json.loads(payload)       

        if(gps_data['status']=='success' and payload != None):
            data = {"status":"success","rssi": rssi,"payload": payload, "snr": snr, "flag": flag,"timestamp":gps_data['timestamp'],"gps_status":gps_data['status'],"latitude":gps_data['latitude'],"longitude":gps_data['longitude']}
            # log.append(("{0},{1},{2},{3},{4},{5} \n").format(gps_data['timestamp'],payload,rssi,snr,gps_data['latitude'],gps_data['longitude']))
            log.write("{0},{1},{2},{3},{4},{5},{6} \r\n".format(gps_data['timestamp'],payload,rssi,snr,gps_data['status'],gps_data['latitude'],gps_data['longitude']))
        elif(payload != None):
            data = {"status":"success","rssi": rssi,"payload": payload, "snr": snr, "flag": flag,"timestamp":None,"gps_status":gps_data['status'],"latitude":None,"longitude":None}
            # log.append(("{0},{1},{2},{3},{4},{5} \n").format("undefined",payload,rssi,snr,"undefined","undefined"))
            log.write("{0},{1},{2},{3},{4},{5},{6} \r\n".format("undefined",payload,rssi,snr,gps_data['status'],"undefined","undefined"))
        
        try:
            display.show_text_wrap("f:{0} sf:{1} cr:{2} bw:{3}".format(lora.fre_client,lora.sf_client,lora.c_rate_client,lora.bw_client))
        except:
            pass
    except:
        data ={"status":"LoRa Invalid reading."}
    httpResponse.WriteResponseOk(
        headers=({'Access-Control-Allow-Origin':'*'}),
        contentType= 'application/json',
        contentCharset= 'UTF-8',
        content = json.dumps(data))


def _httpHandlerGPSGet(httpClient, httpResponse):
    httpResponse.WriteResponseOk(
        headers=({'Access-Control-Allow-Origin':'*'}),
        contentType= 'application/json',
        contentCharset= 'UTF-8',
        content = json.dumps(gps.gps_working()))

def _httpHandlerSetParam(httpClient, httpResponse, routeArgs):
    print("data params : \t {0} \t{1}".format(routeArgs['type'],routeArgs['value']))
    data = {"type":routeArgs['type'],"value":routeArgs['value']}
    if(routeArgs['type']=="frequency"):
        lora.setFrequency(int(routeArgs['value']))
        lora.init()
    elif(routeArgs['type']=="spreading_factor"):
        lora.setSpreadingFactor(int(routeArgs['value']))
        lora.init()
    elif(routeArgs['type']=="bandwidth"):
        lora.setSignalBandwidth(int(routeArgs['value']))
        lora.init()
    elif(routeArgs['type']=="coding_rate"):
        lora.setCodingRate(int(routeArgs['value']))
        lora.init()
    else:
        pass   
    httpResponse.WriteResponseOk(
        headers=({'Access-Control-Allow-Origin':'*'}),
        contentType= 'application/json',
        contentCharset= 'UTF-8',
        content = json.dumps(data))


def _httpHandlerGetAllParams(httpClient, httpResponse):
    data = {"frequency":lora.fre_client,"sf":lora.sf_client,"bw":lora.bw_client,"coding_rate":lora.c_rate_client}
    httpResponse.WriteResponseOk(
        headers=({'Access-Control-Allow-Origin':'*'}),
        contentType= 'application/json',
        contentCharset= 'UTF-8',
        content = json.dumps(data))


def _httpHandlerGetLogs(httpClient, httpResponse,routeArgs):
    if(routeArgs['type']=="machine"):
        e = open('machine.log','r')
        data = e.read()
    elif (routeArgs['type']=="web"):
        e = open('web.log','r')
        data = e.read()
    gc.collect()
    httpResponse.WriteResponseOk(
        headers=({'Access-Control-Allow-Origin':'*'}),
        contentType= 'application/json',
        contentCharset= 'UTF-8',
        content = data)


def _httpHandlerClearLogs(httpClient, httpResponse):
    os.remove('web.log')
    os.remove('machine.log')
    os.listdir()
    gc.collect()
    httpResponse.WriteResponseOk(
        headers=({'Access-Control-Allow-Origin':'*'}),
        contentType= 'application/json',
        contentCharset= 'UTF-8',
        content = json.dumps({"status":"success"}))

# def _httpHandlerGetLog(httpClient, httpResponse):
#     global log
#     # data = {"frequency":lora.fre_client,"sf":lora.sf_client,"bw":lora.bw_client,"coding_rate":lora.c_rate_client}
#     httpResponse.WriteResponseOk(
#         headers=({'Access-Control-Allow-Origin':'*'}),
#         contentType= "text/csv",
#         contentCharset= 'UTF-8',
#         content = log)
# def _httpHandlerClearLog(httpClient, httpResponse):
#     global log
#     log = "timeStamp,gps_status,latitude,longitude,macAddr,data,rssi,snr\r\n"
#     httpResponse.WriteResponseOk(
#         headers=({'Access-Control-Allow-Origin':'*'}),
#         contentType= 'application/json',
#         contentCharset= 'UTF-8',
#         content = json.dumps({"status":"success"}))
# ,('/log',"GET",_httpHandlerGetLog),('clearlog',"GET",_httpHandlerClearLog)
routeHandlers = [('/lora',"GET",_httpHandlerLoRaGet),('/gps',"GET",_httpHandlerGPSGet),('/set/<type>/<value>','GET',_httpHandlerSetParam),('/params',"GET",_httpHandlerGetAllParams),
('/log/<type>',"GET",_httpHandlerGetLogs),('/clear',"GET",_httpHandlerClearLogs)]
srv = MicroWebSrv(routeHandlers=routeHandlers,webPath='/www/')
srv.WebSocketThreaded		= False
_thread.start_new_thread(LoRaInternal,())
_thread.start_new_thread(srv.Start,())
# srv.Start()