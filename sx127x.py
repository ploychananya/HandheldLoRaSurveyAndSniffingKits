from time import sleep
import gc
import binascii

# binary = ""

PA_OUTPUT_RFO_PIN = 0
PA_OUTPUT_PA_BOOST_PIN = 1

# registers
REG_FIFO = 0x00
REG_OP_MODE = 0x01
REG_FRF_MSB = 0x06
REG_FRF_MID = 0x07
REG_FRF_LSB = 0x08
REG_PA_CONFIG = 0x09
REG_LNA = 0x0c
REG_FIFO_ADDR_PTR = 0x0d

REG_FIFO_TX_BASE_ADDR = 0x0e
FifoTxBaseAddr = 0x00
# FifoTxBaseAddr = 0x80

REG_FIFO_RX_BASE_ADDR = 0x0f
FifoRxBaseAddr = 0x00
REG_FIFO_RX_CURRENT_ADDR = 0x10
REG_IRQ_FLAGS_MASK = 0x11
REG_IRQ_FLAGS = 0x12
REG_RX_NB_BYTES = 0x13
REG_PKT_RSSI_VALUE = 0x1a
REG_PKT_SNR_VALUE = 0x1b
REG_MODEM_CONFIG_1 = 0x1d
REG_MODEM_CONFIG_2 = 0x1e
REG_PREAMBLE_MSB = 0x20
REG_PREAMBLE_LSB = 0x21
REG_PAYLOAD_LENGTH = 0x22
REG_FIFO_RX_BYTE_ADDR = 0x25
REG_MODEM_CONFIG_3 = 0x26
REG_RSSI_WIDEBAND = 0x2c
REG_DETECTION_OPTIMIZE = 0x31
REG_DETECTION_THRESHOLD = 0x37
REG_SYNC_WORD = 0x39
REG_DIO_MAPPING_1 = 0x40
REG_VERSION = 0x42

# modes
MODE_LONG_RANGE_MODE = 0x80  # bit 7: 1 => LoRa mode
MODE_SLEEP = 0x00
MODE_STDBY = 0x01
MODE_TX = 0x03
MODE_RX_CONTINUOUS = 0x05
MODE_RX_SINGLE = 0x06

# PA config
PA_BOOST = 0x80

# IRQ masks
IRQ_TX_DONE_MASK = 0x08
IRQ_PAYLOAD_CRC_ERROR_MASK = 0x20
IRQ_RX_DONE_MASK = 0x40
IRQ_RX_TIME_OUT_MASK = 0x80

# Buffer size
MAX_PKT_LENGTH = 255
# 255
ff=434
_bw=125E3
_sf=12
_cr=5


