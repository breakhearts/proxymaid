import rpc.ProxyPool
from thrift.transport import TSocket, TTransport
from thrift.protocol import TBinaryProtocol
import settings

class ProxyPoolClient(object):
    def __init__(self):
        self.transport = TSocket.TSocket(settings.PROXY_POOL_SERVER_HOST, settings.PROXY_POOL_LISTEN_PORT)
        self.transport = TTransport.TBufferedTransport(self.transport)
        protocol = TBinaryProtocol.TBinaryProtocol(self.transport)
        self.client = rpc.ProxyPool.Client(protocol)

    def open(self):
        self.transport.open()

    def close(self):
        self.transport.close()

    def is_connect(self):
        return self.transport.isOpen()

    def __getattr__(self, item):
        if hasattr(self.client, item):
            return getattr(self.client, item)
        raise AttributeError()