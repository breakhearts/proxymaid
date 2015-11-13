from multiprocessing import Process

import pytest

from proxymaid.proxypoolservice import run_proxy_pool_service
from proxymaid.proxymaid_rpc.proxypoolclient import ProxyPoolClient


@pytest.fixture(scope="function")
def setup(request):
    from proxymaid.proxy import dbhelper
    dbhelper.drop_tables()
    dbhelper.create_tables()
    p = Process(target=run_proxy_pool_service)
    p.daemon = True
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
    p = client.req_proxy('http://www.baidu.com')
    assert p == ""
    client.free_proxy("127.0.0.1:8080", 0.1)
    p = client.req_proxy_for_validate()
    assert p == "127.0.0.1:8080"
    client.close()
