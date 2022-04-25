import logging
import time
import numpy as np
import jpype as jp
from pydm.data_plugins.plugin import PyDMPlugin, PyDMConnection
from qtpy.QtCore import QTimer
import random

#
# Plugin for acnet protocol using the JPype wrapping of the Java DIODmq API
# This requires a Java 8 JRE installation in the PATH, JPype in the python
# environment, and access to the usgov.jar and rabbitmq-client.jar
#
class Connection(PyDMConnection):

    def __init__(self, channel, address, protocol=None, parent=None):
        super(Connection, self).__init__(channel, address, protocol, parent)
        print("acnet_plugin")
        print("channel:", channel)
        print("address:", address)
        self.add_listener(channel)
        self.value = address
        self.unit = None

        if (not jp.isJVMStarted()):
            jp.startJVM(classpath=['./usgov.jar', './rabbitmq-client.jar'])
        self.cls = jp.JClass("gov.fnal.controls.tools.dio.DIODMQ")
        self.package = jp.JPackage("gov.fnal.controls.tools.dio")
        self.typeerr = jp.JClass("gov.fnal.controls.tools.timed.TimedError")
        self.typedouble = jp.JClass("gov.fnal.controls.tools.timed.TimedDouble")
        self.typedoublearray = jp.JClass("gov.fnal.controls.tools.timed.TimedDoubleArray")

        proxy1 = jp.JProxy(self.package.JpypeMonitorCallback,inst=self)
        self.sub1 = self.package.JpypeMonitor(proxy1, address)
        self.connected = True

    def send_new_value(self):
        val_to_send = "{0}-{1}".format(self.value, random.randint(0, 9))
        self.new_value_signal[str].emit(str(val_to_send))

    def send_connection_state(self, conn):
        self.connection_state_signal.emit(conn)

    def add_listener(self, channel):
        super(Connection, self).add_listener(channel)
        self.send_connection_state(True)

    def dataChanged (self, dataRequest, data) :
        self.value = data
        if isinstance(data, self.typeerr) :
            print ("callback error: ", dataRequest, data.getMessage())
        elif isinstance(data, self.typedouble) :
            self.new_value_signal[float].emit(float(data.doubleValue()))
        elif isinstance(data, self.typedoublearray) :
            print ("callback: ", dataRequest, data.getArraySize(), data.doubleArray())
        else :
            print (type(data))
            print (data)

    def close(self):
        self.sub1.dispose()



class AcnetPlugin(PyDMPlugin):
    protocol = "acnet"
    connection_class = Connection

