from proxy import ProxyPool, Proxy
from common.logger import Logger
import settings

logger = Logger(settings.LOG_ROOT, "proxy_pool_service")
thrift_logger = Logger(settings.LOG_ROOT, "thrift.server.TServer")

class ProxyPoolHandler:
    def __init__(self, proxy_pool):
        self.proxy_pool = proxy_pool

    def spot_proxy(self, ip, port, country):
        p = Proxy(ip=ip, port=port, country=country.decode('utf-8'))
        if self.proxy_pool.has_proxy(p.proxy_url()):
            logger.debug_class_fun(ProxyPoolHandler.__name__, "proxy exists, proxy_url = %s", p.proxy_url())
        else:
            logger.debug_class_fun(ProxyPoolHandler.__name__,"new proxy, proxy_url = %s", p.proxy_url())
            self.proxy_pool.add_proxy(p)

    def has_proxy(self, proxy_url):
        return self.proxy_pool.has_proxy(proxy_url)

    def req_proxy(self, url):
        p = self.proxy_pool.req_proxy(url)
        if p:
            logger.debug_class_fun(ProxyPoolHandler.__name__, "req proxy ok, proxy_url = %s", p.proxy_url())
        else:
            logger.debug_class_fun(ProxyPoolHandler.__name__, "req proxy failed")
        if p :
            return p.proxy_url()
        else:
            return ""

    def free_proxy(self, proxy_url, latency):
        logger.debug_class_fun(ProxyPoolHandler.__name__, "free proxy, proxy_url = %s, latency = %02f", proxy_url, latency)
        return self.proxy_pool.free_proxy(proxy_url, latency)

def start_proxy_pool_service(**kwargs):
    proxy_pool = ProxyPool(kwargs)
    import rpc.ProxyPool
    from thrift.transport import TSocket, TTransport
    from thrift.server import TServer
    from thrift.protocol import TBinaryProtocol
    handler = ProxyPoolHandler(proxy_pool)
    processor = rpc.ProxyPool.Processor(handler)
    transport = TSocket.TServerSocket(port=settings.PROXY_POOL_LISTEN_PORT)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()
    server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
    logger.debug_fun("start proxy pool service ok")
    server.serve()