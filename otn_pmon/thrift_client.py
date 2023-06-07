##
#   Copyright (c) 2021 Alibaba Group and Accelink Technologies
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#   THIS CODE IS PROVIDED ON AN *AS IS* BASIS, WITHOUT WARRANTIES OR
#   CONDITIONS OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT
#   LIMITATION ANY IMPLIED WARRANTIES OR CONDITIONS OF TITLE, FITNESS
#   FOR A PARTICULAR PURPOSE, MERCHANTABILITY OR NON-INFRINGEMENT.
#
#   See the Apache Version 2.0 License for specific language governing
#   permissions and limitations under the License.
##

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
        socket = TSocket.TSocket(THRIFT_SERVER, THRIFT_SERVER_PORT)
        self.transport = TTransport.TBufferedTransport(socket)
        bprotocol = TBinaryProtocol.TBinaryProtocol(self.transport)

        periph_rpc = importlib.import_module("otn_pmon.thrift_api.periph_rpc")
        self.pltfm_mgr = periph_rpc.Client(bprotocol)

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
