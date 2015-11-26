from proxy import ProxyPool, Proxy
from common.logger import Logger
import settings
from proxyweb import start_proxy_web

logger = Logger(settings.LOG_ROOT, "proxy_pool_service")
thrift_logger = Logger(settings.LOG_ROOT, "thrift.server.TServer")

class ProxyPoolHandler:
    def __init__(self, proxy_pool):
        self.proxy_pool = proxy_pool

    def spot_proxy(self, ip, port, country):
        if country:
            country=country.decode('utf-8')
        p = Proxy(ip=ip, port=port, country=country)
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

    def req_proxy_for_validate(self):
        p = self.proxy_pool.req_proxy_for_validate()
        logger.debug_class_fun(ProxyPoolHandler.__name__, "request ok, proxy_url = %s", p)
        if p:
            return p
        else:
            return ""

    def update_proxy_status(self, proxy_url, available):
        deleted = self.proxy_pool.update_proxy_status(proxy_url, available)
        logger.debug_class_fun(ProxyPoolHandler.__name__, "update ok, available = %s, deleted = %s", available, deleted)

def run_proxy_pool_service(**kwargs):
    proxy_pool = ProxyPool(kwargs)
    proxy_pool.load()
    logger.debug("proxy_pool load ok, count = %d", proxy_pool.count())
    from thrift.transport import TSocket, TTransport
    from thrift.server import TServer
    from thrift.protocol import TBinaryProtocol
    handler = ProxyPoolHandler(proxy_pool)
    import proxymaid_rpc.rpc.ProxyPool
    processor = proxymaid_rpc.rpc.ProxyPool.Processor(handler)
    import proxymaid_rpc.settings
    transport = TSocket.TServerSocket(port=proxymaid_rpc.settings.PROXY_POOL_LISTEN_PORT)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()
    server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
    start_proxy_web(proxy_pool ,9100)
    logger.debug_fun("start proxy pool service ok")
    server.serve()