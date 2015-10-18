from common import utility
import requests
from common.logger import Logger
from proxypoolclient import ProxyPoolClient
from thrift import Thrift
import settings
from proxy import proxy_request
import socket
from proxy import Proxy

logger = Logger(settings.LOG_ROOT, "proxy_spider")

def validate_proxy(proxy_url):
    for v_url in settings.PROXY_VALIDATION_URLS:
        try:
            r = proxy_request(v_url, proxy_url, utility.random_ua(),
                              timeout = settings.VALIDATION_TIMEOUT)
        except requests.exceptions.ConnectionError:
            continue
        except requests.exceptions.Timeout:
            continue
        except socket.timeout:
            continue
        except:
            continue
        if r.status_code != 200:
            continue
        else:
            return True, r.elapsed.total_seconds()
    return False, 0

def spider_page(page_url, parse):
    headers = {'user-agent': utility.random_ua()}
    try:
        r = requests.get(page_url, headers=headers, timeout = 30)
    except:
        logger.traceback()
        return
    if r.status_code != 200:
        logger.error("get list page failed, url = %s, status_code = %d", page_url, r.status_code)
        return
    client = ProxyPoolClient()
    try:
        client.open()
        logger.debug_fun("connect ok")
    except Thrift.TException:
        logger.traceback()
        logger.debug_fun("connect failed, quit")
        return
    logger.debug_fun("get list page ok, url = %s", page_url)
    candidate_proxies = parse(r.content)
    for ip, port in candidate_proxies:
        logger.debug_fun("check proxy, ip = %s, port = %d", ip, port)
        proxy_url = Proxy.make_proxy_url(ip, port)
        ret, resp_second = validate_proxy(proxy_url)
        if not ret or resp_second > settings.PROXY_MAX_DELAY:
            logger.debug_fun("check proxy failed, proxy_url = %s", proxy_url)
            continue
        logger.debug_fun("check proxy ok, proxy_url = %s", proxy_url)
        try:
            proxy_exists = client.has_proxy(proxy_url)
        except:
            logger.traceback()
            logger.debug_fun("check proxy exists failed, proxy_url = %s", proxy_url)
            break
        if proxy_exists:
            logger.debug_fun("proxy exists, proxy_url = %s", proxy_url)
        else:
            try:
                country = utility.get_ip_country(ip)
            except:
                logger.traceback()
                logger.debug_fun("get country failed, proxy_url = %s", proxy_url)
                break
            try:
                client.spot_new_proxy(ip, port, country)
            except:
                logger.traceback()
                logger.debug_fun("spot new proxy failed, ip = %s, port = %d, country = %s", ip, port, country)
                break
            logger.debug_fun("spot new proxy, ip = %s, port = %d, country = %s", ip, port, country)
        break