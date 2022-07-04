""" Defines the BOARD class that contains the board pin mappings and RF module HF/LF info. """
# -*- coding: utf-8 -*-

# Copyright 2015-2018 Mayer Analytics Ltd.
#
# This file is part of pySX127x.
#
# pySX127x is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# pySX127x is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more
# details.
#
# You can be released from the requirements of the license by obtaining a commercial license. Such a license is
# mandatory as soon as you develop commercial activities involving pySX127x without disclosing the source code of your
# own applications, or shipping pySX127x with a closed source product.
#
# You should have received a copy of the GNU General Public License along with pySX127.  If not, see
# <http://www.gnu.org/licenses/>.


import gpiod
import spidev

import time


class BOARD:
    """ Board initialisation/teardown and pin configuration is kept here.
        Also, information about the RF module is kept here.
        This is the Raspberry Pi board with one LED and a modtronix inAir9B.
    """
    # Note that the BCOM numbering for the gpiods is used.
    # DIO0 = 22   # RaspPi gpiod 22
    DIO0_CHIP = "gpiodchip6"
    DIO0_LINE_OFFSET = int(15)

    # DIO1 = 23   # RaspPi gpiod 23
    DIO1_CHIP = "gpiodchip5"
    DIO1_LINE_OFFSET = int(1)
    # DIO2 = 24   # RaspPi gpiod 24
    DIO2_CHIP = "gpiodchip5"
    DIO2_LINE_OFFSET = int(0)
    # DIO3 = 25   # RaspPi gpiod 25
    DIO3_CHIP = "gpiodchip5"
    DIO3_LINE_OFFSET = int(0)
    #LED  = 18   # RaspPi gpiod 18 connects to the LED on the proto shield
    LED_CHIP = "gpiodchip5"
    LED_LINE_OFFSET = int(4)
    led = None
    # SWITCH = 4  # RaspPi gpiod 4 connects to a switch
    SWITCH_CHIP = "gpiodchip0"
    SWITCH_LINE_OFFSET = int(8)
    # The spi object is kept here
    spi = None
    
    # tell pySX127x here whether the attached RF module uses low-band (RF*_LF pins) or high-band (RF*_HF pins).
    # low band (called band 1&2) are 137-175 and 410-525
    # high band (called band 3) is 862-1020
    low_band = True

    @staticmethod
    def setup():
        """ Configure the Raspberry gpiods
        :rtype : None
        """
        gpiod.setmode(gpiod.BCM)
        # LED
        # gpiod.setup(BOARD.LED, gpiod.OUT)
        # gpiod.output(BOARD.LED, 0)
        led_chip = gpiod.chip(BOARD.LED_CHIP)
        BOARD.led = led_chip.get_line(BOARD.LED_LINE_OFFSET)
        led_config = gpiod.line_request()
        led_config.consumer = "Set-Up"
        led_config.request_type = gpiod.line_request.DIRECTION_OUTPUT   
        BOARD.led.request(led_config)
        # switch
        switch_chip = gpiod.chip(BOARD.SWITCH_CHIP)
        switch = switch_chip.get_line(BOARD.SWITCH_LINE_OFFSET)
        switch_config = gpiod.line_request()
        switch_config.consumer = "Set-UP"
        switch_config.flags = gpiod.line_request.FLAG_BIAS_PULL_DOWN
        switch_config.request_type =  gpiod.line_request.DIRECTION_INPUT
        switch.request(switch_config)

        # gpiod.setup(BOARD.SWITCH, gpiod.IN, pull_up_down=gpiod.PUD_DOWN) 
        # DIOx
        DIO_DICT = {BOARD.DIO0_CHIP : BOARD.DIO0_LINE_OFFSET, 
                    BOARD.DIO1_CHIP : BOARD.DIO1_LINE_OFFSET, 
                    BOARD.DIO2_CHIP : BOARD.DIO2_LINE_OFFSET, 
                    BOARD.DIO3_CHIP : BOARD.DIO3_LINE_OFFSET}
        for chip,offset in DIO_DICT.items():
            dio_chip = gpiod.chip(chip)
            dio = dio_chip.get_line(offset)
            dio_config = gpiod.line_request()
            dio_config.flags = gpiod.line_request.FLAG_BIAS_PULL_DOWN
            dio_config.request_type = gpiod.line_request.DIRECTION_INPUT
            dio.request(dio_config)
            # gpiod.setup(gpiod_pin, gpiod.IN, pull_up_down=gpiod.PUD_DOWN)
        # blink 2 times to signal the board is set up
        BOARD.blink(.1, 2)

    @staticmethod
    def teardown():
        """ Cleanup gpiod and SpiDev """
        # gpiod.cleanup()
        BOARD.spi.close()

    @staticmethod
    def SpiDev(spi_bus=0, spi_cs=0):
        """ Init and return the SpiDev object
        :return: SpiDev object
        :param spi_bus: The RPi SPI bus to use: 0 or 1
        :param spi_cs: The RPi SPI chip select to use: 0 or 1
        :rtype: SpiDev
        """
        BOARD.spi = spidev.SpiDev()
        BOARD.spi.open(spi_bus, spi_cs)
        BOARD.spi.max_speed_hz = 5000000    # SX127x can go up to 10MHz, pick half that to be safe
        return BOARD.spi

    @staticmethod
    def add_event_detect(dio_number, callback):
        """ Wraps around the gpiod.add_event_detect function
        :param dio_number: DIO pin 0...5
        :param callback: The function to call when the DIO triggers an IRQ.
        :return: None
        """
        # gpiod.add_event_detect(dio_number, gpiod.RISING, callback=callback)

    @staticmethod
    def add_events(cb_dio0, cb_dio1, cb_dio2, cb_dio3, cb_dio4, cb_dio5, switch_cb=None):
        '''BOARD.add_event_detect(BOARD.DIO0, callback=cb_dio0)
        BOARD.add_event_detect(BOARD.DIO1, callback=cb_dio1)
        BOARD.add_event_detect(BOARD.DIO2, callback=cb_dio2)
        BOARD.add_event_detect(BOARD.DIO3, callback=cb_dio3)
        # the modtronix inAir9B does not expose DIO4 and DIO5
        if switch_cb is not None:
            gpiod.add_event_detect(BOARD.SWITCH, gpiod.RISING, callback=switch_cb, bouncetime=300)'''

    @staticmethod
    def led_on():
        """ Switch the proto shields LED
        :param value: 0/1 for off/on. Default is 1.
        :return: value
        :rtype : int
        """
        BOARD.led.set_value(0)
        
        return 0

    @staticmethod
    def led_off():
        """ Switch LED off
        :return: 0
        """
        BOARD.led.set_value(1)
       
        return 0

    @staticmethod
    def blink(time_sec, n_blink):
        if n_blink == 0:
            return
        BOARD.led_on()
        for i in range(n_blink):
            time.sleep(time_sec)
            BOARD.led_off()
            time.sleep(time_sec)
            BOARD.led_on()
        BOARD.led_off()