class SX127x:
    # sending to update at web client

    def __init__(self,
                 name = 'SX127x',
                 parameters = {'frequency': ff, 'tx_power_level': 2, 'signal_bandwidth': _bw,
                               'spreading_factor': _sf, 'coding_rate': _cr, 'preamble_length': 8,
                               'implicitHeader': False, 'sync_word': 0x12, 'enable_CRC': True},
                 onReceive = True):
        # sending to update at web client
        self.fre_client = 434
        self.sf_client = 12
        self.bw_client= 125E3
        self.c_rate_client = 5
        ####################################
        self.name = name
        self.parameters = parameters
        self._onReceive = onReceive
        self._lock = False


    def init(self, parameters = None):
        if parameters: self.parameters = parameters
        init_try = True
        re_try = 0
        # check version
        while(init_try and re_try < 5):
            version = self.readRegister(REG_VERSION)
            re_try = re_try + 1
            if(version != 0):
                init_try = False;
        # if version != 0x12:
        #     raise Exception('Invalid version.')

        # put in LoRa and sleep mode
        self.sleep()

        # config
        self.setFrequency(self.parameters['frequency'])
        print("init frequency =  %d " %(self.parameters['frequency']))
        self.setSignalBandwidth(self.parameters['signal_bandwidth'])

        # set LNA boost
        self.writeRegister(REG_LNA, self.readRegister(REG_LNA) | 0x03)

        # set auto AGC
        self.writeRegister(REG_MODEM_CONFIG_3, 0x04)

        self.setTxPower(self.parameters['tx_power_level'])
        self._implicitHeaderMode = None
        self.implicitHeaderMode(self.parameters['implicitHeader'])
        self.setSpreadingFactor(self.parameters['spreading_factor'])
        self.setCodingRate(self.parameters['coding_rate'])
        self.setPreambleLength(self.parameters['preamble_length'])
        self.setSyncWord(self.parameters['sync_word'])
        self.enableCRC(self.parameters['enable_CRC'])

        # set LowDataRateOptimize flag if symbol time > 16ms (default disable on reset)
        # self.writeRegister(REG_MODEM_CONFIG_3, self.readRegister(REG_MODEM_CONFIG_3) & 0xF7)  # default disable on reset
        if 1000 / (self.parameters['signal_bandwidth'] / 2**self.parameters['spreading_factor']) > 16:
            self.writeRegister(REG_MODEM_CONFIG_3, self.readRegister(REG_MODEM_CONFIG_3) | 0x08)

        # set base addresses
        self.writeRegister(REG_FIFO_TX_BASE_ADDR, FifoTxBaseAddr)
        self.writeRegister(REG_FIFO_RX_BASE_ADDR, FifoRxBaseAddr)

        self.standby()


    def beginPacket(self, implicitHeaderMode = False):
        self.standby()
        self.implicitHeaderMode(implicitHeaderMode)

        # reset FIFO address and paload length
        self.writeRegister(REG_FIFO_ADDR_PTR, FifoTxBaseAddr)
        self.writeRegister(REG_PAYLOAD_LENGTH, 0)


    def endPacket(self):
        # put in TX mode
        self.writeRegister(REG_OP_MODE, MODE_LONG_RANGE_MODE | MODE_TX)

        # wait for TX done, standby automatically on TX_DONE

        while (self.readRegister(REG_IRQ_FLAGS) & IRQ_TX_DONE_MASK) == 0:
            pass

        # clear IRQ's
        self.writeRegister(REG_IRQ_FLAGS, IRQ_TX_DONE_MASK)

        self.collect_garbage()


    def write(self, buffer):
        currentLength = self.readRegister(REG_PAYLOAD_LENGTH)
        size = len(buffer)

        # check size
        size = min(size, (MAX_PKT_LENGTH - FifoTxBaseAddr - currentLength))

        # write data
        for i in range(size):
            self.writeRegister(REG_FIFO, buffer[i])

        # update length
        self.writeRegister(REG_PAYLOAD_LENGTH, currentLength + size)
        return size


    def aquire_lock(self, lock = False):
        self._lock = False


    def println(self, string, implicitHeader = False):
        self.aquire_lock(True)  # wait until RX_Done, lock and begin writing.

        self.beginPacket(implicitHeader)
        self.write(string.encode())
        self.endPacket()

        self.aquire_lock(False) # unlock when done writing


    def getIrqFlags(self):
        irqFlags = self.readRegister(REG_IRQ_FLAGS)
        self.writeRegister(REG_IRQ_FLAGS, irqFlags)
        return irqFlags


    def packetRssi(self):
        return (self.readRegister(REG_PKT_RSSI_VALUE) - (164 if self._frequency < 868E6 else 157))


    def packetSnr(self):
        return (self.readRegister(REG_PKT_SNR_VALUE)) * 0.25


    def standby(self):
        self.writeRegister(REG_OP_MODE, MODE_LONG_RANGE_MODE | MODE_STDBY)


    def sleep(self):
        self.writeRegister(REG_OP_MODE, MODE_LONG_RANGE_MODE | MODE_SLEEP)


    def setTxPower(self, level, outputPin = PA_OUTPUT_PA_BOOST_PIN):
        if (outputPin == PA_OUTPUT_RFO_PIN):
            # RFO
            level = min(max(level, 0), 14)
            self.writeRegister(REG_PA_CONFIG, 0x70 | level)

        else:
            # PA BOOST
            level = min(max(level, 2), 17)
            self.writeRegister(REG_PA_CONFIG, PA_BOOST | (level - 2))


    def setFrequency(self, frequency):
        global ff
        ff = frequency
        self.parameters['frequency'] = frequency
        self.fre_client = frequency
        self._frequency = frequency
        
        # print("set frequency in def =  %d " %(self._frequency))

        frfs = {169: (42, 64, 0),
                433: (108, 64, 0),
                434: (108, 128, 0),
                866: (216, 128, 0),
                868: (217, 0, 0),
                915: (228, 192, 0)}

        self.writeRegister(REG_FRF_MSB, frfs[frequency][0])
        self.writeRegister(REG_FRF_MID, frfs[frequency][1])
        self.writeRegister(REG_FRF_LSB, frfs[frequency][2])
        # self.init()


    def setSpreadingFactor(self, sf):
        self.sf_client = sf
        self.parameters['spreading_factor'] = sf
        global _sf
        _sf = sf
        sf = min(max(sf, 6), 12)
        print("set Spreading Factor  in def=  %d " %(sf))
        self.writeRegister(REG_DETECTION_OPTIMIZE, 0xc5 if sf == 6 else 0xc3)
        self.writeRegister(REG_DETECTION_THRESHOLD, 0x0c if sf == 6 else 0x0a)
        self.writeRegister(REG_MODEM_CONFIG_2, (self.readRegister(REG_MODEM_CONFIG_2) & 0x0f) | ((sf << 4) & 0xf0))
        # self.init()


    def setSignalBandwidth(self, sbw):
        self.bw_client = sbw
        self.parameters['signal_bandwidth'] = sbw
        global _bw 
        _bw = sbw
        bins = (7.8E3, 10.4E3, 15.6E3, 20.8E3, 31.25E3, 41.7E3, 62.5E3, 125E3, 250E3)
        print("set Bandwidth in def =  %d " %(sbw))

        bw = bins.index(sbw)
        for i in range(len(bins)):
            if sbw <= bins[i]:
                bw = i
                break
        # bw = bins.index(sbw)
        self.writeRegister(REG_MODEM_CONFIG_1, (self.readRegister(REG_MODEM_CONFIG_1) & 0x0f) | (bw << 4))
        # self.init()


    def setCodingRate(self, denominator):
        self.c_rate_client = denominator
        self.parameters['coding_rate']= denominator
        global _cr 
        _cr = denominator
        print("set Coding Rate in def=  %d " %(denominator))
        denominator = min(max(denominator, 5), 8)
        cr = denominator - 4
        self.writeRegister(REG_MODEM_CONFIG_1, (self.readRegister(REG_MODEM_CONFIG_1) & 0xf1) | (cr << 1))
        # self.init()


    def setPreambleLength(self, length):
        self.writeRegister(REG_PREAMBLE_MSB,  (length >> 8) & 0xff)
        self.writeRegister(REG_PREAMBLE_LSB,  (length >> 0) & 0xff)


    def enableCRC(self, enable_CRC = False):
        modem_config_2 = self.readRegister(REG_MODEM_CONFIG_2)
        config = modem_config_2 | 0x04 if enable_CRC else modem_config_2 & 0xfb
        self.writeRegister(REG_MODEM_CONFIG_2, config)


    def setSyncWord(self, sw):
        self.writeRegister(REG_SYNC_WORD, sw)


    # def enable_Rx_Done_IRQ(self, enable = True):
        # if enable:
            # self.writeRegister(REG_IRQ_FLAGS_MASK, self.readRegister(REG_IRQ_FLAGS_MASK) & ~IRQ_RX_DONE_MASK)
        # else:
            # self.writeRegister(REG_IRQ_FLAGS_MASK, self.readRegister(REG_IRQ_FLAGS_MASK) | IRQ_RX_DONE_MASK)


    # def dumpRegisters(self):
        # for i in range(128):
            # print("0x{0:02x}: {1:02x}".format(i, self.readRegister(i)))


    def implicitHeaderMode(self, implicitHeaderMode = False):
        if self._implicitHeaderMode != implicitHeaderMode:  # set value only if different.
            self._implicitHeaderMode = implicitHeaderMode
            modem_config_1 = self.readRegister(REG_MODEM_CONFIG_1)
            config = modem_config_1 | 0x01 if implicitHeaderMode else modem_config_1 & 0xfe
            self.writeRegister(REG_MODEM_CONFIG_1, config)


    def onReceive(self, callback):
        self._onReceive = callback

        if self.pin_RxDone:
            if callback:
                self.writeRegister(REG_DIO_MAPPING_1, 0x00)
                self.pin_RxDone.set_handler_for_irq_on_rising_edge(handler = self.handleOnReceive)
            else:
                self.pin_RxDone.detach_irq()


    def receive(self, size = 0):
        self.implicitHeaderMode(size > 0)
        if size > 0: self.writeRegister(REG_PAYLOAD_LENGTH, size & 0xff)

        # The last packet always starts at FIFO_RX_CURRENT_ADDR
        # no need to reset FIFO_ADDR_PTR
        self.writeRegister(REG_OP_MODE, MODE_LONG_RANGE_MODE | MODE_RX_CONTINUOUS)


    def handleOnReceive(self, event_source):
        # self.aquire_lock(True)              # lock until TX_Done
        irqFlags = self.getIrqFlags()

        if (irqFlags == IRQ_RX_DONE_MASK):  # RX_DONE only, irqFlags should be 0x40
            # automatically standby when RX_DONE
            if self._onReceive:
                payload = self.read_payload()
                self._onReceive(self, payload)

        elif self.readRegister(REG_OP_MODE) != (MODE_LONG_RANGE_MODE | MODE_RX_SINGLE):
            # no packet received.
            # reset FIFO address / # enter single RX mode
            self.writeRegister(REG_FIFO_ADDR_PTR, FifoRxBaseAddr)
            self.writeRegister(REG_OP_MODE, MODE_LONG_RANGE_MODE | MODE_RX_SINGLE)

        # self.aquire_lock(False)             # unlock in any case.
        self.collect_garbage()
        return True

