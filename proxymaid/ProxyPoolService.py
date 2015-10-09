from proxypool import ProxyPool, Proxy

class ProxyPoolHandler:
    def __init__(self, proxy_pool):
        self.proxy_pool = proxy_pool

    def spot_proxy(self, proxy_url, port, country):
        pass

    def req_proxy(self, url):
        return self.proxy_pool.req_proxy(url)

    def free_proxy(self, proxy_url, latency):
        return self.proxy_pool.free_proxy(proxy_url, latency)
