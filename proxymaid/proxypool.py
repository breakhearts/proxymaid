from Queue import Queue
from datetime import datetime
class Proxy(object):
    def __init__(self, ip, port, country = "N/A"):
        self.ip = ip
        self.port = port
        self.country = country

    def set_country(self, country):
        self.country = country

    @staticmethod
    def make_proxy_id(ip, port):
        return "%s:%d" % (ip, port)

    def proxy_id(self):
        return Proxy.make_proxy_id(self.ip, self.port)

class ProxyPool(object):
    class ProxyMeta(object):
        def __init__(self, proxy, settings = None):
            self.proxy = proxy
            self.last_used_time = None
            # key:netloc, value:latency second
            self.latency = {}
            # master netloc who are using this proxy
            self.master = None
            self.setting = {
                "interval_second": 30,
                "max_latency": 10
            }
            if settings:
                self.settings.update(settings)

    def __init__(self):
        self.proxy_queue_set = [
            Queue(),
            Queue()
        ]
        self.proxy_meta_map = {}
        self.current_queue_index = 0

    def backup_queue_index(self):
        return self.current_queue_index == 0 and 1 or 0

    def get_proxy_from_queue(self):
        if self.proxy_queue_set[self.current_queue_index].empty():
            if self.proxy_queue_set[self.backup_queue_index()].empty():
                return None
            else:
                self.current_queue_index = self.backup_queue_index()
        proxy_id = self.proxy_queue_set[self.current_queue_index].get_nowait()
        if proxy_id in self.proxy_meta_map:
            self.proxy_queue_set[self.backup_queue_index()].put_nowait(proxy_id)
        return proxy_id

    def put_proxy_to_queue(self, proxy_id):
        self.proxy_queue_set[self.backup_queue_index()].put_nowait(proxy_id)

    def add_proxy(self, proxy):
        self.proxy_meta_map[proxy.proxy_id()] = ProxyPool.ProxyMeta(proxy)
        self.proxy_queue_set[self.backup_queue_index()].put_nowait(proxy.proxy_id())

    def del_proxy(self, proxy_id):
        del self.proxy_meta_map[proxy_id]

    def req_proxy(self, url):
        from urlparse import urlparse
        netloc = urlparse(url).netloc
        t = None
        while True:
            proxy_id = self.get_proxy_from_queue()
            if t == proxy_id:
                return None
            t = t and t or proxy_id
            if not proxy_id:
                return None
            if proxy_id in self.proxy_meta_map:
                proxy_meta = self.proxy_meta_map[proxy_id]
                now = datetime.utcnow()
                if (now - proxy_meta.last_used_time).total_seconds() < self.settings["interval_second"]:
                    continue
                if netloc in proxy_meta.latency and proxy_meta.latency[netloc] > self.settings["max_latency"]:
                    continue
                proxy_meta.last_used_time = now
                proxy_meta.master = proxy_id
                return proxy_meta.proxy
        return None

    def free_proxy(self, proxy_id, latency = float("inf")):
        if proxy_id in self.proxy_meta_map:
            proxy_meta = self.proxy_meta_map[proxy_id]
            proxy_meta.latency[proxy_meta.master] = latency
            proxy_meta.master = None