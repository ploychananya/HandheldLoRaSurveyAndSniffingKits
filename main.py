import network
import machine
import utime, gc, _thread

import config_lora
import json
import gps
from sx127x import SX127x
from controller_esp32 import ESP32Controller
from microWebSrv import MicroWebSrv
from ssd1306_i2c import Display

ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid='CHANANYA-AP')
print('network config : ',ap.ifconfig())

display = Display()
controller = ESP32Controller()
lora = controller.add_transceiver(SX127x(name = 'LoRa'),
        pin_id_ss = ESP32Controller.PIN_ID_FOR_LORA_SS,
        pin_id_RxDone = ESP32Controller.PIN_ID_FOR_LORA_DIO0)

print("LoRa Receiver")

def _httpHandlerLoRaGet(httpClient, httpResponse):
    try:
        lora.receivedPacket()
        lora.blink_led()
        payload, rssi, snr, flag = lora.read_payload(),lora.packetRssi(),lora.packetSnr(),lora.getIrqFlags()
        # print("RSSI: {0} dBm , Payload: {1}, Snr: {2}, flag: {3}".format(rssi,payload,snr,flag))
        display.show_text("RSSI: {}".format(rssi), 20, 20)
        data = {"rssi": rssi,"payload": payload, "snr": snr, "flag": flag}
        # lora.beginPacket()
        lora.endPacket()
        # {"mac_address": payload.mac_Addr,"ip_address":payload.ip_Addr,"payload":payload.data,"rssi": rssi,"snr": snr, "flag": flag}
    except:
        data ={"status":"LoRa Invalid reading."}
    httpResponse.WriteResponseOk(
        headers=({'Access-Control-Allow-Origin':'*'}),
        contentType= 'application/json',
        contentCharset= 'UTF-8',
        content = json.dumps(data))


def _httpHandlerGPSGet(httpClient, httpResponse):
    try:
        data = gps.gps_working()
    except:
        data = {"status":"GPS Invalid reading."}
    httpResponse.WriteResponseOk(
        headers=({'Access-Control-Allow-Origin':'*'}),
        contentType= 'application/json',
        contentCharset= 'UTF-8',
        content = json.dumps(data))

def _httpHandlerSetParam(httpClient, httpResponse, routeArgs):
    print("data params : \t {0} \t{1}".format(routeArgs['type'],routeArgs['value']))
    data = {"type":routeArgs['type'],"value":routeArgs['value']}
    if(routeArgs['type']=="frequency"):
        SX127x.setFrequency(lora,int(routeArgs['value']))
    elif(routeArgs['type']=="spreading_factor"):
        SX127x.setSpreadingFactor(lora,int(routeArgs['value']))
    elif(routeArgs['type']=="bandwidth"):
        SX127x.setSignalBandwidth(lora,int(routeArgs['value']))
    elif(routeArgs['type']=="coding_rate"):
        SX127x.setCodingRate(lora,int(routeArgs['value']))
    else:
        pass   
    httpResponse.WriteResponseOk(
        headers=({'Access-Control-Allow-Origin':'*'}),
        contentType= 'application/json',
        contentCharset= 'UTF-8',
        content = json.dumps(data))


def _httpHandlerGetAllParams(httpClient, httpResponse):
    data = {"frequency":lora.fre_client,"sf":lora.sf_client,"bw":lora.bw_client,"coding rate":lora.c_rate_client}
    httpResponse.WriteResponseOk(
        headers=({'Access-Control-Allow-Origin':'*'}),
        contentType= 'application/json',
        contentCharset= 'UTF-8',
        content = json.dumps(data))

routeHandlers = [('/lora',"GET",_httpHandlerLoRaGet),('/gps',"GET",_httpHandlerGPSGet),('/set/<type>/<value>','GET',_httpHandlerSetParam),
('/params',"GET",_httpHandlerGetAllParams)]
srv = MicroWebSrv(routeHandlers=routeHandlers,webPath='/www/')
srv.WebSocketThreaded		= False
srv.Start()
