import os
DBPATH = os.path.abspath(os.path.dirname(__file__) + '/../data/db/proxy.db')
DBNAME = "sqlite:///" + DBPATH