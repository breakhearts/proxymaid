import os
ROOT = os.path.abspath(os.path.dirname(__file__))

DBPATH = ROOT + '/../data/db/proxy.db'
DBNAME = "sqlite:///" + DBPATH

LOG_ROOT = ROOT + "/../data/logs"

# validator setting
PROXY_VALIDATION_URLS = [
    ("http://www.baidu.com", "hao123.com"),
    ("http://www.google.com", "mail.google.com"),
    ("http://www.bing.com", "go.microsoft.com")
]

VALIDATION_TIMEOUT = 3
VALIDATION_INTERVAL = 30 * 60
PROXY_MAX_DELAY = 5
