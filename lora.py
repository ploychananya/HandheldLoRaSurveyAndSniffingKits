
from ssd1306_i2c import Display
import config_lora
from sx127x import SX127x
from controller_esp32 import ESP32Controller
from microWebSrv import MicroWebSrv
# import LoRaReceiver

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
        payload, rssi = lora.read_payload(),lora.packetRssi()
        # display.show_text_wrap("{0} RSSI: {1}".format(payload.decode(), lora.packetRssi()))
        display.show_text("RSSI: {}\n".format(lora.packetRssi()), 10, 10)
        data = "RSSI: {0} dBm , Payload: {1} <br>".format(rssi,payload)
        print("RSSI: {0} , Payload: {1}\n".format(rssi,payload))

    except:
        data = 'Invalid reading.<br>'

    httpResponse.WriteResponseOk(
        headers=({'Cache-Control': 'no-cache'}),
        contentType= 'text/event-stream',
        contentCharset= 'UTF-8',
        content = 'data: {0}\n\n'.format(data) )

routeHandlers = [('/lora',"GET",_httpHandlerLoRaGet)]
srv = MicroWebSrv(routeHandlers=routeHandlers,webPath='/www/')
srv.WebSocketThreaded		= False
srv.Start()