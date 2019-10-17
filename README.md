# Install new firmware
~/.local/bin/esptool.py  --port /dev/ttyUSB0 erase_flash
~/.local/bin/esptool.py --port /dev/ttyUSB0 write_flash 0x1000 <path to firmware file>

./BUILD.sh erase fixed it.

# Access flash 
sudo rshell -p /dev/ttyUSB0
rshell --buffer-size=30 -p /dev/ttyUSB0 -a -e nano

# copy code to Flash
cp main.py /pyboard/flash/

# into Micropython
repl  





