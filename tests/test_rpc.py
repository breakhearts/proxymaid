from multiprocessing import Process
from proxymaid.proxypoolservice import start_proxy_pool_service
from proxymaid.proxypoolclient import ProxyPoolClient
import pytest

@pytest.fixture(scope="function")
def setup(request):
    from proxymaid.proxy import dbhelper
    dbhelper.drop_tables()
    dbhelper.create_tables()
    p = Process(target=start_proxy_pool_service)
    p.start()
    def fin():
        dbhelper.drop_tables()
    request.addfinalizer(fin)
    return p

def test_client(setup):
    client = ProxyPoolClient()
    client.open()
    client.spot_proxy('127.0.0.1', 8080, 'China')
    p = client.req_proxy('http://www.baidu.com')
    assert p == "127.0.0.1:8080"
    client.close()