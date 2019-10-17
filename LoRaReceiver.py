from microWebSrv import MicroWebSrv
from ssd1306_i2c import Display
import config_lora
from sx127x import SX127x
from controller_esp32 import ESP32Controller

print("LoRa Receiver")
display = Display()

def receive(lora):
    # while True:
    lora.receivedPacket()
    lora.blink_led()

            # try:
            #     payload = lora.read_payload()
            #     rssi = lora.packetRssi()
            #     display.show_text_wrap("{0} RSSI: {1}".format(payload.decode(), lora.packetRssi()))
            #     data = "RSSI: {0} , Payload: {1}\n".format(rssi,payload)
            #     print("*** Received message ***\n{}".format(payload.decode()))

            # except Exception as e:
            #     print(e)
            #     data = 'Invalid reading.'

            # display.show_text("RSSI: {}\n".format(lora.packetRssi()), 10, 10)
            # print("with RSSI: {}\n".format(lora.packetRssi()))
            # return data

            
        # else:
        #     data = 'Attempting to read sensor...'
        #     return data
            
            # httpResponse.WriteResponseOk(
            # headers=({'Cache-Control': 'no-cache'}),
            # contentType= 'text/event-stream',
            # coontentCharset= 'UTF-8',
            # content = 'data: {0}\n\n'.format(data) )

# routeHandlers = [('/lora',"GET",_httpHandlerLoRaGet)]
# srv = MicroWebSrv(routeHandlers=routeHandlers,webPath='/www/')
# srv.Start(threaded=False)
