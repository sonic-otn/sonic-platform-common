import time
import importlib
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.Thrift import TException

THRIFT_SERVER = 'localhost'
THRIFT_SERVER_PORT = 9092

class ThriftClient(object):
    def open(self):
        self.transport = TSocket.TSocket(THRIFT_SERVER, THRIFT_SERVER_PORT)

        self.transport = TTransport.TBufferedTransport(self.transport)
        bprotocol = TBinaryProtocol.TBinaryProtocol(self.transport)

        pltfm_mgr_client_module = importlib.import_module("otn_pmon.device.periph_rpc")
        self.pltfm_mgr = pltfm_mgr_client_module.Client(bprotocol)

        self.transport.open()
        return self
    def close(self):
        self.transport.close()
    def __enter__(self):
        return self.open()
    def __exit__(self, exc_type, exc_value, tb):
        self.close()

def thrift_try(func, attempts=35):
    for attempt in range(attempts):
        try:
            with ThriftClient() as client:
               return func(client.pltfm_mgr)
        except TException as e:
            if attempt + 1 == attempts:
               raise e
        time.sleep(1)
