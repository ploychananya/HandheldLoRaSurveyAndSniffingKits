import network
import machine
# station = network.WLAN(network.STA_IF)
# station.active(True)
# station.connect("PL212", "0826147071")
# station.connect("KUWIN", "")
# while not station.isconnected():
#     machine.idle()
# station.ifconfig()
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid='PLOY-AP')
print('network config : ',ap.ifconfig())
import lora