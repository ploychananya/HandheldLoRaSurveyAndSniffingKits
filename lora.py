
# from ssd1306_i2c import Display
import config_lora
import json
import gps
from sx127x import SX127x
from controller_esp32 import ESP32Controller
from microWebSrv import MicroWebSrv
from ssd1306_i2c import Display

# import LoRaReceiver

#---------------gps
# import machine
# lineend='\r\n'
# uart = machine.UART(2, rx=15, tx=12, baudrate=9600, bits=8, parity=None, stop=1, timeout=1500, buffer_size=1024)
# uart = machine.UART(2, rx=15, tx=12, baudrate=9600, timeout=1500)
# gps = machine.GPS(uart)
# float_precision(6)
# gps.startservice()
# gps.getdata()

#---------------gps


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
        print("RSSI: {0} dBm , Payload: {1}, Snr: {2}, flag: {3}".format(rssi,payload,snr,flag))
        display.show_text("RSSI: {}".format(rssi), 20, 20)
        data = {"rssi": rssi,"payload": payload, "snr": snr, "flag": flag,"text":"fuck"}
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

def _httpHandlerSetParam(httpClient, httpResponse):
    data  = httpClient.ReadRequestContentAsJSON()
    print("data params : \t {0}".format(data))
    httpResponse.WriteResponseOk(
        headers=({'Access-Control-Allow-Origin':'*'}),
        contentType= 'application/json',
        contentCharset= 'UTF-8',
        content = data)

routeHandlers = [('/lora',"GET",_httpHandlerLoRaGet),('/gps',"GET",_httpHandlerGPSGet),('/s','POST',_httpHandlerSetParam)]
srv = MicroWebSrv(routeHandlers=routeHandlers,webPath='/www/')
srv.WebSocketThreaded		= False
srv.Start()