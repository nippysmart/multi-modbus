#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Multi ModBus 
#
# Author: leniwiec <https://www.leniwiec.org> 
#
# Read data from modbus rtu -> tcp gateway and represent it as Domoticz devices. 
# Requirements:
# 1. pip install pymodbus
# 2. pip install pyModbusTCP
# 3. pip install json
#
#
"""
<plugin key="NIPPYMultiModBus" name="NIPPY Multi ModBus resolver" author="leniwiec" version="1.0.0">
    <params>
        <param field="Address" label="IP Adress" width="350px" required="true"/>
        <param field="Port" label="Port" width="120px" required="true" default="502"/>
        <param field="Mode1" label="Config file" width="120px" required="true" default="/config/plugins/multi-modbus/devices.json"/>
        <param field="Mode2" label="Update interval (sec)" width="120px" required="true" default="30"/>
        <param field="Mode6" label="Debug" width="120px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal" default="true"/>
            </options>
        </param>
    </params>
</plugin>
"""


import Domoticz
from time import sleep
import os
import json

from pyModbusTCP.client import ModbusClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian


class BasePlugin:
    enabled = False
    def __init__(self):
        self.data = None
        return
                
    def onStart(self):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Log("onStart called")
            Domoticz.Log("IP: "+str(Parameters["Address"]))
            Domoticz.Log("PORT: "+str(Parameters["Port"]))
            Domoticz.Log("CONFIG: "+str(Parameters["Mode1"]))
            Domoticz.Log("INTERVAL: "+str(Parameters["Mode2"]))
            Domoticz.Log("DEBUG: "+str(Parameters["Mode6"]))

        with open(Parameters["Mode1"],'r') as f:
            self.data = json.load(f)

        # types of device can be found here: https://www.domoticz.com/wiki/Developing_a_Python_plugin#Available_Device_Types
        for i in self.data:
            for r in i['input_registers']:
                if (r['Unit'] not in Devices):
                    Domoticz.Device(Name=i['name']+' - '+r['description'], Unit=int(r['Unit']), Type=int(r['Type']), Subtype=int(r['SubType']), Options={"Custom": "0;"+r['unit']}, Used=int(r['Used'])).Create()

        Domoticz.Heartbeat(int(Parameters["Mode2"]))


    def onStop(self):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Log("onStop called")

    def onConnect(self, Connection, Status, Description):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Log("onConnect called")

    def onMessage(self, Connection, Data, Status, Extra):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Log("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Log("onHeartbeat called")
        
        modbus_client = ModbusClient(host=Parameters["Address"], port=int(Parameters["Port"]))

        for i in self.data:
            modbus_client.unit_id = i['slave']

            input_registers = {}

            for r in i['input_registers']:

                if isinstance(r['id'],str):
                    idR = int(r['id'], 16)
                else:
                    idR = int(r['id'])

                if r['type'] == "int8":
                    buff = modbus_client.read_input_registers(idR,1)
                    if buff is None:
                        TimeoutDevice(Unit=r['Unit'])
                        continue
                    [input_registers[idR]] = buff 
                    if 'translate' in r:
                        # 0 - gray, 1 - green, 2 - yellow, 3 - dark yellow, 4 - red
                        if 'colors' in r:
                            color = r['colors'][str(input_registers[idR])] 
                        else:
                            color = 0
                        UpdateDevice(r['Unit'], nValue=color, sValue=r['translate'][str(input_registers[idR])], AlwaysUpdate=False)
                    else:
                        UpdateDevice(r['Unit'], nValue=0, sValue='%.4f'%(input_registers[idR]/r['divider']), AlwaysUpdate=False)
                else:
                    buff = modbus_client.read_input_registers(idR,2) 
                    if buff is None:
                        TimeoutDevice(Unit=r['Unit'])
                        continue
                    [input_registers[idR],input_registers[idR+1]] = buff

                    x = [input_registers[idR],input_registers[idR+1]]
                    decoder = BinaryPayloadDecoder.fromRegisters(x, byteorder=Endian.Big, wordorder=Endian.Big)
                    if r['type'] == "int16":
                        value = round(decoder.decode_16bit_int(), 4)/r['divider']
                    elif r['type'] == "int32":
                        value = round(decoder.decode_32bit_int(), 4)/r['divider']
                    elif r['type'] == "float16":
                        value = round(decoder.decode_16bit_float(), 4)/r['divider']
                    elif r['type'] == "float32":
                        value = round(decoder.decode_32bit_float(), 4)/r['divider']

                    UpdateDevice(r['Unit'], nValue=0, sValue='%.4f'%(value), AlwaysUpdate=False)

                if Parameters["Mode6"] == "Debug":
                    Domoticz.Log(Devices[r['Unit']].Name+': '+Devices[r['Unit']].sValue)
 




global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data, Status, Extra):
    global _plugin
    _plugin.onMessage(Connection, Data, Status, Extra)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

def UpdateDevice(Unit, nValue, sValue, Image=-1, TimedOut=0, AlwaysUpdate=False):
    if Unit in Devices:
        if Devices[Unit].nValue != int(nValue) or Devices[Unit].sValue != str(sValue) or Devices[Unit].TimedOut != TimedOut or AlwaysUpdate:
            Devices[Unit].Update(int(nValue), str(sValue))
 
def TimeoutDevice(All=False, Unit=0):
    if All:
        for x in Devices:
            UpdateDevice(x, Devices[x].nValue, Devices[x].sValue, TimedOut=1)
    else:
        UpdateDevice(Unit, Devices[Unit].nValue, Devices[Unit].sValue, TimedOut=1)