#        self.aquire_lock(True)              # lock until TX_Done
#
#        irqFlags = self.readRegister(REG_IRQ_FLAGS) # should be 0x50
#        self.writeRegister(REG_IRQ_FLAGS, irqFlags)
#
#        if (irqFlags & IRQ_RX_DONE_MASK) == 0: # check `RxDone`
#            self.aquire_lock(False)
#            return # `RxDone` is not set
#
#        # check `PayloadCrcError` bit
#        crcOk = not bool (irqFlags & IRQ_PAYLOAD_CRC_ERROR_MASK)
#
#        # set FIFO address to current RX address
#        self.writeRegister(REG_FIFO_ADDR_PTR, self.readRegister(REG_FIFO_RX_CURRENT_ADDR))
#
#        if self._onReceive:
#            payload = self.read_payload()
#            print(payload)
#            self.aquire_lock(False)     # unlock when done reading
#
#            self._onReceive(self, payload)
#
#        self.aquire_lock(False)             # unlock in any case.


    def receivedPacket(self, size = 0):
        irqFlags = self.getIrqFlags()

        self.implicitHeaderMode(size > 0)
        if size > 0: self.writeRegister(REG_PAYLOAD_LENGTH, size & 0xff)

        if (irqFlags == IRQ_RX_DONE_MASK):  # RX_DONE only, irqFlags should be 0x40
            # automatically standby when RX_DONE
            return True

        elif self.readRegister(REG_OP_MODE) != (MODE_LONG_RANGE_MODE | MODE_RX_SINGLE):
            # no packet received.
            # reset FIFO address / # enter single RX mode
            self.writeRegister(REG_FIFO_ADDR_PTR, FifoRxBaseAddr)
            self.writeRegister(REG_OP_MODE, MODE_LONG_RANGE_MODE | MODE_RX_SINGLE)


    def read_payload(self):
        # set FIFO address to current RX address
        # fifo_rx_current_addr = self.readRegister(REG_FIFO_RX_CURRENT_ADDR)
        self.writeRegister(REG_FIFO_ADDR_PTR, self.readRegister(REG_FIFO_RX_CURRENT_ADDR))

        # read packet length
        packetLength = self.readRegister(REG_PAYLOAD_LENGTH) if self._implicitHeaderMode else \
                       self.readRegister(REG_RX_NB_BYTES)
        
        # self.collect_garbage()
        payload = bytearray()
        for i in range(packetLength):
            payload.append(self.readRegister(REG_FIFO))

        self.collect_garbage()
        return bytes(payload)


    def readRegister(self, address, byteorder = 'big', signed = False):
        response = self.transfer(self.pin_ss, address & 0x7f)
        # print("{0} ".format(response),end='')
        # print("{0} ".format(binascii.hexlify(response)),end='')
        return int.from_bytes(response, byteorder)


    def writeRegister(self, address, value):
        self.transfer(self.pin_ss, address | 0x80, value)


    def collect_garbage(self):
        gc.collect()
        #print('[Memory - free: {}   allocated: {}]'.format(gc.mem_free(), gc.mem_alloc()))
