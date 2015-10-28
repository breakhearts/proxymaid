from Queue import Queue, PriorityQueue
from datetime import datetime
from common.model import DBHelper
import settings
from sqlalchemy import Column, String, Integer
from common.utility import wise_mk_dir_for_file
import requests

wise_mk_dir_for_file(settings.DBPATH)
dbhelper = DBHelper(settings.DBNAME)

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

    @staticmethod
    def split_proxy_url(proxy_url):
        return proxy_url.split(":")

    def proxy_url(self):
        return Proxy.make_proxy_url(self.ip, self.port)

class ProxyModel(dbhelper.get_base_class()):
    __tablename__ = "proxy"
    ip = Column(String, primary_key=True)
    port = Column(Integer, primary_key=True)
    country = Column(String)

    @staticmethod
    def load(ip, port):
        session = dbhelper.create_session()
        t = session.query(ProxyModel).filter(ProxyModel.ip).filter(ProxyModel.port).first()
        session.close()
        return t

    @staticmethod
    def load_all():
        session = dbhelper.create_session()
        t = session.query(ProxyModel)
        session.close()
        return [x for x in t]

    def delete(self):
        session = dbhelper.create_session()
        t = session.query(ProxyModel).filter(ProxyModel.ip == self.ip).filter(ProxyModel.port == self.port).first()
        if t:
            session.delete(t)
            session.commit()
        session.close()

    def insert(self):
        dbhelper.insert_one(self)

    def update(self):
        session = dbhelper.create_session()
        t = session.query(ProxyModel).filter(ProxyModel.ip == self.ip).filter(ProxyModel.port == self.port).first()
        for (k, v) in self.__dict__.items():
            if not k.startswith('_'):
                setattr(t, k, v)
        session.commit()
        session.close()

dbhelper.create_tables()

class ProxyPool(object):
    class ProxyMeta(object):
        def __init__(self, proxy):
            self.proxy = proxy
            self.last_used_time = None
            # key:netloc, value:latency second
            self.latency = {}
            # master netloc who are using this proxy
            self.master = None
            self.unavailable_count = 0

    def __init__(self, settings = None):
        self.proxy_queue = []
        self.proxy_queue_cursor = 0
        self.proxy_queue_validator_cursor = 0
        self.proxy_meta_map = {}
        self.current_queue_index = 0
        self.settings = {
            "interval_second": 30,
            "max_latency": 5,
            "max_unavailable_count": 3
        }
        # avoid delay variation, when proxy check failed, only at least one proxy available in the same round, let
        # proxy.unavailable_count plus one
        import sys
        self.last_available_distance = sys.maxint
        if settings:
            self.settings.update(settings)

    def load(self):
        for pm in ProxyModel.load_all():
            p = Proxy(ip=pm.ip, port=pm.port, country=pm.country)
            self.add_proxy(p)

    def backup_queue_index(self):
        return self.current_queue_index == 0 and 1 or 0

    def count(self):
        return len(self.proxy_meta_map)

    def proxy_in_queue_count(self):
        return len(self.proxy_queue)

    def get_proxy_from_queue(self):
        while True:
            if len(self.proxy_queue) == 0:
                return None
            proxy_url = self.proxy_queue[self.proxy_queue_cursor]
            if proxy_url in self.proxy_meta_map:
                self.proxy_queue_cursor = (self.proxy_queue_cursor + 1) % len(self.proxy_queue)
                return proxy_url
            else:
                del self.proxy_queue[self.proxy_queue]


    def __add_proxy(self, proxy):
        if proxy.proxy_url() not in self.proxy_meta_map:
            self.proxy_meta_map[proxy.proxy_url()] = ProxyPool.ProxyMeta(proxy)
            self.proxy_queue.append(proxy.proxy_url())

    def add_proxy(self, proxy):
        self.__add_proxy(proxy)
        pm = ProxyModel(ip=proxy.ip, port=proxy.port, country=proxy.country)
        pm.insert()

    def __del_proxy(self, proxy_url):
        if proxy_url in self.proxy_meta_map:
            del self.proxy_meta_map[proxy_url]

    def del_proxy(self, proxy_url):
        self.__del_proxy(proxy_url)
        ip, port = Proxy.split_proxy_url(proxy_url)
        p = ProxyModel(ip=ip, port=port)
        p.delete()

    def has_proxy(self, proxy_url):
        return proxy_url in self.proxy_meta_map

    def req_proxy(self, url):
        from urlparse import urlparse
        netloc = urlparse(url).netloc
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

    def update_proxy_status(self, proxy_url, available):
        if proxy_url not in self.proxy_meta_map:
            return
        p = self.proxy_meta_map[proxy_url]
        if available:
            p.unavailable_count = 0
            self.last_available_distance = 0
        else:
            self.last_available_distance += 1
            if self.last_available_distance < max(self.count(), self.settings["max_unavailable_count"]):
                p.unavailable_count += 1
            if p.unavailable_count >= self.settings["max_unavailable_count"]:
                self.del_proxy(proxy_url)

    def req_proxy_for_validator(self):
        if self.proxy_queue_validator_cursor >= len(self.proxy_queue):
            self.proxy_queue_validator_cursor = 0
        p = self.proxy_queue[self.proxy_queue_validator_cursor]
        self.proxy_queue_validator_cursor = (self.proxy_queue_validator_cursor + 1) % len(self.proxy_queue)
        return p

def proxy_request(url, proxy_url, user_agent=None, timeout=None):
    proxies = {
        "http": proxy_url
    }
    headers = {}
    if user_agent:
        headers["user-agent"] = user_agent
    if timeout:
        return requests.get(url, proxies=proxies, headers=headers, timeout=timeout)
    else:
        return requests.get(url, proxies=proxies, headers=headers)