# -*-coding:utf-8-*-

from lxml import etree
from proxymaid.common.logger import Logger
from proxymaid import settings
from proxymaid.spider import spider_page
from proxymaid.common.server import SimpleServer

logger = Logger(settings.LOG_ROOT, "proxy_spider")

def parse_kuai_page(content):
    proxies = []
    tree = etree.HTML(content)
    for tr in tree.xpath('//div[@id="list"]/table/tbody/tr'):
        url, port, anonymous, protocols, methods, comments, _, _ = tr.xpath("td/text()")
        port = int(port)
        if anonymous.find("匿名".decode('utf-8')) == -1:
            logger.debug_fun("skip non-anonymous proxy, url = %s", url)
        else:
            protocols = [x.strip().lower() for x in protocols.split(',')]
            if "http" not in set(protocols):
                logger.debug_fun("skip proxy not support http, url = %s", url)
                continue
            proxies.append((url, port))
    return proxies

def parse_xicidaili_page(content):
    proxies = []
    tree = etree.HTML(content)
    for tr in tree.xpath('//*[@id="ip_list"]/tr'):
        tds = tr.xpath("td/text()")
        if len(tds) < 6:
            continue
        url = tds[0]
        port = int(tds[1])
        if tds[3].find("高匿".decode('utf-8')) == -1:
            logger.debug_fun("skip non-anonymous proxy, url = %s", url)
            continue
        if tds[4].find("HTTP") == -1:
            logger.debug_fun("skip proxy not support http, url = %s", url)
            continue
        proxies.append((url, port))
    return proxies

def parse_free_proxy_list_page(content):
    proxies = []
    tree = etree.HTML(content)
    for tr in tree.xpath('//*[@class="display fpltable"]/tbody/tr'):
        tds = tr.xpath("td/text()")
        if len(tds) != 8:
            continue
        try:
            url = tds[0]
            port = int(tds[1])
            if tds[4].find("anonymous") == -1 and tds[4].find("elite") == -1:
                logger.debug_fun("skip non-anonymous proxy, url = %s", url)
                continue
            proxies.append((url, port))
        except:
            pass
    return  proxies

def parse_gather_proxy(content):
    proxies = []
    tree = etree.HTML(content)
    for script in tree.xpath('//*[@class="proxy-list"]/descendant::script/text()'):
        try:
            script = script.replace("gp.insertPrx(", "")
            script = script.replace(");", "")
            import json
            t = json.loads(script)
            url = t["PROXY_IP"]
            port = int(t["PROXY_PORT"],16)
            proxies.append((url, port))
        except:
            pass
    return proxies

class ProxySpiderServer(SimpleServer):

    def run(self):
        spider_page("http://www.kuaidaili.com/proxylist/1/", parse_kuai_page)
        spider_page("http://www.xicidaili.com", parse_xicidaili_page)
        spider_page("http://free-proxy-list.net/", parse_free_proxy_list_page)

    def after_run(self):
        import time
        time.sleep(60 * 30)

    def tear_down(self):
        logger.debug_class_fun(ProxySpiderServer.__name__, "gracefully quit")