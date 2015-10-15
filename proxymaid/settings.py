import os
ROOT = os.path.abspath(os.path.dirname(__file__))

DBPATH = ROOT + '/../data/db/proxy.db'
DBNAME = "sqlite:///" + DBPATH

LOG_ROOT = ROOT + "/logs"
PROXY_POOL_SERVER_HOST = "localhost"
PROXY_POOL_LISTEN_PORT = 9000
