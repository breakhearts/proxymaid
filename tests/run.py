import pytest
import sys
import os
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), ".."))
from proxymaid import settings
import os
settings.DBPATH = os.path.join(os.path.dirname(settings.DBPATH), "test_proxy.db")
settings.DBNAME = "sqlite:///" + settings.DBPATH

if __name__ == '__main__':
    pytest.main()