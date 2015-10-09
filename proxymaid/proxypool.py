from Queue import Queue, PriorityQueue
from datetime import datetime
class Proxy(object):
    def __init__(self, ip, port, country = "N/A"):
        self.ip = ip
        self.port = port
        self.country = country

    def set_country(self, country):
        self.country = country

    @staticmethod
    def make_proxy_url(ip, port):
        return "%s:%d" % (ip, port)

    def proxy_url(self):
        return Proxy.make_proxy_url(self.ip, self.port)

class ProxyPool(object):
    class ProxyMeta(object):
        def __init__(self, proxy):
            self.proxy = proxy
            self.last_used_time = None
            # key:netloc, value:latency second
            self.latency = {}
            # master netloc who are using this proxy
            self.master = None

    def __init__(self, settings = None):
        self.proxy_queue_set = [
            Queue(),
            Queue()
        ]
        self.proxy_meta_map = {}
        self.current_queue_index = 0
        self.settings = {
            "interval_second": 30,
            "max_latency": 5
        }
        if settings:
            self.settings.update(settings)

    def backup_queue_index(self):
        return self.current_queue_index == 0 and 1 or 0

    def count(self):
        return len(self.proxy_meta_map)

    def proxy_in_queue_count(self):
        return self.proxy_queue_set[0].qsize() + self.proxy_queue_set[1].qsize()

    def get_proxy_from_queue(self):
        if self.proxy_queue_set[self.current_queue_index].empty():
            if self.proxy_queue_set[self.backup_queue_index()].empty():
                return None
            else:
                self.current_queue_index = self.backup_queue_index()
        proxy_url = self.proxy_queue_set[self.current_queue_index].get_nowait()
        if proxy_url in self.proxy_meta_map:
            self.proxy_queue_set[self.backup_queue_index()].put_nowait(proxy_url)
        return proxy_url

    def put_proxy_to_queue(self, proxy_url):
        self.proxy_queue_set[self.backup_queue_index()].put_nowait(proxy_url)

    def add_proxy(self, proxy):
        if proxy.proxy_url() not in self.proxy_meta_map:
            self.proxy_meta_map[proxy.proxy_url()] = ProxyPool.ProxyMeta(proxy)
            self.proxy_queue_set[self.backup_queue_index()].put_nowait(proxy.proxy_url())

    def del_proxy(self, proxy_url):
        if proxy_url in self.proxy_meta_map:
            del self.proxy_meta_map[proxy_url]

    def has_proxy(self, proxy_url):
        return proxy_url in self.proxy_meta_map

    def req_proxy(self, url):
        from urlparse import urlparse
        netloc = urlparse(url).netloc
        t = None
        busy_queue = PriorityQueue()
        lazy_queue = PriorityQueue()
        index = 0
        now = datetime.utcnow()
        while index < self.proxy_in_queue_count():
            index += 1
            proxy_url = self.get_proxy_from_queue()
            if not proxy_url:
                break
            if proxy_url in self.proxy_meta_map:
                proxy_meta = self.proxy_meta_map[proxy_url]
                if proxy_meta.last_used_time and (now - proxy_meta.last_used_time).total_seconds() < self.settings["interval_second"]:
                    busy_queue.put_nowait((proxy_meta.last_used_time, proxy_url))
                    continue
                if netloc in proxy_meta.latency and proxy_meta.latency[netloc] > self.settings["max_latency"]:
                    lazy_queue.put_nowait((proxy_meta.latency[netloc], proxy_url))
                    continue
                proxy_meta.last_used_time = now
                proxy_meta.master = netloc
                return proxy_meta.proxy
        #while not busy_queue.empty():
        #    _, proxy_url  = busy_queue.get_nowait()
        #    if proxy_url in self.proxy_meta_map:
        #        proxy_meta = self.proxy_meta_map[proxy_url]
        #        proxy_meta.last_used_time = now
        #        proxy_meta.master = netloc
        #        return proxy_meta.proxy
        while not lazy_queue.empty():
            _, proxy_url = lazy_queue.get_nowait()
            if proxy_url in self.proxy_meta_map:
                proxy_meta = self.proxy_meta_map[proxy_url]
                proxy_meta.last_used_time = now
                proxy_meta.master = netloc
                return proxy_meta.proxy
        return None

    def free_proxy(self, proxy_url, latency = float("inf")):
        if isinstance(proxy_url, Proxy):
            proxy_url = proxy_url.proxy_url()
        if proxy_url in self.proxy_meta_map:
            proxy_meta = self.proxy_meta_map[proxy_url]
            if proxy_meta.master:
                proxy_meta.latency[proxy_meta.master] = latency
            proxy_meta.master = None