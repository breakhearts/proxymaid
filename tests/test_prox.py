from proxymaid.proxy import Proxy, ProxyPool, ProxyModel, dbhelper

class TestPorxyModel:
    def test_op(self):
        dbhelper.create_tables()
        p = ProxyModel(ip="127.0.0.1", port=88888)
        try:
            p.insert()
        except:
            pass
        t = ProxyModel.load_all()
        p = t[-1]
        proxy_count = len(t)
        assert p.ip == "127.0.0.1" and p.port == 88888
        p = ProxyModel.load("127.0.0.1", 88888)
        assert p.ip == "127.0.0.1" and p.port == 88888
        p.port = 99999
        p.update()
        p = ProxyModel.load_all()[-1]
        assert p.ip == "127.0.0.1" and p.port == 99999
        p.delete()
        assert proxy_count - 1 == len(ProxyModel.load_all())

class TestProxyPool:

    def test_add_del(self):
        proxypool = ProxyPool()
        p1 = Proxy(ip="127.0.0.1", port=80)
        p2 = Proxy(ip="127.0.0.1", port=8080)
        p3 = Proxy(ip="127.0.0.2", port=8080)
        proxypool.add_proxy(p1)
        proxypool.add_proxy(p1)
        proxypool.add_proxy(p2)
        proxypool.add_proxy(p3)
        assert proxypool.count() == 3
        assert proxypool.has_proxy(p1.proxy_url())
        proxypool.del_proxy(p1.proxy_url())
        assert proxypool.count() == 2
        proxypool.del_proxy(p2.proxy_url())
        proxypool.del_proxy(p3.proxy_url())
        assert proxypool.count() == 0
        proxypool.del_proxy(p1.proxy_url())

    def test_req_free(self):
        proxypool = ProxyPool({"interval_second":0.3, "max_latency":1})
        assert proxypool.settings["max_latency"] == 1
        assert proxypool.settings["interval_second"] == 0.3
        p1 = Proxy(ip="127.0.0.1", port=80)
        p2 = Proxy(ip="127.0.0.1", port=8080)
        p3 = Proxy(ip="127.0.0.2", port=80)
        p4 = Proxy(ip="127.0.0.2", port=8080)
        proxypool.add_proxy(p1)
        proxypool.add_proxy(p2)
        proxypool.add_proxy(p3)
        proxypool.add_proxy(p4)
        rp1 = proxypool.req_proxy("http://pytest.org/latest/unittest.html")
        assert rp1.proxy_url() == p1.proxy_url()
        rp2 = proxypool.req_proxy("http://pytest.org/latest/goodpractises.html")
        assert rp2.proxy_url() == p2.proxy_url()
        rp3 = proxypool.req_proxy("http://www.oschina.net/translate/unit-testing-with-the-python-mock-class")
        assert rp3.proxy_url() == p3.proxy_url()
        rp4 = proxypool.req_proxy("http://my.oschina.net/lionets/blog/269892")
        assert rp4.proxy_url() == p4.proxy_url()
        rp5 = proxypool.req_proxy("http://my.oschina.net/lionets/blog/269892")
        assert not rp5
        proxypool.free_proxy(p1, 1.5)
        rp = proxypool.req_proxy("http://pytest.org/latest/unittest.html")
        assert not rp
        proxypool.free_proxy(p3, 1.3)
        proxypool.free_proxy(p2, 1.3)
        import time
        time.sleep(0.3)
        rp = proxypool.req_proxy("http://pytest.org/latest/unittest.html")
        assert rp.proxy_url() == p3.proxy_url()
        rp = proxypool.req_proxy("http://pytest.org/latest/unittest.html")
        assert rp.proxy_url() == p4.proxy_url()
        rp = proxypool.req_proxy("http://pytest.org/latest/unittest.html")
        assert rp.proxy_url() == p2.proxy_url()
        rp = proxypool.req_proxy("http://pytest.org/latest/unittest.html")
        assert rp.proxy_url() == p1.proxy_url()
        rp = proxypool.req_proxy("http://pytest.org/latest/unittest.html")
        assert not rp