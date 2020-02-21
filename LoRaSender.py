from time import sleep
import machine
import json
import config_lora
import ubinascii
# from ssd1306_i2c import Display

# from ssd1306_i2c import Display

def send(lora):
    counter = 0
    print("LoRa Sender")

    # display = Display()

    while True:
        # display.show_text("fre: {0} sf: {1}"+ 
                        # "bw: {2} cr: {3}".format(lora.fre_client,lora.sf_client,lora.bw_client,lora.c_rate_client), 10,10 )
        payload = 'Hello Im ttgo Esp32  ({0})'.format(counter)
        # data="{macAddr:"+ubinascii.hexlify(machine.unique_id()).decode()+",data:"payload+"}"
        data={"macAddr":ubinascii.hexlify(machine.unique_id()).decode(),"data":payload}

        print("Sending packet: \n{}\n".format(data))
        # display.show_text_wrap("{0} RSSI: {1}".format(payload, lora.packetRssi()))
        lora.println(json.dumps(data))

        counter += 1
        sleep(3)
